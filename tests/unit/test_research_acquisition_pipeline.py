from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.acquisition import (
    AcquisitionRequest,
    AcquisitionResult,
    AcquiredSource,
    ResearchAcquisitionEngine,
    ResearchAcquisitionProvider,
)
from core.research.acquisition_pipeline import (
    ResearchAcquisitionPipeline,
)


class MockAcquisitionProvider(ResearchAcquisitionProvider):
    provider_name = "mock-web"

    def acquire(self, request):
        return AcquisitionResult(
            query=request.query,
            completed=True,
            status="SUCCESS",
            sources=[
                AcquiredSource(
                    source_id="web-source-001",
                    title="Mock AI Security Article",
                    source_type="web",
                    locator="https://example.test/ai-security",
                    publisher="Mock Publisher",
                    content=(
                        "AI security requires controlled "
                        "permissions and verification."
                    ),
                    metadata={
                        "reliability": 0.9,
                    },
                )
            ],
        )


class DuplicateAcquisitionProvider(
    ResearchAcquisitionProvider
):
    provider_name = "duplicate-web"

    def acquire(self, request):
        return AcquisitionResult(
            query=request.query,
            completed=True,
            status="SUCCESS",
            sources=[
                AcquiredSource(
                    source_id="web-source-002",
                    title="Same Content Different Source",
                    source_type="web",
                    locator="https://example.test/duplicate",
                    publisher="Another Publisher",
                    content=(
                        "AI security requires controlled "
                        "permissions and verification."
                    ),
                )
            ],
        )


def main():
    print("SAHIBEX RESEARCH ACQUISITION PIPELINE TEST")

    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "research.db"

        acquisition_engine = ResearchAcquisitionEngine()

        acquisition_engine.register_provider(
            MockAcquisitionProvider()
        )

        pipeline = ResearchAcquisitionPipeline(
            database_path,
            acquisition_engine,
        )

        # -----------------------------------------------------
        # Acquisition + ingestion
        # -----------------------------------------------------

        request = AcquisitionRequest(
            query="AI security",
            max_sources=5,
        )

        result = pipeline.acquire_and_ingest(
            request,
            "mock-web",
        )

        assert result.acquisition.completed is True
        assert result.acquisition.query == "AI security"
        print("[PASS] acquisition completed")

        assert len(result.acquisition.sources) == 1
        print("[PASS] acquired source received")

        assert result.stored_count == 1
        assert result.duplicate_count == 0
        print("[PASS] acquired source ingested")

        ingestion = result.ingested[0]

        assert ingestion.document_stored is True
        assert ingestion.duplicate is False
        assert ingestion.matched_document_id is None
        print("[PASS] document stored")

        # -----------------------------------------------------
        # Source conversion
        # -----------------------------------------------------

        source = pipeline.ingestion_pipeline.storage.get_source(
            "web-source-001"
        )

        assert source is not None
        assert source.source_type == "web"
        assert source.publisher == "Mock Publisher"
        assert source.reliability == 0.9
        assert source.metadata["acquisition"] is True

        print("[PASS] acquired source converted to ResearchSource")

        # -----------------------------------------------------
        # Document conversion
        # -----------------------------------------------------

        document = pipeline.ingestion_pipeline.storage.get_document(
            ingestion.document_id
        )

        assert document is not None
        assert document.source_id == "web-source-001"
        assert document.title == "Mock AI Security Article"
        assert document.content.startswith("AI security requires")
        assert document.content_hash
        assert document.metadata["acquisition"] is True

        print("[PASS] acquired source converted to ResearchDocument")

        # -----------------------------------------------------
        # Persistent storage
        # -----------------------------------------------------

        assert (
            pipeline.ingestion_pipeline.storage.source_count()
            == 1
        )

        assert (
            pipeline.ingestion_pipeline.storage.document_count()
            == 1
        )

        print("[PASS] source persisted")

        print("[PASS] document persisted")

        # -----------------------------------------------------
        # Existing ResearchEngine integration
        # -----------------------------------------------------

        assert (
            "web-source-001"
            in pipeline.ingestion_pipeline.engine.sources
        )

        assert (
            ingestion.document_id
            in pipeline.ingestion_pipeline.engine.documents
        )

        print("[PASS] ResearchEngine integration")

        # -----------------------------------------------------
        # Duplicate acquisition protection
        # -----------------------------------------------------

        acquisition_engine.register_provider(
            DuplicateAcquisitionProvider()
        )

        duplicate_result = pipeline.acquire_and_ingest(
            request,
            "duplicate-web",
        )

        assert duplicate_result.stored_count == 0
        assert duplicate_result.duplicate_count == 1

        duplicate_ingestion = (
            duplicate_result.ingested[0]
        )

        assert duplicate_ingestion.duplicate is True
        assert duplicate_ingestion.document_stored is False
        assert (
            duplicate_ingestion.matched_document_id
            == ingestion.document_id
        )

        print("[PASS] duplicate acquired content blocked")

        # -----------------------------------------------------
        # Persistent counts remain unchanged
        # -----------------------------------------------------

        assert (
            pipeline.ingestion_pipeline.storage.source_count()
            == 2
        )

        assert (
            pipeline.ingestion_pipeline.storage.document_count()
            == 1
        )

        print("[PASS] duplicate did not create document")

        # -----------------------------------------------------
        # Restart persistence
        # -----------------------------------------------------

        pipeline.close()

        new_acquisition_engine = ResearchAcquisitionEngine()
        new_pipeline = ResearchAcquisitionPipeline(
            database_path,
            new_acquisition_engine,
        )

        restored_source = (
            new_pipeline.ingestion_pipeline.storage.get_source(
                "web-source-001"
            )
        )

        restored_document = (
            new_pipeline.ingestion_pipeline.storage.get_document(
                ingestion.document_id
            )
        )

        assert restored_source is not None
        assert restored_document is not None

        assert (
            restored_document.content
            == "AI security requires controlled "
            "permissions and verification."
        )

        print("[PASS] source survives restart")

        print("[PASS] document survives restart")

        assert (
            new_pipeline.ingestion_pipeline.storage.source_count()
            == 2
        )

        assert (
            new_pipeline.ingestion_pipeline.storage.document_count()
            == 1
        )

        print("[PASS] persistent counts survive restart")

        new_pipeline.close()

    print("SAHIBEX RESEARCH ACQUISITION PIPELINE TEST: PASS")


if __name__ == "__main__":
    main()
