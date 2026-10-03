from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.knowledge_merge import KnowledgeMergeService
from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


def build_knowledge(
    knowledge_id: str,
    statement: str,
    *,
    findings=None,
    evidence=None,
    confidence=0.0,
    verified=False,
    metadata=None,
):
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        findings=list(findings or []),
        evidence=list(evidence or []),
        confidence=confidence,
        verified=verified,
        metadata=dict(metadata or {}),
    )


def main() -> None:
    print("SAHIBEX 6H-6C KNOWLEDGE MERGE PERSISTENCE TEST")

    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "knowledge_merge.db"

        primary = build_knowledge(
            "knowledge_001",
            "Python is a programming language.",
            findings=["finding_001"],
            evidence=["evidence_001"],
            confidence=0.70,
            verified=True,
            metadata={"origin": "primary"},
        )

        duplicate = build_knowledge(
            "knowledge_002",
            "Python   is a programming language.",
            findings=["finding_002"],
            evidence=["evidence_002"],
            confidence=0.80,
            verified=True,
            metadata={"origin": "duplicate"},
        )

        service = KnowledgeMergeService()
        merge_result = service.merge(primary, duplicate)

        assert merge_result.merged is True
        assert merge_result.knowledge is not None

        merged = merge_result.knowledge

        # 1. Persist merged knowledge
        storage = ResearchStorage(database_path)

        storage.save_knowledge(merged)

        loaded = storage.get_knowledge(
            "knowledge_001"
        )

        assert loaded is not None
        assert loaded.knowledge_id == "knowledge_001"
        assert loaded.statement == (
            "Python is a programming language."
        )
        print("[PASS] merged knowledge persistence")

        # 2. Verify merged findings/evidence survived
        assert loaded.findings == [
            "finding_001",
            "finding_002",
        ]
        assert loaded.evidence == [
            "evidence_001",
            "evidence_002",
        ]
        print("[PASS] merged finding/evidence persistence")

        # 3. Verify confidence and verification survived
        assert loaded.confidence == 0.80
        assert loaded.verified is True
        print("[PASS] merged confidence/verification persistence")

        # 4. Verify metadata survived
        assert loaded.metadata == {
            "origin": "primary"
        } or loaded.metadata == {
            "origin": "primary",
            "origin_1": "duplicate",
        } or loaded.metadata == {
            "origin": "primary",
            "duplicate": "duplicate",
        }
        print("[PASS] merged metadata persistence")

        storage.close()

        # 5. Verify persistence after restart
        storage = ResearchStorage(database_path)

        reloaded = storage.get_knowledge(
            "knowledge_001"
        )

        assert reloaded is not None
        assert reloaded.knowledge_id == "knowledge_001"
        assert reloaded.findings == [
            "finding_001",
            "finding_002",
        ]
        assert reloaded.evidence == [
            "evidence_001",
            "evidence_002",
        ]
        assert reloaded.confidence == 0.80
        assert reloaded.verified is True

        print("[PASS] persistence across restart")

        # 6. Duplicate must not be silently created as the merged object
        duplicate_loaded = storage.get_knowledge(
            "knowledge_002"
        )

        assert duplicate_loaded is None
        print(
            "[PASS] duplicate is not persisted as merged replacement"
        )

        # 7. Storage count remains exactly one
        assert storage.knowledge_count() == 1
        print("[PASS] knowledge count integrity")

        storage.close()

    print(
        "SAHIBEX 6H-6C KNOWLEDGE MERGE PERSISTENCE TEST: PASS"
    )


if __name__ == "__main__":
    main()
