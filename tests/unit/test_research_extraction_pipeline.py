
from dataclasses import replace
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
from core.research.pipeline import ResearchIngestionPipeline


class HighConfidenceTestExtractor(ResearchExtractor):
    """Return strong test findings from a single document."""

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


def test_research_extraction_pipeline() -> None:
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
            content_hash=ResearchEngine.hash_content(content),
        )

        with ResearchIngestionPipeline(database_path) as pipeline:
            # 1. Document ingestion
            ingestion = pipeline.ingest(source, document)

            assert ingestion.document_stored is True
            assert ingestion.duplicate is False

            # A forged object with the same ID must not be allowed to
            # attach unrelated text to the registered source/document chain.
            extraction_pipeline = ResearchExtractionPipeline(
                pipeline,
                extractor=HighConfidenceTestExtractor(),
            )
            forged_document = replace(
                document,
                content="Forged claim attributed to a different document.",
            )
            try:
                extraction_pipeline.extract_document(forged_document)
            except ValueError as exc:
                assert "content does not match" in str(exc)
            else:
                raise AssertionError(
                    "extraction accepted altered content under a registered document ID"
                )
            assert not any(
                item.claim == "Forged claim attributed to a different document."
                for item in pipeline.engine.findings.values()
            )

            # 2. Extraction pipeline
            extraction_pipeline = ResearchExtractionPipeline(
                pipeline,
                extractor=HighConfidenceTestExtractor(),
            )

            result = extraction_pipeline.extract_and_verify(document)

            assert result.document_id == document.document_id
            assert result.source_id == source.source_id
            assert result.extracted_count == 2
            assert len(result.findings) == 2

            # 3. Finding and evidence linkage
            first = result.findings[0]

            assert first.document_id == document.document_id
            assert first.source_id == source.source_id
            assert first.finding_stored is True
            assert first.evidence_stored is True

            finding = pipeline.engine.findings[first.finding_id]
            evidence = pipeline.engine.evidence[first.evidence_id]

            assert finding.document_id == document.document_id
            assert finding.claim == (
                "Evidence must remain linked to its source."
            )
            assert finding.evidence_text == (
                "Evidence must remain linked to its source."
            )
            assert finding.confidence == 0.95

            assert evidence.finding_id == finding.finding_id
            assert evidence.source_id == source.source_id
            assert evidence.evidence_text == (
                "Evidence must remain linked to its source."
            )
            assert evidence.supports is True
            assert evidence.strength == evidence.metadata[
                "evidence_strength"
            ]["strength_score"]
            assert 0.0 <= evidence.strength <= 1.0

            # 4. Knowledge creation
            knowledge_items = list(pipeline.engine.knowledge.values())

            assert len(knowledge_items) == 2

            # 5. Single-source verification policy
            # One source is not sufficient to verify a knowledge claim.
            for item in knowledge_items:
                assert item.verified is False
                assert item.confidence >= 0.60
                assert item.metadata.get(
                    "verification_status"
                ) == "UNVERIFIED"
                assert item.metadata.get(
                    "independent_source_count", 0
                ) == 1

            # 6. Finding/evidence linkage remains intact
            assert all(
                len(item.findings) == 1
                for item in knowledge_items
            )
            assert all(
                len(item.evidence) == 1
                for item in knowledge_items
            )

            for item in knowledge_items:
                evidence_id = next(iter(item.evidence))
                stored_evidence = pipeline.storage.get_evidence(
                    evidence_id
                )

                assert stored_evidence is not None
                assert stored_evidence.finding_id in item.findings
                assert stored_evidence.source_id == source.source_id

            # 7. Persistent knowledge retains its unverified status
            for item in knowledge_items:
                stored_knowledge = pipeline.storage.get_knowledge(
                    item.knowledge_id
                )

                assert stored_knowledge is not None
                assert (
                    stored_knowledge.knowledge_id
                    == item.knowledge_id
                )
                assert stored_knowledge.verified is False
                assert stored_knowledge.metadata.get(
                    "verification_status"
                ) == "UNVERIFIED"

            print("SAHIBEX RESEARCH EXTRACTION PIPELINE TEST")
            print("[PASS] document ingestion")
            print("[PASS] document -> extraction")
            print("[PASS] extraction -> finding")
            print("[PASS] finding/source linkage")
            print("[PASS] finding -> evidence")
            print("[PASS] evidence/source linkage")
            print("[PASS] finding/evidence -> knowledge")
            print("[PASS] single-source verification is rejected")
            print("[PASS] unverified knowledge persistence")
            print("SAHIBEX RESEARCH EXTRACTION PIPELINE TEST: PASS")


if __name__ == "__main__":
    test_research_extraction_pipeline()
