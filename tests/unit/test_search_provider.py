from __future__ import annotations

from core.research.acquisition import (
    AcquisitionRequest,
    ResearchAcquisitionEngine,
)
from core.research.search_provider import (
    FunctionSearchBackend,
    SearchProviderConfig,
    SearchResearchProvider,
    SearchResult,
)


def fake_search(
    query: str,
    max_results: int,
):
    assert query == "AI security research"

    results = [
        SearchResult(
            title="AI Security Research",
            url="https://example.com/ai-security",
            snippet="Research about AI security.",
            publisher="Example Research",
        ),
        SearchResult(
            title="AI Security Guide",
            url="https://example.org/security-guide",
            snippet="A guide to AI security.",
            publisher="Example Guide",
        ),
        # Intentional duplicate URL.
        SearchResult(
            title="Duplicate Result",
            url="https://example.com/ai-security",
            snippet="Duplicate result.",
            publisher="Duplicate",
        ),
    ]

    return results[:max_results]


def test_search_result_validation():
    result = SearchResult(
        title="Test",
        url="https://example.com",
        snippet="Test snippet",
    )

    assert result.title == "Test"
    assert result.url == "https://example.com"

    print(
        "[PASS] search result validation"
    )


def test_invalid_search_urls_blocked():
    blocked = False

    try:
        SearchResult(
            title="Invalid",
            url="ftp://example.com",
        )
    except ValueError:
        blocked = True

    assert blocked is True

    print(
        "[PASS] invalid search URL blocked"
    )


def test_backend_adapter():
    backend = FunctionSearchBackend(
        fake_search
    )

    results = backend.search(
        "AI security research",
        max_results=3,
    )

    assert len(results) == 3
    assert isinstance(
        results[0],
        SearchResult,
    )

    print(
        "[PASS] search backend adapter"
    )


def test_provider_identity_and_network_capability():
    backend = FunctionSearchBackend(
        fake_search
    )

    provider = SearchResearchProvider(
        backend
    )

    assert provider.provider_name == "search"
    assert provider.requires_network is True

    print(
        "[PASS] provider identity"
    )

    print(
        "[PASS] provider marked as network-capable"
    )


def test_search_results_normalized_and_deduplicated():
    backend = FunctionSearchBackend(
        fake_search
    )

    provider = SearchResearchProvider(
        backend,
        SearchProviderConfig(
            max_results=10
        ),
    )

    results = provider.search(
        "  AI   security   research  ",
        max_results=10,
    )

    assert len(results) == 2

    assert results[0].rank == 1
    assert results[1].rank == 2

    assert (
        results[0].url
        == "https://example.com/ai-security"
    )

    assert (
        results[1].url
        == "https://example.org/security-guide"
    )

    print(
        "[PASS] query normalization"
    )

    print(
        "[PASS] duplicate search results removed"
    )

    print(
        "[PASS] search ranking normalized"
    )


def test_acquisition_result():
    backend = FunctionSearchBackend(
        fake_search
    )

    provider = SearchResearchProvider(
        backend
    )

    request = AcquisitionRequest(
        query="AI security research",
        source_type="web",
        max_sources=2,
    )

    result = provider.acquire(
        request
    )

    assert result.completed is True
    assert result.status == "completed"

    assert len(result.sources) == 2

    first = result.sources[0]

    assert first.source_type == "web"

    assert (
        first.locator
        == "https://example.com/ai-security"
    )

    assert (
        first.content
        == "Research about AI security."
    )

    assert (
        first.metadata["provider"]
        == "search"
    )

    assert (
        first.metadata["discovery_only"]
        is True
    )

    assert (
        first.metadata[
            "content_is_search_snippet"
        ]
        is True
    )

    assert (
        first.metadata["search_rank"]
        == 1
    )

    print(
        "[PASS] acquisition result created"
    )

    print(
        "[PASS] search source metadata preserved"
    )

    print(
        "[PASS] search snippets marked discovery-only"
    )


def test_provider_registration():
    engine = ResearchAcquisitionEngine()

    backend = FunctionSearchBackend(
        fake_search
    )

    provider = SearchResearchProvider(
        backend
    )

    engine.register_provider(
        provider
    )

    assert (
        "search"
        in engine.providers()
    )

    assert (
        engine.provider_requires_network(
            "search"
        )
        is True
    )

    print(
        "[PASS] search provider registered"
    )

    print(
        "[PASS] search network capability exposed"
    )



def test_hindi_query_expansion_preserves_original_and_discovers_english_sources():
    seen_queries = []

    def bilingual_search(query: str, max_results: int):
        seen_queries.append((query, max_results))
        if "AI सुरक्षा" in query:
            return [
                SearchResult(
                    title=f"Hindi AI security {i}",
                    url=f"https://example.com/hindi-{i}",
                    snippet="Hindi discovery result",
                    published_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                )
                for i in range(max_results)
            ]
        return [
            SearchResult(
                title=f"Official AI safety report {i}",
                url=f"https://example.org/report-{i}",
                snippet="English primary-source lead",
                published_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            )
            for i in range(max_results)
        ]

    provider = SearchResearchProvider(
        FunctionSearchBackend(bilingual_search),
        SearchProviderConfig(max_results=5),
    )
    results = provider.search("आज AI सुरक्षा में क्या नया है?", max_results=5)

    assert seen_queries[0][0] == "आज AI सुरक्षा में क्या नया है?"
    assert len(seen_queries) == 5
    assert all(call[1] == 1 for call in seen_queries)
    assert seen_queries[1][0] == "latest AI safety security news"
    assert "safety security" in seen_queries[1][0]
    assert [call[0] for call in seen_queries[2:]] == [
        "AI safety latest news",
        "AI security today",
        "artificial intelligence safety security risks",
    ]
    assert len(results) == 2
    assert any("example.com/hindi" in item.url for item in results)
    assert any("example.org/report" in item.url for item in results)
    assert any(item.metadata["discovery_query"] == seen_queries[0][0] for item in results)
    assert any(item.metadata["discovery_query"] == seen_queries[1][0] for item in results)



def test_fallback_backend_used_when_primary_search_is_blocked():
    calls = []

    class BlockingBackend(FunctionSearchBackend):
        def search(self, query: str, *, max_results: int):
            calls.append("primary")
            raise RuntimeError("anti-bot challenge")

    class FallbackBackend(FunctionSearchBackend):
        def search(self, query: str, *, max_results: int):
            calls.append("fallback")
            return [SearchResult(
                title="RSS discovery lead",
                url="https://news.google.com/rss/articles/test",
                snippet="Discovery only",
                published_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                metadata={"discovery_only": True},
            )]

    provider = SearchResearchProvider(
        BlockingBackend(lambda query, limit: []),
        SearchProviderConfig(max_results=5),
        fallback_backend=FallbackBackend(lambda query, limit: []),
    )
    results = provider.search("latest AI safety news", max_results=5)
    assert calls == ["primary", "fallback"]
    assert len(results) == 1
    assert results[0].metadata["discovery_query"] == "latest AI safety news"

def test_english_query_is_not_expanded():
    assert SearchResearchProvider._query_variants("latest AI security news") == [
        "latest AI security news"
    ]

def main():
    print(
        "SAHIBEX SEARCH PROVIDER TEST"
    )

    test_search_result_validation()

    test_invalid_search_urls_blocked()

    test_backend_adapter()

    test_provider_identity_and_network_capability()

    test_search_results_normalized_and_deduplicated()

    test_acquisition_result()

    test_provider_registration()

    test_hindi_query_expansion_preserves_original_and_discovers_english_sources()

    test_english_query_is_not_expanded()

    test_fallback_backend_used_when_primary_search_is_blocked()

    print(
        "SAHIBEX SEARCH PROVIDER TEST: PASS"
    )


if __name__ == "__main__":
    main()


def test_time_sensitive_search_discards_undated_or_old_primary_results_and_uses_recent_fallback():
    from datetime import datetime, timezone
    from core.research.search_provider import SearchResult, SearchProviderConfig

    old = SearchResult(title="Old AI safety story", url="https://old.example/story", published_at="2026-08-01T00:00:00Z")
    recent = SearchResult(title="Recent AI safety story", url="https://recent.example/story", published_at=datetime.now(timezone.utc).isoformat())
    primary = FunctionSearchBackend(lambda query, limit: [old])
    fallback = FunctionSearchBackend(lambda query, limit: [recent])
    provider = SearchResearchProvider(primary, SearchProviderConfig(max_results=5), fallback_backend=fallback)
    results = provider.search("latest AI safety news", max_results=5)
    assert [item.url for item in results] == ["https://recent.example/story"]


def test_time_sensitive_search_does_not_promote_undated_result():
    from core.research.search_provider import SearchResult, SearchProviderConfig

    backend = FunctionSearchBackend(lambda query, limit: [SearchResult(title="Undated AI safety story", url="https://unknown.example/story")])
    provider = SearchResearchProvider(backend, SearchProviderConfig(max_results=5))
    assert provider.search("latest AI safety news", max_results=5) == []



def test_fallback_failure_for_one_query_variant_does_not_abort_later_variants():
    from datetime import datetime, timezone
    from core.research.search_provider import SearchProviderBackend, SearchResult, SearchProviderConfig

    class AlwaysFail(SearchProviderBackend):
        backend_name = "always_fail"

        def search(self, query, *, max_results):
            raise RuntimeError("primary provider blocked")

    class VariantFallback(SearchProviderBackend):
        backend_name = "variant_fallback"

        def search(self, query, *, max_results):
            if "सुरक्षा" in query:
                raise RuntimeError("temporary feed failure for Hindi variant")
            return [SearchResult(
                title="Recent AI safety incident report",
                url="https://www.google.com/ai-safety-report",
                snippet="Recent report about AI safety risks",
                published_at=datetime.now(timezone.utc).isoformat(),
            )]

    provider = SearchResearchProvider(
        AlwaysFail(),
        SearchProviderConfig(max_results=5),
        fallback_backend=VariantFallback(),
    )
    results = provider.search("आज AI सुरक्षा में क्या नया है?", max_results=5)
    assert len(results) == 1
    assert results[0].url == "https://www.google.com/ai-safety-report"
