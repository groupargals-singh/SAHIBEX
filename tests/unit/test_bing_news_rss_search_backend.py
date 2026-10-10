from datetime import datetime, timezone
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest

from core.research.bing_news_rss_search_backend import BingNewsRSSSearchBackend


class FakeRSSProvider:
    def __init__(self, sources):
        self.sources = sources
        self.request = None

    def acquire(self, request):
        self.request = request
        return SimpleNamespace(sources=self.sources)


def source(locator, published_at="Fri, 09 Oct 2026 12:00:00 GMT", title="AI safety report - Publisher"):
    return SimpleNamespace(
        locator=locator,
        published_at=published_at,
        title=title,
        publisher="Bing News",
        content="AI safety security report",
    )


def bing_url(target, host="www.bing.com"):
    return f"https://{host}/news/apiclick.aspx?{urlencode({'url': target, 'c': '123'})}"


def test_extracts_and_validates_publisher_url_from_bing_rss():
    target = "https://www.google.com/reports/ai-safety"
    provider = FakeRSSProvider([source(bing_url(target))])
    results = BingNewsRSSSearchBackend(provider=provider).search("AI safety report", max_results=3)
    assert len(results) == 1
    assert results[0].url == target
    assert results[0].metadata["discovery_only"] is True
    assert results[0].metadata["content_is_search_snippet"] is True
    assert provider.request.metadata["url"].startswith("https://www.bing.com/news/search?")


def test_rejects_private_destination_in_bing_rss():
    provider = FakeRSSProvider([source(bing_url("http://127.0.0.1/admin"))])
    with pytest.raises(RuntimeError, match="no safe"):
        BingNewsRSSSearchBackend(provider=provider).search("AI safety report", max_results=3)


def test_rejects_spoofed_bing_redirect_host():
    provider = FakeRSSProvider([source(bing_url("https://publisher.example/story", host="bing.com.attacker.example"))])
    with pytest.raises(RuntimeError, match="no safe"):
        BingNewsRSSSearchBackend(provider=provider).search("AI safety report", max_results=3)


def test_time_sensitive_query_discards_old_and_undated_articles():
    recent = source(bing_url("https://www.google.com/recent"), datetime(2026, 10, 9, tzinfo=timezone.utc).isoformat())
    old = source(bing_url("https://www.google.com/old"), "Tue, 01 Sep 2026 12:00:00 GMT")
    undated = source(bing_url("https://www.google.com/undated"), None)
    provider = FakeRSSProvider([recent, old, undated])
    results = BingNewsRSSSearchBackend(provider=provider).search("आज AI सुरक्षा में क्या नया है?", max_results=5)
    assert [item.url for item in results] == ["https://www.google.com/recent"]


def test_skips_publisher_category_and_listing_pages():
    provider = FakeRSSProvider([
        source(bing_url("https://indianexpress.com/section/technology/artificial-intelligence/")),
        source(bing_url("https://www.google.com/article")),
    ])
    results = BingNewsRSSSearchBackend(provider=provider).search("AI safety report", max_results=3)
    assert [item.url for item in results] == ["https://www.google.com/article"]


def test_general_query_does_not_apply_recency_filter():
    provider = FakeRSSProvider([source(bing_url("https://www.google.com/old"), "Tue, 01 Sep 2026 12:00:00 GMT")])
    results = BingNewsRSSSearchBackend(provider=provider).search("AI safety architecture", max_results=5)
    assert results[0].url == "https://www.google.com/old"
