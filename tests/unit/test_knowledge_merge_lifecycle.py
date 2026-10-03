from datetime import datetime, timezone
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
):
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        findings=list(findings or []),
        evidence=list(evidence or []),
        confidence=confidence,
        verified=verified,
    )


def main() -> None:
    print("SAHIBEX 6H-6C KNOWLEDGE MERGE LIFECYCLE TEST")

    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "knowledge_merge_lifecycle.db"

        primary = build_knowledge(
            "knowledge_001",
            "Python is a programming language.",
            findings=["finding_001"],
            evidence=["evidence_001"],
            confidence=0.70,
            verified=True,
        )

        duplicate = build_knowledge(
            "knowledge_002",
            "Python   is a programming language.",
            findings=["finding_002"],
            evidence=["evidence_002"],
            confidence=0.80,
            verified=True,
        )

        storage = ResearchStorage(database_path)

        # 1. Persist both original knowledge objects first.
        storage.save_knowledge(primary)
        storage.save_knowledge(duplicate)

        assert storage.get_knowledge("knowledge_001") is not None
        assert storage.get_knowledge("knowledge_002") is not None
        assert storage.knowledge_count() == 2

        print("[PASS] primary and duplicate persistence")

        # 2. Perform safe merge.
        service = KnowledgeMergeService()
        merge_result = service.merge(
            primary,
            duplicate,
        )

        assert merge_result.merged is True
        assert merge_result.safe_to_merge is True
        assert merge_result.knowledge is not None

        merged = merge_result.knowledge

        print("[PASS] safe merge execution")

        # 3. Persist merged primary.
        storage.save_knowledge(merged)

        loaded_primary = storage.get_knowledge(
            "knowledge_001"
        )

        assert loaded_primary is not None
        assert loaded_primary.findings == [
            "finding_001",
            "finding_002",
        ]
        assert loaded_primary.evidence == [
            "evidence_001",
            "evidence_002",
        ]
        assert loaded_primary.confidence == 0.80
        assert loaded_primary.verified is True

        print("[PASS] merged primary persistence")

        # 4. Duplicate record must still exist.
        loaded_duplicate = storage.get_knowledge(
            "knowledge_002"
        )

        assert loaded_duplicate is not None
        assert loaded_duplicate.knowledge_id == "knowledge_002"

        print("[PASS] duplicate record preserved")

        # 5. A merge lifecycle record must be persisted.
        assert hasattr(
            storage,
            "save_knowledge_merge",
        )

        merged_at = datetime.now(timezone.utc)

        storage.save_knowledge_merge(
            merge_id="merge_001",
            primary_knowledge_id="knowledge_001",
            duplicate_knowledge_id="knowledge_002",
            similarity_score=merge_result.similarity_score,
            status="MERGED",
            merged_at=merged_at,
            metadata={
                "reason": "exact_normalized_duplicate",
            },
        )

        print("[PASS] merge lifecycle persistence")

        # 6. Retrieve lifecycle record.
        merge_record = storage.get_knowledge_merge(
            "merge_001"
        )

        assert merge_record is not None
        assert merge_record["merge_id"] == "merge_001"
        assert merge_record["primary_knowledge_id"] == (
            "knowledge_001"
        )
        assert merge_record["duplicate_knowledge_id"] == (
            "knowledge_002"
        )
        assert merge_record["similarity_score"] == 1.0
        assert merge_record["status"] == "MERGED"
        assert merge_record["metadata"] == {
            "reason": "exact_normalized_duplicate",
        }

        print("[PASS] merge lifecycle retrieval")

        # 7. Verify merge history survives restart.
        storage.close()

        storage = ResearchStorage(database_path)

        restarted_record = storage.get_knowledge_merge(
            "merge_001"
        )

        assert restarted_record is not None
        assert restarted_record["merge_id"] == "merge_001"
        assert restarted_record["primary_knowledge_id"] == (
            "knowledge_001"
        )
        assert restarted_record["duplicate_knowledge_id"] == (
            "knowledge_002"
        )
        assert restarted_record["status"] == "MERGED"

        print("[PASS] merge lifecycle persistence across restart")

        # 8. Both knowledge records must still exist.
        assert storage.get_knowledge(
            "knowledge_001"
        ) is not None

        assert storage.get_knowledge(
            "knowledge_002"
        ) is not None

        assert storage.knowledge_count() == 2

        print("[PASS] non-destructive knowledge integrity")

        # 9. Merge history count.
        assert hasattr(
            storage,
            "knowledge_merge_count",
        )

        assert storage.knowledge_merge_count() == 1

        print("[PASS] merge history count")

        storage.close()

    print(
        "SAHIBEX 6H-6C KNOWLEDGE MERGE LIFECYCLE TEST: PASS"
    )


if __name__ == "__main__":
    main()
