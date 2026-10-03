from __future__ import annotations

import tempfile
from pathlib import Path

from core.research.acquisition import (
    AcquisitionRequest,
    ResearchAcquisitionEngine,
)
from core.research.acquisition_pipeline import (
    ResearchAcquisitionPipeline,
)
from core.research.document_provider import (
    DocumentProviderConfig,
    LocalDocumentResearchProvider,
)


def check(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir).resolve()
        database_path = root / "research.db"

        documents = root / "documents"
        documents.mkdir()

        document_path = documents / "research.txt"

        document_path.write_text(
            "SAHIBEX document pipeline integration test.\n"
            "This document must enter the research ingestion pipeline.",
            encoding="utf-8",
        )

        provider = LocalDocumentResearchProvider(
            DocumentProviderConfig(
                project_root=root,
            )
        )

        acquisition_engine = ResearchAcquisitionEngine(
            providers=[
                provider,
            ]
        )

        check(
            acquisition_engine.providers()
            == ["document"],
            "document provider was not registered",
        )

        check(
            acquisition_engine.provider_requires_network(
                "document"
            )
            is False,
            "document provider incorrectly requires network",
        )

        print(
            "[PASS] document provider registered"
        )

        request = AcquisitionRequest(
            query="SAHIBEX document pipeline integration",
            source_type="document",
            metadata={
                "path": "documents/research.txt",
            },
        )

        pipeline = ResearchAcquisitionPipeline(
            database_path=database_path,
            acquisition_engine=acquisition_engine,
        )

        try:
            # -----------------------------------------------------
            # Permission boundary
            # -----------------------------------------------------

            permission = (
                pipeline.check_network_permission(
                    "document",
                    confirmation=False,
                )
            )

            check(
                permission["allowed"] is True,
                "non-network document provider was blocked",
            )

            check(
                permission["requires_network"] is False,
                "document provider reported network requirement",
            )

            print(
                "[PASS] non-network permission boundary"
            )

            # -----------------------------------------------------
            # Full acquisition + ingestion
            # -----------------------------------------------------

            result = pipeline.acquire_and_ingest(
                request,
                provider_name="document",
                confirmation=False,
            )

            check(
                result.acquisition.completed is True,
                "document acquisition did not complete",
            )

            check(
                result.acquisition.status
                == "completed",
                "acquisition status mismatch",
            )

            check(
                len(result.acquisition.sources)
                == 1,
                "expected one acquired document",
            )

            check(
                result.stored_count == 1,
                "expected one stored document",
            )

            check(
                result.duplicate_count == 0,
                "first ingestion was incorrectly marked duplicate",
            )

            check(
                len(result.ingested) == 1,
                "expected one ingestion result",
            )

            ingestion = result.ingested[0]

            check(
                ingestion.duplicate is False,
                "first ingestion unexpectedly duplicate",
            )

            print(
                "[PASS] document acquisition entered ingestion pipeline"
            )

            print(
                "[PASS] document stored in research pipeline"
            )

            # -----------------------------------------------------
            # Metadata propagation
            # -----------------------------------------------------

            acquired = result.acquisition.sources[0]

            check(
                acquired.source_type == "document",
                "source type was not preserved",
            )

            check(
                acquired.locator
                == "documents/research.txt",
                "document locator was not preserved",
            )

            check(
                acquired.metadata[
                    "content_is_full_document"
                ]
                is True,
                "full-document metadata was lost",
            )

            check(
                acquired.metadata[
                    "provider_name"
                ]
                == "document",
                "provider metadata was lost",
            )

            print(
                "[PASS] document metadata preserved"
            )

            # -----------------------------------------------------
            # Second acquisition / deduplication
            # -----------------------------------------------------

            second_result = pipeline.acquire_and_ingest(
                request,
                provider_name="document",
                confirmation=False,
            )

            check(
                second_result.acquisition.completed
                is True,
                "second acquisition failed",
            )

            check(
                second_result.stored_count == 0,
                "duplicate document was stored again",
            )

            check(
                second_result.duplicate_count == 1,
                "duplicate document was not detected",
            )

            check(
                len(second_result.ingested) == 1,
                "second ingestion result missing",
            )

            check(
                second_result.ingested[0].duplicate
                is True,
                "second ingestion was not marked duplicate",
            )

            print(
                "[PASS] duplicate document detected"
            )

            # -----------------------------------------------------
            # Research source/document conversion
            # -----------------------------------------------------

            converted_source = pipeline._build_source(
                acquired
            )

            converted_document = pipeline._build_document(
                acquired
            )

            check(
                converted_source.source_type
                == "document",
                "ResearchSource type mismatch",
            )

            check(
                converted_source.source_id
                == acquired.source_id,
                "ResearchSource ID mismatch",
            )

            check(
                converted_document.source_id
                == acquired.source_id,
                "ResearchDocument source ID mismatch",
            )

            check(
                converted_document.content
                == acquired.content,
                "ResearchDocument content mismatch",
            )

            check(
                converted_document.content_hash,
                "ResearchDocument content hash missing",
            )

            print(
                "[PASS] research source/document conversion"
            )

            print()
            print(
                "SAHIBEX DOCUMENT PROVIDER PIPELINE "
                "INTEGRATION TEST: PASS"
            )

        finally:
            pipeline.close()


if __name__ == "__main__":
    main()
