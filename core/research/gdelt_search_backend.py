from __future__ import annotations

from urllib.parse import urlencode

from core.research.acquisition import AcquisitionRequest
from core.research.rss_provider import RSSAtomResearchProvider
from core.research.search_provider import SearchProviderBackend, SearchResult


class GDELTSearchBackend(SearchProviderBackend):
    """Credential-free GDELT query discovery; results remain unverified leads."""

    backend_name = "gdelt_doc_rss"

    def __init__(self, provider: RSSAtomResearchProvider | None = None) -> None:
        self.provider = provider or RSSAtomResearchProvider()

    def search(self, query: str, *, max_results: int) -> list[SearchResult]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if not isinstance(max_results, int) or isinstance(max_results, bool) or max_results <= 0:
            raise ValueError("max_results must be a positive integer")

        normalized = query.strip()
        params = urlencode({
            "query": normalized,
            "mode": "ArtList",
            "format": "rss",
            "maxrecords": min(max_results * 3, 75),
            "sort": "HybridRel",
        })
        feed_url = "https://api.gdeltproject.org/api/v2/doc/doc?" + params
        acquired = self.provider.acquire(AcquisitionRequest(
            query=normalized,
            source_type="rss",
            max_sources=min(max_results * 3, 75),
            metadata={"url": feed_url},
        ))

        results: list[SearchResult] = []
        seen: set[str] = set()
        for source in acquired.sources:
            url = str(source.locator or "").strip()
            if not url.startswith(("https://", "http://")) or url in seen:
                continue
            seen.add(url)
            snippet = " ".join(str(source.content or "").split())[:500]
            results.append(SearchResult(
                title=source.title,
                url=url,
                snippet=snippet,
                publisher=source.publisher,
                author=source.author if hasattr(source, "author") else None,
                published_at=str(source.published_at) if source.published_at else None,
                rank=len(results) + 1,
                metadata={
                    "backend": self.backend_name,
                    "provider": "gdelt_doc_rss",
                    "discovery_only": True,
                    "content_is_search_snippet": True,
                    "feed_url": feed_url,
                },
            ))
            if len(results) >= max_results:
                break
        if not results:
            raise RuntimeError("GDELT returned no usable query-relevant discovery results")
        return results
