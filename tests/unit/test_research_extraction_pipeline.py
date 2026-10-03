from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.engine import ResearchEngine
from core.research.extraction_pipeline import (
    ResearchExtractionPipeline,
)
from core.research.extractor import (
    ExtractedFinding,
    ResearchExtractor,
)
from core.research.models import (
    ResearchDocument,
    ResearchSource,
)
from core.research.pipeline import (
    ResearchIngestionPipeline,
)


class HighConfidenceTestExtractor(ResearchExtractor):
    """
    Test-only extractor.

    Production ResearchExtractor deliberately uses a conservative
    0.50 extraction confidence.

    This test extractor supplies strong evidence so that the existing
    ResearchEngine verification threshold can be exercised.
    """

    def extract(self, document: ResearchDocument):
        return [
            ExtractedFinding(
                claim="Evidence must remain linked to its source.",
                evidence_text=(
                    "Evidence must remain linked to its source."
                ),
                confidence=0.95,
            ),
            ExtractedFinding(
                claim=(
                    "Findings must be extracted before verification."
                ),
                evidence_text=(
                    "Findings must be extracted before verification."
                ),
                confidence=0.95,
            ),
        ]


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "research.db"

        source = ResearchSource(
            source_id="src-extraction-001",
            title="Extraction Test Source",
            source_type="web",
            locator="https://example.com/extraction",
            publisher="Example Research",
            reliability=0.95,
        )

        content = (
            "Evidence must remain linked to its source. "
            "Findings must be extracted before verification."
        )

        document = ResearchDocument(
            document_id="doc-extraction-001",
            source_id=source.source_id,
            title="Extraction Test Document",
            content=content,
            collected_at="2026-09-20T00:00:00+00:00",
            content_hash=ResearchEngine.hash_content(
                content
            ),
        )

        with ResearchIngestionPipeline(
            database_path
        ) as pipeline:

            # -------------------------------------------------
            # Document ingestion
            # -------------------------------------------------

            ingestion = pipeline.ingest(
                source,
                document,
            )

            assert ingestion.document_stored is True
            assert ingestion.duplicate is False

            # -------------------------------------------------
            # Extraction pipeline
            # -------------------------------------------------

            extraction_pipeline = ResearchExtractionPipeline(
                pipeline,
                extractor=HighConfidenceTestExtractor(),
            )

            result = extraction_pipeline.extract_and_verify(
                document
            )

            # -------------------------------------------------
            # Extraction
            # -------------------------------------------------

            assert result.document_id == document.document_id
            assert result.source_id == source.source_id
            assert result.extracted_count == 2
            assert len(result.findings) == 2

            # -------------------------------------------------
            # Finding
            # -------------------------------------------------

            first = result.findings[0]

            assert first.document_id == document.document_id
            assert first.source_id == source.source_id
            assert first.finding_stored is True

            finding = pipeline.engine.findings[
                first.finding_id
            ]

            assert finding.document_id == document.document_id

            assert finding.claim == (
                "Evidence must remain linked to its source."
            )

            assert finding.evidence_text == (
                "Evidence must remain linked to its source."
            )

            assert finding.confidence == 0.95

            # -------------------------------------------------
            # Evidence
            # -------------------------------------------------

            assert first.evidence_stored is True

            evidence = pipeline.engine.evidence[
                first.evidence_id
            ]

            assert evidence.finding_id == finding.finding_id
            assert evidence.source_id == source.source_id

            assert evidence.evidence_text == (
                "Evidence must remain linked to its source."
            )

            assert evidence.supports is True
            assert evidence.strength == 0.95

            # -------------------------------------------------
            # Knowledge creation
            # -------------------------------------------------

            assert len(pipeline.engine.knowledge) == 2

            knowledge_items = list(
                pipeline.engine.knowledge.values()
            )

            assert len(knowledge_items) == 2

            # -------------------------------------------------
            # Verification
            # -------------------------------------------------

            assert all(
                item.verified is True
                for item in knowledge_items
            )

            assert all(
                item.confidence >= 0.60
                for item in knowledge_items
            )

            # -------------------------------------------------
            # Knowledge linkage
            # -------------------------------------------------

            assert all(
                len(item.findings) == 1
                for item in knowledge_items
            )

            assert all(
                len(item.evidence) == 1
                for item in knowledge_items
            )

            # -------------------------------------------------
            # Persistent knowledge
            # -------------------------------------------------

            for item in knowledge_items:
                stored_knowledge = (
                    pipeline.storage.get_knowledge(
                        item.knowledge_id
                    )
                )

                assert stored_knowledge is not None
                assert stored_knowledge.verified is True

            print(
                "SAHIBEX RESEARCH EXTRACTION PIPELINE TEST"
            )
            print(
                "[PASS] document → extraction"
            )
            print(
                "[PASS] extraction → finding"
            )
            print(
                "[PASS] finding → evidence"
            )
            print(
                "[PASS] finding/source linkage"
            )
            print(
                "[PASS] evidence/finding linkage"
            )
            print(
                "[PASS] finding/evidence → knowledge"
            )
            print(
                "[PASS] knowledge verification"
            )
            print(
                "[PASS] verified knowledge persistence"
            )
            print(
                "SAHIBEX RESEARCH EXTRACTION PIPELINE TEST: PASS"
            )


if __name__ == "__main__":
    main()
