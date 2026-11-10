from __future__ import annotations

from datetime import datetime, timezone
import tempfile
from pathlib import Path

from core.research.models import KnowledgeCandidate
from core.research.engine import ResearchEngine
from core.research.storage import ResearchStorage
from core.research.query import ResearchQueryEngine


def main() -> None:
    print("SAHIBEX PERSISTENT KNOWLEDGE QUERY TEST")

    with tempfile.TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "research.db"

        # -----------------------------------------------------
        # 1. Create and persist knowledge
        # -----------------------------------------------------
        storage = ResearchStorage(database_path)

        knowledge = KnowledgeCandidate(
            knowledge_id="knowledge-persistent-001",
            statement="SAHIBEX uses verified research knowledge.",
            findings=["finding-001"],
            evidence=["evidence-001"],
            confidence=0.95,
            verified=True,
        )

        storage.save_knowledge(knowledge)
        storage.record_knowledge_verification(
            knowledge_id=knowledge.knowledge_id,
            status="VERIFIED",
            reason="Test fixture records an explicit verified lifecycle event.",
            verified_at=datetime.now(timezone.utc),
            metadata={"independent_source_count": 2, "supporting_source_count": 2},
        )

        assert storage.knowledge_count() == 1
        print("[PASS] knowledge persisted")

        storage.close()

        # -----------------------------------------------------
        # 2. Simulate SAHIBEX restart
        # -----------------------------------------------------
        restarted_storage = ResearchStorage(database_path)

        assert restarted_storage.knowledge_count() == 1
        print("[PASS] knowledge survives restart")

        # -----------------------------------------------------
        # 3. New empty ResearchEngine
        # -----------------------------------------------------
        engine = ResearchEngine()

        query_engine = ResearchQueryEngine(
            engine,
            storage=restarted_storage,
        )

        # -----------------------------------------------------
        # 4. Search persistent knowledge
        # -----------------------------------------------------
        result = query_engine.search(
            "verified research knowledge",
            verified_only=True,
        )

        assert result.total_matches == 1
        assert result.matches[0].knowledge_id == (
            "knowledge-persistent-001"
        )

        print("[PASS] persistent knowledge retrieval")

        # -----------------------------------------------------
        # 5. Verify confidence preserved
        # -----------------------------------------------------
        assert result.matches[0].confidence == 0.95
        print("[PASS] confidence preserved")

        # -----------------------------------------------------
        # 6. Verify verified-only protection
        # -----------------------------------------------------
        unverified = KnowledgeCandidate(
            knowledge_id="knowledge-unverified-001",
            statement="This is unverified research knowledge.",
            findings=["finding-002"],
            evidence=["evidence-002"],
            confidence=0.40,
            verified=False,
        )

        restarted_storage.save_knowledge(unverified)

        verified_result = query_engine.search(
            "unverified research knowledge",
            verified_only=True,
        )

        assert all(
            match.verified
            for match in verified_result.matches
        )

        print("[PASS] verified-only persistent filtering")

        # -----------------------------------------------------
        # 7. Allow unverified retrieval explicitly
        # -----------------------------------------------------
        all_result = query_engine.search(
            "unverified research knowledge",
            verified_only=False,
        )

        assert any(
            match.knowledge_id == "knowledge-unverified-001"
            for match in all_result.matches
        )

        print("[PASS] explicit unverified retrieval")

        restarted_storage.close()

    print("SAHIBEX PERSISTENT KNOWLEDGE QUERY TEST: PASS")


if __name__ == "__main__":
    main()
