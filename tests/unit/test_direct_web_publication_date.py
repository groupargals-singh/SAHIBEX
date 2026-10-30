from datetime import datetime, timedelta, timezone

from core.research.acquisition import AcquisitionRequest
from core.research.web_provider import DirectWebResearchProvider


def test_extracts_article_published_time_from_meta_tag():
    value = DirectWebResearchProvider._extract_published_at(
        '<meta property="article:published_time" content="2026-10-07T22:49:26+05:30" />'
    )
    assert value == datetime(2026, 10, 7, 17, 19, 26, tzinfo=timezone.utc)


def test_extracts_json_ld_date_published():
    value = DirectWebResearchProvider._extract_published_at(
        '<script type="application/ld+json">{"datePublished":"2026-08-19T13:14:57.488Z"}</script>'
    )
    assert value == datetime(2026, 8, 19, 13, 14, 57, 488000, tzinfo=timezone.utc)


def test_does_not_infer_publication_time_when_missing_or_invalid():
    assert DirectWebResearchProvider._extract_published_at('<html><p>Published yesterday</p></html>') is None
    assert DirectWebResearchProvider._extract_published_at(
        '<meta property="article:published_time" content="not-a-date" />'
    ) is None


def test_ignores_naive_timestamps_without_timezone():
    assert DirectWebResearchProvider._extract_published_at(
        '<meta property="article:published_time" content="2026-10-07T22:49:26" />'
    ) is None


def test_does_not_treat_modified_time_as_publication_time():
    assert DirectWebResearchProvider._extract_published_at(
        '<meta property="article:modified_time" content="2026-10-10T10:00:00Z" />'
    ) is None


def test_time_sensitive_acquisition_rejects_stale_or_listing_pages():
    provider = DirectWebResearchProvider()
    fresh_time = datetime.now(timezone.utc) - timedelta(days=1)
    fresh_timestamp = fresh_time.isoformat().replace("+00:00", "Z")
    fresh_body = "Fresh AI safety report content with enough concrete detail to represent a real article rather than a title stub. " * 3
    fresh_html = f'<html><head><meta property="article:published_time" content="{fresh_timestamp}"></head><body><article><p>{fresh_body}</p></article></body></html>'
    stale_html = '<html><head><meta property="article:published_time" content="2026-05-20T10:00:00Z"></head><body><p>Old index content.</p></body></html>'

    def fake_fetch(url):
        body = stale_html if "/section/" in url else fresh_html
        return {
            "url": url,
            "final_url": url,
            "status": 200,
            "content_type": "text/html",
            "content": body,
            "bytes": len(body),
        }

    provider.fetch_url = fake_fetch
    result = provider.acquire(AcquisitionRequest(
        query="latest AI safety news",
        source_type="web",
        max_sources=2,
        metadata={"urls": [
            "https://www.google.com/fresh-article",
            "https://www.google.com/section/ai",
        ]},
    ))
    assert len(result.sources) == 1
    assert result.sources[0].locator.endswith("fresh-article")
    assert result.status == "partial"
    assert any("listing page rejected" in item for item in result.metadata["errors"])


def test_time_sensitive_acquisition_rejects_title_only_or_near_empty_publisher_page():
    provider = DirectWebResearchProvider()
    url = "https://www.example.com/title-only"
    published = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    body = f'<html><head><meta property="article:published_time" content="{published}" /></head><body><article><h1>AI safety report</h1><p>Only a short title stub.</p></article></body></html>'
    provider.fetch_url = lambda requested: {
        "url": requested,
        "final_url": requested,
        "status": 200,
        "content_type": "text/html",
        "content": body,
        "bytes": len(body),
    }
    result = provider.acquire(AcquisitionRequest(
        query="latest AI safety news today",
        source_type="web",
        metadata={"url": url},
    ))
    assert result.sources == []
    assert result.completed is False
    assert any("article body too short" in item for item in result.metadata["errors"])


def test_discovery_timestamp_parser_accepts_rfc2822_rss_date():
    value = DirectWebResearchProvider._parse_discovery_publication_timestamp(
        "Fri, 09 Oct 2026 10:00:00 GMT"
    )
    assert value == datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


def test_time_sensitive_acquisition_accepts_recent_explicit_rss_timestamp_when_publisher_date_is_missing():
    provider = DirectWebResearchProvider()
    url = "https://www.example.com/article"
    recent_timestamp = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    article_text = "Current AI security report content with enough concrete detail to support a real research finding and source verification. " * 3
    body = f"<html><body><article><p>{article_text}</p></article></body></html>"
    provider.fetch_url = lambda requested: {
        "url": requested,
        "final_url": requested,
        "status": 200,
        "content_type": "text/html",
        "content": body,
        "bytes": len(body),
    }
    result = provider.acquire(AcquisitionRequest(
        query="latest AI security news",
        source_type="web",
        metadata={
            "url": url,
            "discovery_metadata_by_url": {
                url: {
                    "published_at": recent_timestamp,
                    "backend": "google_news_rss",
                    "discovery_only": True,
                }
            },
        },
    ))
    assert len(result.sources) == 1
    assert result.sources[0].published_at.isoformat() == recent_timestamp
    assert result.sources[0].metadata["publication_timestamp_source"] == "rss_discovery_metadata"


def test_time_sensitive_acquisition_rejects_stale_discovery_timestamp():
    provider = DirectWebResearchProvider()
    url = "https://www.example.com/article"
    body = "<html><body><article><p>Old AI security report content.</p></article></body></html>"
    provider.fetch_url = lambda requested: {
        "url": requested,
        "final_url": requested,
        "status": 200,
        "content_type": "text/html",
        "content": body,
        "bytes": len(body),
    }
    result = provider.acquire(AcquisitionRequest(
        query="latest AI security news",
        source_type="web",
        metadata={
            "url": url,
            "discovery_metadata_by_url": {
                url: {
                    "published_at": "2026-05-20T10:00:00+00:00",
                    "backend": "google_news_rss",
                    "discovery_only": True,
                }
            },
        },
    ))
    assert result.sources == []
    assert any("publication date is missing or outside" in item for item in result.metadata["errors"])


def test_time_sensitive_acquisition_rejects_missing_publication_date():
    provider = DirectWebResearchProvider()
    body = "<html><body><article><p>Article has no publication date.</p></article></body></html>"
    provider.fetch_url = lambda url: {
        "url": url,
        "final_url": url,
        "status": 200,
        "content_type": "text/html",
        "content": body,
        "bytes": len(body),
    }
    result = provider.acquire(AcquisitionRequest(
        query="latest AI security news",
        source_type="web",
        metadata={"url": "https://www.google.com/article"},
    ))
    assert result.sources == []
    assert result.completed is False
    assert any("publication date is missing" in item for item in result.metadata["errors"])


def test_article_fragment_excludes_page_navigation_and_prefers_article_body():
    raw = '<html><body><nav>Trending unrelated story</nav><article><h1>AI safety report</h1><p>Researchers found a safety issue.</p></article><footer>More stories</footer></body></html>'
    selected, scope = DirectWebResearchProvider._content_fragment(raw)
    visible, _ = DirectWebResearchProvider._visible_text(selected)
    assert scope == "article"
    assert "Researchers found a safety issue" in visible
    assert "Trending unrelated story" not in visible
    assert "More stories" not in visible
