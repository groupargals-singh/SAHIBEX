from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.acquisition import (
    AcquisitionRequest,
    ResearchAcquisitionEngine,
)
from core.research.acquisition_pipeline import (
    ResearchAcquisitionPipeline,
)
from core.research.search_provider import (
    FunctionSearchBackend,
    SearchResearchProvider,
    SearchResult,
)


class CountingSearchBackend(FunctionSearchBackend):
    """
    Deterministic search backend for integration testing.

    No real internet access is performed.
    """

    backend_name = "counting_test_search"

    def __init__(self):
        self.calls = []

        super().__init__(
            self._search
        )

    def _search(
        self,
        query: str,
        max_results: int,
    ):
        self.calls.append(
            {
                "query": query,
                "max_results": max_results,
            }
        )

        results = [
            SearchResult(
                title="SAHIBEX Search Integration",
                url="https://example.com/sahibex-search",
                snippet=(
                    "This is a deterministic search result "
                    "used by the SAHIBEX integration test."
                ),
                publisher="SAHIBEX Test",
            ),
            SearchResult(
                title="SAHIBEX Research Example",
                url="https://example.org/sahibex-research",
                snippet=(
                    "This second result verifies multi-result "
                    "search acquisition."
                ),
                publisher="SAHIBEX Test",
            ),
        ]

        return results[:max_results]


def make_pipeline(tmp_path: Path):
    database_path = tmp_path / "research.db"

    backend = CountingSearchBackend()

    provider = SearchResearchProvider(
        backend
    )

    acquisition_engine = ResearchAcquisitionEngine()

    acquisition_engine.register_provider(
        provider
    )

    pipeline = ResearchAcquisitionPipeline(
        database_path=str(database_path),
        acquisition_engine=acquisition_engine,
    )

    return pipeline, provider, backend


def make_request() -> AcquisitionRequest:
    return AcquisitionRequest(
        query="SAHIBEX search permission test",
        source_type="web",
        max_sources=2,
    )


def test_search_blocked_without_confirmation():
    with TemporaryDirectory() as temp_dir:
        pipeline, provider, backend = make_pipeline(
            Path(temp_dir)
        )

        try:
            request = make_request()

            blocked = False

            try:
                pipeline.acquire_and_ingest(
                    request,
                    provider_name="search",
                    confirmation=False,
                )
            except PermissionError:
                blocked = True

            assert blocked is True

            # Critical security assertion:
            # backend.search() must never execute before
            # NETWORK_ACCESS permission is granted.
            assert backend.calls == []

            print(
                "[PASS] search blocked without confirmation"
            )

            print(
                "[PASS] search backend was never executed"
            )

        finally:
            pipeline.close()


def test_search_executes_after_confirmation():
    with TemporaryDirectory() as temp_dir:
        pipeline, provider, backend = make_pipeline(
            Path(temp_dir)
        )

        try:
            request = make_request()

            result = pipeline.acquire_and_ingest(
                request,
                provider_name="search",
                confirmation=True,
            )

            assert result is not None

            assert len(backend.calls) == 1

            assert backend.calls[0]["query"] == (
                "SAHIBEX search permission test"
            )

            assert backend.calls[0]["max_results"] == 2

            assert result.stored_count == 2
            assert result.duplicate_count == 0

            assert len(result.ingested) == 2

            print(
                "[PASS] confirmed search executed"
            )

            print(
                "[PASS] search backend executed exactly once"
            )

            print(
                "[PASS] search results entered ingestion pipeline"
            )

            print(
                "[PASS] search results were stored"
            )

        finally:
            pipeline.close()


def test_search_results_preserve_discovery_metadata():
    with TemporaryDirectory() as temp_dir:
        pipeline, provider, backend = make_pipeline(
            Path(temp_dir)
        )

        try:
            request = make_request()

            result = pipeline.acquire_and_ingest(
                request,
                provider_name="search",
                confirmation=True,
            )

            assert result.stored_count == 2

            acquisition = result.acquisition

            assert acquisition.completed is True
            assert acquisition.status == "completed"

            assert len(acquisition.sources) == 2

            first = acquisition.sources[0]

            assert first.source_type == "web"

            assert (
                first.title
                == "SAHIBEX Search Integration"
            )

            assert (
                first.locator
                == "https://example.com/sahibex-search"
            )

            assert (
                first.metadata["provider"]
                == "search"
            )

            assert (
                first.metadata["backend"]
                == "counting_test_search"
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

            assert (
                first.metadata["reliability"]
                == 0.5
            )

            print(
                "[PASS] search source metadata preserved"
            )

            print(
                "[PASS] discovery-only classification preserved"
            )

            print(
                "[PASS] search ranking preserved"
            )

        finally:
            pipeline.close()


def test_search_provider_is_network_capable():
    with TemporaryDirectory() as temp_dir:
        pipeline, provider, backend = make_pipeline(
            Path(temp_dir)
        )

        try:
            assert provider.provider_name == "search"

            assert provider.requires_network is True

            assert (
                pipeline.acquisition_engine
                .provider_requires_network(
                    "search"
                )
                is True
            )

            print(
                "[PASS] search provider classified as network-capable"
            )

        finally:
            pipeline.close()


def test_blocked_search_does_not_create_research_data():
    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "research.db"

        pipeline, provider, backend = make_pipeline(
            Path(temp_dir)
        )

        try:
            request = make_request()

            try:
                pipeline.acquire_and_ingest(
                    request,
                    provider_name="search",
                    confirmation=False,
                )
            except PermissionError:
                pass

            # No backend execution.
            assert backend.calls == []

            # Search acquisition never happened.
            # Therefore no acquired sources should exist
            # in the result/storage path from this operation.
            assert database_path.exists()

            summary = pipeline.ingestion_pipeline.storage.summary()

            assert summary["sources"] == 0
            assert summary["documents"] == 0

            print(
                "[PASS] blocked search created no source"
            )

            print(
                "[PASS] blocked search created no document"
            )

        finally:
            pipeline.close()


def main():
    print(
        "SAHIBEX SEARCH PROVIDER PERMISSION INTEGRATION TEST"
    )

    test_search_blocked_without_confirmation()

    test_search_executes_after_confirmation()

    test_search_results_preserve_discovery_metadata()

    test_search_provider_is_network_capable()

    test_blocked_search_does_not_create_research_data()

    print(
        "SAHIBEX SEARCH PROVIDER PERMISSION INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
