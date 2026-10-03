from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.models import (
    ResearchDocument,
    ResearchSource,
)
from core.research.pipeline import (
    ResearchIngestionPipeline,
)


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "research.db"

        source = ResearchSource(
            source_id="src-001",
            title="SAHIBEX Research Source",
            source_type="web",
            locator="https://example.com/research",
            publisher="Example Research",
            reliability=0.9,
        )

        document = ResearchDocument(
            document_id="doc-001",
            source_id="src-001",
            title="Research Document",
            content=(
                "SAHIBEX verifies evidence before "
                "creating trusted knowledge."
            ),
            collected_at="2026-09-20T00:00:00+00:00",
            content_hash="",
        )

        # ResearchEngine generates the authoritative content hash.
        from core.research.engine import ResearchEngine

        document = ResearchDocument(
            document_id=document.document_id,
            source_id=document.source_id,
            title=document.title,
            content=document.content,
            collected_at=document.collected_at,
            content_hash=ResearchEngine.hash_content(
                document.content
            ),
            language=document.language,
            metadata=document.metadata,
        )

        # ---------------------------------------------
        # First ingestion
        # ---------------------------------------------

        with ResearchIngestionPipeline(
            database_path
        ) as pipeline:

            result = pipeline.ingest(
                source,
                document,
            )

            assert result.source_id == "src-001"
            assert result.document_id == "doc-001"
            assert result.source_registered is True
            assert result.document_stored is True
            assert result.duplicate is False
            assert result.matched_document_id is None

            assert (
                pipeline.storage.get_document("doc-001")
                == document
            )

            assert (
                pipeline.engine.documents["doc-001"]
                == document
            )

            # Same document again.
            duplicate_result = pipeline.ingest(
                source,
                document,
            )

            assert duplicate_result.duplicate is True
            assert (
                duplicate_result.matched_document_id
                == "doc-001"
            )

        # ---------------------------------------------
        # Restart pipeline.
        # ---------------------------------------------

        with ResearchIngestionPipeline(
            database_path
        ) as pipeline:

            restart_duplicate = pipeline.ingest(
                source,
                document,
            )

            assert restart_duplicate.duplicate is True
            assert (
                restart_duplicate.matched_document_id
                == "doc-001"
            )

        print("SAHIBEX RESEARCH INGESTION TEST")
        print("[PASS] source registration")
        print("[PASS] new document ingestion")
        print("[PASS] persistent document storage")
        print("[PASS] research engine integration")
        print("[PASS] duplicate protection")
        print("[PASS] pipeline restart protection")
        print("SAHIBEX RESEARCH INGESTION TEST: PASS")


if __name__ == "__main__":
    main()
