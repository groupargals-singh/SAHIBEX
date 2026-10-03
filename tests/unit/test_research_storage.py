from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchDocument,
    ResearchFinding,
    ResearchSource,
)
from core.research.storage import ResearchStorage


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "research.db"

        source = ResearchSource(
            source_id="src-001",
            title="AI Security Research",
            source_type="web",
            locator="https://example.com/security",
            publisher="Example Research",
            reliability=0.9,
        )

        document = ResearchDocument(
            document_id="doc-001",
            source_id="src-001",
            title="AI Security Document",
            content="Research content for SAHIBEX.",
            collected_at="2026-09-20T00:00:00+00:00",
            content_hash="hash-001",
        )

        finding = ResearchFinding(
            finding_id="find-001",
            document_id="doc-001",
            claim="Verification improves research reliability.",
            evidence_text="The document describes verification controls.",
            confidence=0.8,
            created_at="2026-09-20T00:00:00+00:00",
        )

        evidence = Evidence(
            evidence_id="evidence-001",
            finding_id="find-001",
            source_id="src-001",
            evidence_text="Supporting research evidence.",
            supports=True,
            strength=0.9,
            created_at="2026-09-20T00:00:00+00:00",
        )

        knowledge = KnowledgeCandidate(
            knowledge_id="knowledge-001",
            statement="Research evidence should be verified.",
            findings=["find-001"],
            evidence=["evidence-001"],
            confidence=0.85,
            verified=True,
            created_at="2026-09-20T00:00:00+00:00",
            last_verified_at="2026-09-20T00:00:00+00:00",
        )

        # -------------------------------------------------
        # First storage session
        # -------------------------------------------------

        with ResearchStorage(database_path) as storage:
            storage.save_source(source)
            storage.save_document(document)
            storage.save_finding(finding)
            storage.save_evidence(evidence)
            storage.save_knowledge(knowledge)

            assert storage.get_source("src-001") == source
            assert storage.get_document("doc-001") == document
            assert storage.get_finding("find-001") == finding
            assert storage.get_evidence("evidence-001") == evidence
            assert storage.get_knowledge("knowledge-001") == knowledge

            found_document = storage.find_document_by_hash(
                "hash-001"
            )

            assert found_document == document

            summary = storage.summary()

            assert summary["sources"] == 1
            assert summary["documents"] == 1
            assert summary["findings"] == 1
            assert summary["evidence"] == 1
            assert summary["knowledge"] == 1

        # -------------------------------------------------
        # Second storage session:
        # proves persistence across restart.
        # -------------------------------------------------

        with ResearchStorage(database_path) as storage:
            assert storage.get_source("src-001") == source
            assert storage.get_document("doc-001") == document
            assert storage.get_finding("find-001") == finding
            assert storage.get_evidence("evidence-001") == evidence
            assert storage.get_knowledge("knowledge-001") == knowledge

            assert storage.source_count() == 1
            assert storage.document_count() == 1
            assert storage.finding_count() == 1
            assert storage.evidence_count() == 1
            assert storage.knowledge_count() == 1

        print("SAHIBEX RESEARCH STORAGE TEST")
        print("[PASS] source persistence")
        print("[PASS] document persistence")
        print("[PASS] finding persistence")
        print("[PASS] evidence persistence")
        print("[PASS] knowledge persistence")
        print("[PASS] document hash lookup")
        print("[PASS] storage summary")
        print("[PASS] persistence across restart")
        print("SAHIBEX RESEARCH STORAGE TEST: PASS")


if __name__ == "__main__":
    main()
