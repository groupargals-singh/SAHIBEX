from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.acquisition import (
    AcquisitionRequest,
    ResearchAcquisitionEngine,
)
from core.research.acquisition_pipeline import ResearchAcquisitionPipeline
from core.research.web_provider import (
    DirectWebResearchProvider,
    WebProviderConfig,
)


class StubDirectWebProvider(DirectWebResearchProvider):
    """
    Deterministic test version of DirectWebResearchProvider.

    The real provider remains network-capable, but the actual HTTP
    operation is replaced so this integration test does not depend
    on the public internet.
    """

    def __init__(self):
        super().__init__(
            WebProviderConfig(
                timeout_seconds=5.0,
                max_response_bytes=100_000,
                max_sources=5,
            )
        )

        self.fetch_calls: list[str] = []

    def fetch_url(self, url: str) -> dict:
        self.fetch_calls.append(url)

        content = """
        <html>
            <head>
                <title>SAHIBEX Integration Test</title>
            </head>
            <body>
                <h1>SAHIBEX Research Test</h1>
                <p>
                    This document verifies the direct web research
                    acquisition and permission boundary.
                </p>
            </body>
        </html>
        """

        return {
            "url": url,
            "final_url": url,
            "status": 200,
            "content_type": "text/html",
            "content": content,
            "bytes": len(content.encode("utf-8")),
        }


def make_pipeline(tmp_path: Path):
    database_path = tmp_path / "research.db"

    acquisition_engine = ResearchAcquisitionEngine()

    provider = StubDirectWebProvider()

    acquisition_engine.register_provider(provider)

    pipeline = ResearchAcquisitionPipeline(
        database_path=str(database_path),
        acquisition_engine=acquisition_engine,
    )

    return pipeline, provider


def make_request() -> AcquisitionRequest:
    return AcquisitionRequest(
        query="SAHIBEX integration test",
        source_type="web",
        max_sources=1,
        metadata={
            "urls": [
                "https://example.com/sahibex-test"
            ]
        },
    )


def test_network_provider_blocked_without_confirmation():
    with TemporaryDirectory() as temp_dir:
        pipeline, provider = make_pipeline(Path(temp_dir))

        try:
            request = make_request()

            blocked = False

            try:
                pipeline.acquire_and_ingest(
                    request,
                    provider_name="direct_web",
                    confirmation=False,
                )
            except PermissionError:
                blocked = True

            assert blocked is True

            # Critical security assertion:
            # the provider must never execute before permission.
            assert provider.fetch_calls == []

            print(
                "[PASS] network provider blocked without confirmation"
            )

            print(
                "[PASS] blocked provider was never executed"
            )

        finally:
            pipeline.close()


def test_network_provider_executes_after_confirmation():
    with TemporaryDirectory() as temp_dir:
        pipeline, provider = make_pipeline(Path(temp_dir))

        try:
            request = make_request()

            result = pipeline.acquire_and_ingest(
                request,
                provider_name="direct_web",
                confirmation=True,
            )

            assert result is not None

            assert provider.fetch_calls == [
                "https://example.com/sahibex-test"
            ]

            assert result.stored_count == 1
            assert result.duplicate_count == 0

            assert len(result.ingested) == 1

            ingestion = result.ingested[0]

            assert ingestion.duplicate is False
            assert ingestion.document_stored is True
            assert ingestion.source_registered is True
            assert ingestion.source_id
            assert ingestion.document_id
            assert ingestion.content_hash

            print(
                "[PASS] confirmed network provider executed"
            )

            print(
                "[PASS] provider executed exactly once"
            )

            print(
                "[PASS] acquired source was ingested"
            )

            print(
                "[PASS] new research document was stored"
            )

        finally:
            pipeline.close()


def test_network_provider_result_contains_research_metadata():
    with TemporaryDirectory() as temp_dir:
        pipeline, provider = make_pipeline(Path(temp_dir))

        try:
            request = make_request()

            result = pipeline.acquire_and_ingest(
                request,
                provider_name="direct_web",
                confirmation=True,
            )

            assert result.stored_count == 1
            assert result.duplicate_count == 0
            assert len(result.ingested) == 1

            ingestion = result.ingested[0]

            # Validate the actual IngestionResult contract.
            assert isinstance(
                ingestion.source_id,
                str,
            )
            assert ingestion.source_id

            assert isinstance(
                ingestion.document_id,
                str,
            )
            assert ingestion.document_id

            assert ingestion.source_registered is True
            assert ingestion.document_stored is True
            assert ingestion.duplicate is False
            assert ingestion.matched_document_id is None

            assert isinstance(
                ingestion.content_hash,
                str,
            )
            assert len(ingestion.content_hash) == 64

            # Validate acquisition-level information.
            assert result.acquisition.completed is True
            assert result.acquisition.status == "completed"

            assert len(
                result.acquisition.sources
            ) == 1

            acquired_source = (
                result.acquisition.sources[0]
            )

            assert acquired_source.source_type == "web"

            assert (
                acquired_source.title
                == "SAHIBEX Integration Test"
            )

            assert (
                "SAHIBEX Research Test"
                in acquired_source.content
            )

            assert (
                acquired_source.metadata["provider"]
                == "direct_web"
            )

            assert (
                acquired_source.metadata["http_status"]
                == 200
            )

            assert (
                acquired_source.metadata["content_type"]
                == "text/html"
            )

            assert (
                acquired_source.metadata["content_hash"]
                == ingestion.content_hash
            )

            print(
                "[PASS] ingestion result matches actual API"
            )

            print(
                "[PASS] research source metadata preserved"
            )

            print(
                "[PASS] content hash preserved"
            )

            print(
                "[PASS] acquisition metadata preserved"
            )

        finally:
            pipeline.close()


def test_second_acquisition_is_deduplicated():
    with TemporaryDirectory() as temp_dir:
        pipeline, provider = make_pipeline(Path(temp_dir))

        try:
            request = make_request()

            first = pipeline.acquire_and_ingest(
                request,
                provider_name="direct_web",
                confirmation=True,
            )

            assert first.stored_count == 1
            assert first.duplicate_count == 0

            first_ingestion = first.ingested[0]

            assert first_ingestion.duplicate is False
            assert first_ingestion.document_stored is True

            second = pipeline.acquire_and_ingest(
                request,
                provider_name="direct_web",
                confirmation=True,
            )

            assert second.stored_count == 0
            assert second.duplicate_count == 1

            assert len(second.ingested) == 1

            second_ingestion = second.ingested[0]

            assert second_ingestion.duplicate is True
            assert second_ingestion.document_stored is False

            assert (
                second_ingestion.matched_document_id
                == first_ingestion.document_id
            )

            assert (
                second_ingestion.content_hash
                == first_ingestion.content_hash
            )

            # Acquisition happens again, but persistent ingestion
            # correctly prevents duplicate storage.
            assert len(provider.fetch_calls) == 2

            print(
                "[PASS] duplicate research content detected"
            )

            print(
                "[PASS] duplicate document was not stored again"
            )

            print(
                "[PASS] matched existing document identified"
            )

        finally:
            pipeline.close()


def main():
    print(
        "SAHIBEX DIRECT WEB PROVIDER INTEGRATION TEST"
    )

    test_network_provider_blocked_without_confirmation()

    test_network_provider_executes_after_confirmation()

    test_network_provider_result_contains_research_metadata()

    test_second_acquisition_is_deduplicated()

    print(
        "SAHIBEX DIRECT WEB PROVIDER INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
