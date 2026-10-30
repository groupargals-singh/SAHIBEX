from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode

from core.research.acquisition import AcquisitionRequest
from core.research.rss_provider import RSSAtomResearchProvider
from core.research.search_provider import SearchProviderBackend, SearchResult


class GoogleNewsRSSSearchBackend(SearchProviderBackend):
    """Credential-free Google News RSS discovery fallback.

    Results are discovery leads only. Google News wrapper URLs are not treated
    as verified evidence; the research pipeline must fetch/verify publisher
    content or return the links as unverified leads.
    """

    backend_name = "google_news_rss"

    def __init__(self, provider: RSSAtomResearchProvider | None = None) -> None:
        self.provider = provider or RSSAtomResearchProvider()

    @staticmethod
    def _is_relevant_for_query(query: str, title: str, snippet: str) -> bool:
        """Conservative lexical relevance filter for AI safety/security searches."""
        query_text = query.casefold()
        if not any(term in query_text for term in (
            "ai safety", "ai security", "artificial intelligence",
            "सुरक्षा", "कृत्रिम बुद्धिमत्ता",
        )):
            return True

        text = f"{title} {snippet}".casefold()
        ai_terms = (
            " ai ", "artificial intelligence", "llm", "model",
            "openai", "anthropic", "claude", "chatgpt", "ai's", "ai ",
        )
        safety_terms = (
            "safety", "security", "risk", "threat", "attack", "cyber",
            "vulnerab", "misalignment", "alignment", "incident",
            "governance", "control", "alarm", "safe", "secure",
            "सुरक्षा", "खतरा",
        )
        has_ai = any(term.strip() in text for term in ai_terms)
        has_safety = any(term in text for term in safety_terms)
        return has_ai and has_safety

    @staticmethod
    def _published_within_days(value, *, days: int = 7, now: datetime | None = None) -> bool:
        """Return True only for explicitly dated items inside the requested window."""
        if not isinstance(days, int) or isinstance(days, bool) or days <= 0:
            raise ValueError("days must be a positive integer")
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

    def search(self, query: str, *, max_results: int) -> list[SearchResult]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if not isinstance(max_results, int) or isinstance(max_results, bool) or max_results <= 0:
            raise ValueError("max_results must be a positive integer")

        normalized_query = query.strip()
        query_lower = normalized_query.casefold()
        time_sensitive = any(term in query_lower for term in (
            "today", "latest", "current", "recent", "this week", "breaking",
            "आज", "ताज़ा", "ताजा", "नवीनतम", "हालिया", "इस सप्ताह", "अभी",
        ))
        # Recency constraints belong in discovery, not in the verification
        # threshold. Search snippets still remain unverified leads.
        feed_query = normalized_query + (" when:7d" if time_sensitive else "")
        params = urlencode({"q": feed_query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
        feed_url = "https://news.google.com/rss/search?" + params
        result = self.provider.acquire(
            AcquisitionRequest(
                query=query,
                source_type="rss",
                max_sources=max_results,
                metadata={"url": feed_url},
            )
        )
        items: list[SearchResult] = []
        for source in result.sources:
            # RSS item bodies may contain markup. Keep a conservative plain
            # text snippet and never promote it to evidence or a verified fact.
            snippet = " ".join(str(source.content or "").replace("<", " ").replace(">", " ").split())[:500]
            if not self._is_relevant_for_query(query, source.title, snippet):
                continue
            if time_sensitive and not self._published_within_days(source.published_at, days=7):
                continue
            items.append(
                SearchResult(
                    title=source.title,
                    url=source.locator,
                    snippet=snippet,
                    # Google News RSS's publisher field can contain the
                    # search query/feed label, not the actual publisher. The
                    # wrapper URL is discovery-only, so defer identity to the
                    # resolved publisher hostname downstream.
                    publisher=None,
                    published_at=(str(source.published_at) if source.published_at else None),
                    rank=len(items) + 1,
                    metadata={
                        "backend": self.backend_name,
                        "provider": "google_news_rss",
                        "discovery_only": True,
                        "content_is_search_snippet": True,
                        "feed_url": feed_url,
                    },
                )
            )
            if len(items) >= max_results:
                break
        if not items:
            raise RuntimeError(
                "Google News RSS returned no query-relevant discovery results"
            )
        return items
