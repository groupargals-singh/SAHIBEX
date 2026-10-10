from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qs, urlencode, urlparse

from core.research.acquisition import AcquisitionRequest
from core.research.rss_provider import RSSAtomResearchProvider
from core.research.search_provider import SearchProviderBackend, SearchResult
from core.research.web_provider import DirectWebResearchProvider


class BingNewsRSSSearchBackend(SearchProviderBackend):
    """Credential-free Bing News RSS discovery with publisher URLs extracted safely.

    Feed items are untrusted discovery leads. Only the explicit URL parameter
    on Bing's known apiclick.aspx redirect endpoint is accepted as the article
    URL. The extracted destination is validated before it leaves this backend;
    publisher text still must be fetched and independently verified downstream.
    """

    backend_name = "bing_news_rss"

    def __init__(self, provider: RSSAtomResearchProvider | None = None) -> None:
        self.provider = provider or RSSAtomResearchProvider()
        self._url_validator = DirectWebResearchProvider()

    @staticmethod
    def _is_time_sensitive(query: str) -> bool:
        text = query.casefold()
        return any(term in text for term in (
            "today", "latest", "current", "recent", "this week", "breaking",
            "आज", "ताज़ा", "ताजा", "नवीनतम", "हालिया", "इस सप्ताह", "अभी", "क्या नया है",
        ))

    @staticmethod
    def _published_within_days(value, *, days: int = 7, now: datetime | None = None) -> bool:
        if isinstance(value, datetime):
            published = value
        elif isinstance(value, str) and value.strip():
            raw = value.strip()
            try:
                normalized = raw[:-1] + "+00:00" if raw.endswith(("Z", "z")) else raw
                published = datetime.fromisoformat(normalized)
            except ValueError:
                try:
                    published = parsedate_to_datetime(raw)
                except (TypeError, ValueError, OverflowError):
                    return False
        else:
            return False
        if published.tzinfo is None or published.utcoffset() is None:
            return False
        reference = now or datetime.now(timezone.utc)
        if reference.tzinfo is None or reference.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        age = reference.astimezone(timezone.utc) - published.astimezone(timezone.utc)
        return timedelta(0) <= age <= timedelta(days=days)

    @staticmethod
    def _is_listing_url(url: str) -> bool:
        path = urlparse(url).path.casefold().rstrip("/")
        segments = path.split("/")
        if any(segment in {"section", "category", "categories", "tag", "topic", "topics"} for segment in segments):
            return True
        # Common publisher index paths that look like articles to search engines.
        if path in {"/technology/artificial-intelligence", "/technology/artificial-intelligence-news", "/artificial-intelligence"}:
            return True
        return False

    def _publisher_url(self, locator: str) -> str:
        parsed = urlparse(locator)
        hostname = (parsed.hostname or "").lower()
        if hostname not in {"bing.com", "www.bing.com"} or not parsed.path.lower().endswith("/apiclick.aspx"):
            raise ValueError("unsupported Bing News redirect URL")
        target = parse_qs(parsed.query, keep_blank_values=False).get("url", [])
        if len(target) != 1:
            raise ValueError("Bing News result must contain exactly one destination URL")
        destination = target[0].strip()
        self._url_validator._validate_url(destination)
        return destination

    def search(self, query: str, *, max_results: int) -> list[SearchResult]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if not isinstance(max_results, int) or isinstance(max_results, bool) or max_results <= 0:
            raise ValueError("max_results must be a positive integer")

        normalized = query.strip()
        # Bing RSS does not reliably support Google's when:7d modifier; recency is enforced against explicit feed timestamps below.
        feed_query = normalized
        feed_url = "https://www.bing.com/news/search?" + urlencode({"q": feed_query, "format": "rss"})
        acquired = self.provider.acquire(AcquisitionRequest(
            query=normalized,
            source_type="rss",
            max_sources=max_results * 3,
            metadata={"url": feed_url},
        ))

        results: list[SearchResult] = []
        seen: set[str] = set()
        time_sensitive = self._is_time_sensitive(normalized)
        for source in acquired.sources:
            try:
                destination = self._publisher_url(source.locator)
            except (ValueError, TypeError):
                continue
            if destination in seen or self._is_listing_url(destination):
                continue
            if time_sensitive and not self._published_within_days(source.published_at):
                continue
            seen.add(destination)
            snippet = " ".join(str(source.content or "").replace("<", " ").replace(">", " ").split())[:500]
            results.append(SearchResult(
                title=source.title,
                url=destination,
                snippet=snippet,
                publisher=source.title.rsplit(" - ", 1)[-1] if " - " in source.title else source.publisher,
                published_at=str(source.published_at) if source.published_at else None,
                rank=len(results) + 1,
                metadata={
                    "backend": self.backend_name,
                    "provider": "bing_news_rss",
                    "discovery_only": True,
                    "content_is_search_snippet": True,
                    "feed_url": feed_url,
                    "publisher_url_extracted_from": "validated_bing_apiclick_url_parameter",
                },
            ))
            if len(results) >= max_results:
                break
        if not results:
            raise RuntimeError("Bing News RSS returned no safe, query-relevant publisher URLs")
        return results
