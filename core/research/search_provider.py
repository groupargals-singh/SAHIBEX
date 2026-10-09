from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional
from urllib.parse import urlparse

from core.research.acquisition import (
    AcquisitionRequest,
    AcquisitionResult,
    AcquiredSource,
    ResearchAcquisitionProvider,
)


@dataclass(frozen=True)
class SearchResult:
    """
    One search-engine result.

    This is metadata/snippet information only.
    It is NOT treated as verified document content.
    """

    title: str
    url: str
    snippet: str = ""
    publisher: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[str] = None
    rank: int = 0
    metadata: dict | None = None

    def __post_init__(self):
        if not isinstance(self.title, str):
            raise TypeError("title must be a string")

        if not self.title.strip():
            raise ValueError("title cannot be empty")

        if not isinstance(self.url, str):
            raise TypeError("url must be a string")

        if not self.url.strip():
            raise ValueError("url cannot be empty")

        parsed = urlparse(self.url)

        if parsed.scheme not in {"http", "https"}:
            raise ValueError(
                "search result URL must use http or https"
            )

        if not parsed.hostname:
            raise ValueError(
                "search result URL must contain a hostname"
            )

        if not isinstance(self.snippet, str):
            raise TypeError("snippet must be a string")

        if self.rank < 0:
            raise ValueError("rank cannot be negative")

        if self.metadata is not None and not isinstance(
            self.metadata,
            dict,
        ):
            raise TypeError("metadata must be a dictionary")


@dataclass(frozen=True)
class SearchProviderConfig:
    max_results: int = 10
    user_agent: str = "SAHIBEX-Research-Search/0.1"

    def __post_init__(self):
        if self.max_results <= 0:
            raise ValueError(
                "max_results must be greater than zero"
            )

        if not self.user_agent.strip():
            raise ValueError(
                "user_agent cannot be empty"
            )


class SearchProviderBackend:
    """
    Backend interface for an actual search service.

    The SearchProvider itself does not depend on a specific
    search engine.

    A backend may later represent:
        - search API
        - self-hosted search
        - commercial search provider
        - metasearch service
        - future SAHIBEX search system
    """

    backend_name = "base_search"

    def search(
        self,
        query: str,
        *,
        max_results: int,
    ) -> list[SearchResult]:
        raise NotImplementedError


class UnavailableSearchBackend(SearchProviderBackend):
    """Explicit fail-closed backend used when no search credential is configured."""

    backend_name = "unconfigured_search"

    def search(
        self,
        query: str,
        *,
        max_results: int,
    ) -> list[SearchResult]:
        raise RuntimeError(
            "No live search provider is configured. "
            "Configure an approved search provider before network research."
        )


class FunctionSearchBackend(SearchProviderBackend):
    """
    Adapter around a normal Python function.

    Useful for:
        - unit tests
        - local search engines
        - API adapters
        - future provider integrations
    """

    backend_name = "function_search"

    def __init__(
        self,
        search_function: Callable[
            [str, int],
            list[SearchResult],
        ],
    ):
        if not callable(search_function):
            raise TypeError(
                "search_function must be callable"
            )

        self.search_function = search_function

    def search(
        self,
        query: str,
        *,
        max_results: int,
    ) -> list[SearchResult]:
        results = self.search_function(
            query,
            max_results,
        )

        if not isinstance(results, list):
            raise TypeError(
                "search backend must return a list"
            )

        for result in results:
            if not isinstance(
                result,
                SearchResult,
            ):
                raise TypeError(
                    "search backend returned an invalid result"
                )

        return results


class SearchResearchProvider(
    ResearchAcquisitionProvider
):
    """
    Search-result acquisition provider.

    IMPORTANT:

    Search results are discovery metadata.
    They are NOT automatically treated as verified facts.

    Full source content should later be acquired through
    DirectWebResearchProvider or another document provider.
    """

    provider_name = "search"
    requires_network = True

    def __init__(
        self,
        backend: SearchProviderBackend,
        config: SearchProviderConfig | None = None,
        fallback_backend: SearchProviderBackend | None = None,
    ):
        if not isinstance(
            backend,
            SearchProviderBackend,
        ):
            raise TypeError(
                "backend must be SearchProviderBackend"
            )

        self.backend = backend
        if fallback_backend is not None and not isinstance(
            fallback_backend, SearchProviderBackend
        ):
            raise TypeError("fallback_backend must be SearchProviderBackend or None")
        self.fallback_backend = fallback_backend

        self.config = (
            config
            if config is not None
            else SearchProviderConfig()
        )

    @staticmethod
    def _normalize_query(query: str) -> str:
        if not isinstance(query, str):
            raise TypeError(
                "search query must be a string"
            )

        normalized = " ".join(
            query.strip().split()
        )

        if not normalized:
            raise ValueError(
                "search query cannot be empty"
            )

        return normalized

    @staticmethod
    def _query_variants(query: str) -> list[str]:
        """Return the original query plus a conservative Hindi keyword expansion.

        This is retrieval assistance, not translation of the user's intent.
        The original query is always searched first and remains unchanged.
        Only known topical phrases are expanded; unknown Hindi text is retained.
        """
        variants = [query]
        if not any("\u0900" <= char <= "\u097f" for char in query):
            return variants

        expanded = query
        replacements = (
            ("क्या नया है", "latest news updates"),
            ("क्या नई जानकारी है", "latest information updates"),
            ("आधिकारिक", "official"),
            ("विश्वसनीय", "reliable trusted"),
            ("रिपोर्ट", "report"),
            ("शोध", "research study"),
            ("सुरक्षा", "safety security"),
            ("खतरा", "risk threat"),
            ("खतरे", "risks threats"),
            ("कृत्रिम बुद्धिमत्ता", "artificial intelligence AI"),
            ("राजधानी", "capital"),
            ("इतिहास", "history"),
            ("भारत", "India"),
            ("आज", "latest current"),
            ("अभी", "latest current"),
            ("क्या", ""),
            ("है", ""),
            ("हैं", ""),
            ("में", ""),
            ("के बारे में", "about"),
        )
        for source, target in replacements:
            expanded = expanded.replace(source, target)
        expanded = " ".join(expanded.split()).strip(" ?।॥,;:")
        if expanded and expanded.casefold() != query.casefold():
            variants.append(expanded)
        return variants

    @staticmethod
    def _stable_source_id(url: str) -> str:
        """
        Create a deterministic source identity from the URL.

        Python's built-in hash() is intentionally randomized
        between interpreter processes, so it must not be used
        for persistent research identity.

        SHA-256 provides deterministic identity across runs.
        """

        if not isinstance(url, str):
            raise TypeError(
                "url must be a string"
            )

        normalized_url = url.strip()

        if not normalized_url:
            raise ValueError(
                "url cannot be empty"
            )

        url_hash = hashlib.sha256(
            normalized_url.encode("utf-8")
        ).hexdigest()

        return f"search_{url_hash}"

    def search(
        self,
        query: str,
        *,
        max_results: int | None = None,
    ) -> list[SearchResult]:
        query = self._normalize_query(query)

        limit = (
            self.config.max_results
            if max_results is None
            else max_results
        )

        if limit <= 0:
            raise ValueError(
                "max_results must be greater than zero"
            )

        limit = min(
            limit,
            self.config.max_results,
        )

        # Preserve the original query, then add a limited keyword expansion
        # for recognized Hindi topical terms so English-language primary
        # sources are not missed. Each variant is discovery-only.
        discovered: list[tuple[SearchResult, str]] = []
        variants = self._query_variants(query)
        # Reserve result capacity for each query variant. Otherwise a full
        # Hindi-result batch can crowd out all English-language primary-source
        # leads before cross-query deduplication.
        per_variant_limit = max(1, limit // len(variants))
        for variant in variants:
            try:
                batch = self.backend.search(
                    variant, max_results=per_variant_limit
                )
            except Exception:
                # Optional fallback is another discovery provider, not a way
                # to bypass a challenge. It runs only after the primary backend
                # fails and still returns unverified source leads.
                if self.fallback_backend is not None:
                    batch = self.fallback_backend.search(
                        variant, max_results=per_variant_limit
                    )
                elif variant == query:
                    raise
                else:
                    continue
            if not batch and self.fallback_backend is not None:
                batch = self.fallback_backend.search(
                    variant, max_results=per_variant_limit
                )
            discovered.extend((item, variant) for item in batch[:limit])

        # Normalize ranking and deduplicate across all query variants.
        normalized_results = []
        seen_urls = set()

        for result, discovery_query in discovered:
            normalized_url = result.url.strip()

            if normalized_url in seen_urls:
                continue

            seen_urls.add(normalized_url)
            metadata = dict(result.metadata or {})
            metadata.setdefault("discovery_query", discovery_query)

            normalized_results.append(
                SearchResult(
                    title=result.title.strip(),
                    url=normalized_url,
                    snippet=result.snippet.strip(),
                    publisher=result.publisher,
                    author=result.author,
                    published_at=result.published_at,
                    rank=len(normalized_results) + 1,
                    metadata=metadata,
                )
            )
            if len(normalized_results) >= limit:
                break

        return normalized_results

    def acquire(
        self,
        request: AcquisitionRequest,
    ) -> AcquisitionResult:
        if not isinstance(
            request,
            AcquisitionRequest,
        ):
            raise TypeError(
                "request must be an AcquisitionRequest"
            )

        query = self._normalize_query(
            request.query
        )

        max_results = min(
            request.max_sources,
            self.config.max_results,
        )

        results = self.search(
            query,
            max_results=max_results,
        )

        acquired_at = datetime.now(
            timezone.utc
        ).isoformat()

        sources = []

        for result in results:
            source_metadata = dict(
                result.metadata or {}
            )

            source_metadata.update(
                {
                    "provider": self.provider_name,
                    "backend": self.backend.backend_name,
                    "search_query": query,
                    "search_rank": result.rank,
                    "acquired_at": acquired_at,
                    "discovery_only": True,
                    "content_is_search_snippet": True,
                    "reliability": 0.5,
                }
            )

            source_id = self._stable_source_id(
                result.url
            )

            sources.append(
                AcquiredSource(
                    source_id=source_id,
                    title=result.title,
                    source_type="web",
                    locator=result.url,
                    publisher=result.publisher,
                    author=result.author,
                    published_at=result.published_at,
                    content=result.snippet,
                    metadata=source_metadata,
                )
            )

        completed = True

        if not sources:
            status = "no_results"
        else:
            status = "completed"

        return AcquisitionResult(
            query=query,
            sources=sources,
            completed=completed,
            status=status,
            metadata={
                "provider": self.provider_name,
                "backend": self.backend.backend_name,
                "result_count": len(sources),
            },
        )
