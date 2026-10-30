from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.engine import ResearchEngine
from core.research.models import (
    Evidence,
    ResearchDocument,
    ResearchFinding,
    ResearchSource,
)
from core.research.pipeline import ResearchIngestionPipeline


def test_pipeline_rejects_forged_cross_source_evidence(tmp_path: Path) -> None:
    import pytest

    source_a = ResearchSource(
        source_id="source-a",
        title="Publisher A",
        source_type="web",
        locator="https://a.example/article",
        publisher="Publisher A",
        reliability=0.9,
    )
    source_b = ResearchSource(
        source_id="source-b",
        title="Publisher B",
        source_type="web",
        locator="https://b.example/article",
        publisher="Publisher B",
        reliability=0.9,
    )
    document_a = ResearchDocument(
        document_id="document-a",
        source_id="source-a",
        title="Publisher A article",
        content="A claim reported by publisher A.",
    )
    document_b = ResearchDocument(
        document_id="document-b",
        source_id="source-b",
        title="Publisher B article",
        content="Different content from publisher B.",
    )

    with ResearchIngestionPipeline(tmp_path / "provenance.db") as pipeline:
        pipeline.ingest(source_a, document_a)
        pipeline.ingest(source_b, document_b)
        pipeline.add_finding(
            ResearchFinding(
                finding_id="finding-a",
                document_id="document-a",
                claim="A claim reported by publisher A.",
                confidence=0.8,
            )
        )
        forged = Evidence(
            evidence_id="forged-evidence",
            finding_id="finding-a",
            source_id="source-b",
            evidence_text="A claim reported by publisher A.",
            supports=True,
            strength=0.99,
        )

        with pytest.raises(ValueError, match="does not match the finding document source"):
            pipeline.add_evidence(forged)

        assert pipeline.engine.evidence.get("forged-evidence") is None
        assert pipeline.storage.get_evidence("forged-evidence") is None


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "research.db"

        source = ResearchSource(
            source_id="src-001",
            title="SAHIBEX Evidence Source",
            source_type="web",
            locator="https://example.com/evidence",
            publisher="Example Research",
            reliability=0.95,
        )

        content = (
            "Evidence verification improves "
            "research reliability."
        )

        document = ResearchDocument(
            document_id="doc-001",
            source_id="src-001",
            title="Evidence Research",
            content=content,
            collected_at="2026-09-20T00:00:00+00:00",
            content_hash=ResearchEngine.hash_content(
                content
            ),
        )

        finding = ResearchFinding(
            finding_id="find-001",
            document_id="doc-001",
            claim=(
                "Evidence verification improves "
                "research reliability."
            ),
            evidence_text=(
                "The source explicitly discusses "
                "evidence verification."
            ),
            confidence=0.90,
            created_at="2026-09-20T00:00:00+00:00",
        )

        evidence = Evidence(
            evidence_id="evidence-001",
            finding_id="find-001",
            source_id="src-001",
            evidence_text=(
                "Supporting evidence from the "
                "research source."
            ),
            supports=True,
            strength=0.95,
            created_at="2026-09-20T00:00:00+00:00",
        )

        with ResearchIngestionPipeline(
            database_path
        ) as pipeline:

            ingestion = pipeline.ingest(
                source,
                document,
            )

            assert ingestion.document_stored is True
            assert ingestion.duplicate is False

            finding_result = pipeline.add_finding(
                finding
            )

            assert finding_result.stored is True
            assert (
                pipeline.storage.get_finding(
                    "find-001"
                )
                == finding
            )

            evidence_result = pipeline.add_evidence(
                evidence
            )

            assert evidence_result.stored is True
            assert (
                pipeline.storage.get_evidence(
                    "evidence-001"
                )
                == evidence
            )

            knowledge_result = pipeline.create_knowledge(
                statement=(
                    "Evidence verification improves "
                    "research reliability."
                ),
                finding_ids=["find-001"],
                evidence_ids=["evidence-001"],
            )

            assert knowledge_result.stored is True
            assert knowledge_result.confidence >= 0.60

            knowledge = pipeline.storage.get_knowledge(
                knowledge_result.knowledge_id
            )

            assert knowledge is not None
            assert knowledge.verified is False
            assert knowledge.metadata["verification_status"] == "UNVERIFIED"
            assert knowledge.metadata["supporting_source_count"] == 1

        print("SAHIBEX RESEARCH EVIDENCE PIPELINE TEST")
        print("[PASS] finding integration")
        print("[PASS] finding persistence")
        print("[PASS] evidence integration")
        print("[PASS] evidence persistence")
        print("[PASS] knowledge candidate creation")
        print("[PASS] single-source knowledge remains unverified")
        print("[PASS] unverified knowledge persistence")
        print(
            "SAHIBEX RESEARCH EVIDENCE PIPELINE TEST: PASS"
        )


if __name__ == "__main__":
    main()
