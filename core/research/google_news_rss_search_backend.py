from __future__ import annotations

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

    def search(self, query: str, *, max_results: int) -> list[SearchResult]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if not isinstance(max_results, int) or isinstance(max_results, bool) or max_results <= 0:
            raise ValueError("max_results must be a positive integer")

        params = urlencode({"q": query.strip(), "hl": "en-US", "gl": "US", "ceid": "US:en"})
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
        for source in result.sources[:max_results]:
            # RSS item bodies may contain markup. Keep a conservative plain
            # text snippet and never promote it to evidence or a verified fact.
            snippet = " ".join(str(source.content or "").replace("<", " ").replace(">", " ").split())[:500]
            items.append(
                SearchResult(
                    title=source.title,
                    url=source.locator,
                    snippet=snippet,
                    publisher=source.publisher,
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
        if not items:
            raise RuntimeError("Google News RSS returned no discovery results")
        return items
