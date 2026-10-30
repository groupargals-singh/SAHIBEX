from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.operational_memory_knowledge import (
    OperationalMemoryKnowledgeIntegration,
    OperationalMemoryKnowledgeResult,
)
from core.research.knowledge_conflict import (
    CONFLICT_TYPE_EXPLICIT_NEGATION,
    RESOLUTION_UNRESOLVED,
    KnowledgeConflictRecord,
)
from core.research.memory_object import MemoryCandidate
from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


def build_storage(database_path: Path) -> ResearchStorage:
    storage = ResearchStorage(database_path)

    storage.save_memory(
        MemoryCandidate(
            memory_id="memory-python",
            content="User is building SAHIBEX with Python.",
            memory_type="project",
            source="user",
            importance=0.9,
            confidence=1.0,
            tags=["sahibex", "python", "development"],
            metadata={"project": "SAHIBEX"},
        )
    )

    storage.save_memory(
        MemoryCandidate(
            memory_id="memory-termux",
            content="User develops SAHIBEX in Termux.",
            memory_type="environment",
            source="user",
            importance=0.8,
            confidence=0.95,
            tags=["sahibex", "termux"],
            metadata={"project": "SAHIBEX"},
        )
    )

    storage.save_memory(
        MemoryCandidate(
            memory_id="memory-trading",
            content="Quantum-bot is a trading specialist brain.",
            memory_type="project",
            source="user",
            importance=0.7,
            confidence=0.9,
            tags=["quantum-bot", "trading"],
            metadata={"project": "quantum-bot"},
        )
    )

    storage.save_knowledge(
        KnowledgeCandidate(
            knowledge_id="knowledge-python",
            statement="SAHIBEX uses Python as its primary implementation language.",
            confidence=0.95,
            verified=True,
            metadata={"topic": "SAHIBEX"},
        )
    )

    storage.save_knowledge(
        KnowledgeCandidate(
            knowledge_id="knowledge-termux",
            statement="SAHIBEX is developed in the Termux environment.",
            confidence=0.9,
            verified=True,
            metadata={"topic": "SAHIBEX"},
        )
    )

    now = datetime.now(timezone.utc)
    for offset, knowledge_id in enumerate(
        ("knowledge-python", "knowledge-termux")
    ):
        storage.record_knowledge_verification(
            knowledge_id=knowledge_id,
            status="VERIFIED",
            reason="Test fixture has persisted verified lifecycle evidence.",
            verified_at=now + timedelta(seconds=offset),
        )

    storage.save_knowledge(
        KnowledgeCandidate(
            knowledge_id="knowledge-unverified",
            statement="SAHIBEX may eventually support additional environments.",
            confidence=0.5,
            verified=False,
            metadata={"topic": "SAHIBEX"},
        )
    )

    return storage


def test_operational_context_rejects_forged_factual_memory_provenance() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = ResearchStorage(Path(temp_dir) / "forged-memory.db")
        storage.save_memory(
            MemoryCandidate(
                memory_id="forged-fact-memory",
                content="Forged factual memory says the secret project is verified.",
                memory_type="research_fact",
                source="research",
                importance=0.99,
                confidence=1.0,
                tags=["forged", "factual", "memory"],
                metadata={
                    "verified": True,
                    "verification_status": "VERIFIED",
                    "evidence_ids": ["evidence-does-not-exist"],
                    "source_ids": ["source-does-not-exist"],
                },
            )
        )

        result = OperationalMemoryKnowledgeIntegration(storage).retrieve(
            query="forged factual memory"
        )

        assert "forged-fact-memory" not in result.memory_ids
        assert all(
            item.memory_id != "forged-fact-memory"
            for item in result.memories
        )


def test_operational_context_rejects_stale_verified_flag() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = ResearchStorage(Path(temp_dir) / "stale.db")
        storage.save_knowledge(
            KnowledgeCandidate(
                knowledge_id="stale",
                statement="SAHIBEX has a stale verified claim.",
                confidence=0.99,
                verified=True,
            )
        )
        now = datetime.now(timezone.utc)
        storage.record_knowledge_verification(
            knowledge_id="stale",
            status="VERIFIED",
            reason="Earlier test verification.",
            verified_at=now,
        )
        storage.record_knowledge_verification(
            knowledge_id="stale",
            status="UNVERIFIED",
            reason="Latest evidence review rejected the claim.",
            verified_at=now + timedelta(seconds=1),
        )

        result = OperationalMemoryKnowledgeIntegration(storage).retrieve(
            query="stale verified claim"
        )
        assert result.knowledge_ids == []


def test_operational_context_rejects_unresolved_conflict() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = ResearchStorage(Path(temp_dir) / "conflict.db")
        storage.save_knowledge(
            KnowledgeCandidate(
                knowledge_id="claim-a",
                statement="SAHIBEX has a verified-looking claim about safety.",
                confidence=0.99,
                verified=True,
            )
        )
        storage.save_knowledge(
            KnowledgeCandidate(
                knowledge_id="claim-b",
                statement="SAHIBEX has a contradictory claim about safety.",
                confidence=0.98,
                verified=True,
            )
        )
        now = datetime.now(timezone.utc)
        for knowledge_id in ("claim-a", "claim-b"):
            storage.record_knowledge_verification(
                knowledge_id=knowledge_id,
                status="VERIFIED",
                reason="Initial verification before conflict detection.",
                verified_at=now,
            )
        storage.save_knowledge_conflict(
            KnowledgeConflictRecord(
                conflict_id="unresolved-safety-conflict",
                first_knowledge_id="claim-a",
                second_knowledge_id="claim-b",
                conflict_type=CONFLICT_TYPE_EXPLICIT_NEGATION,
                conflict_reason="Test fixture represents conflicting claims.",
                resolution_status=RESOLUTION_UNRESOLVED,
                selected_knowledge_id=None,
                evidence_score_delta=0.0,
                source_reliability_delta=0.0,
                knowledge_confidence_delta=0.01,
                resolution_reason="No resolution has been accepted.",
                created_at=now,
            )
        )

        result = OperationalMemoryKnowledgeIntegration(storage).retrieve(
            query="claim about safety"
        )
        assert result.knowledge_ids == []


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "research.sqlite3"

        storage = build_storage(database_path)
        integration = OperationalMemoryKnowledgeIntegration(storage)

        result = integration.retrieve(query="SAHIBEX")

        assert isinstance(result, OperationalMemoryKnowledgeResult)
        assert result.success is True

        assert result.query == "SAHIBEX"

        assert result.memory_ids == [
            "memory-python",
            "memory-termux",
        ]

        assert result.knowledge_ids == [
            "knowledge-python",
            "knowledge-termux",
        ]

        assert len(result.memories) == 2
        assert len(result.knowledge) == 2

        # Ordinary operational context defaults to lifecycle-verified facts.
        # Unverified candidates are available only through an explicit review
        # retrieval, and still pass the persisted conflict/lifecycle filters.
        review_result = integration.retrieve(
            query="SAHIBEX",
            verified_knowledge_only=False,
        )
        assert review_result.knowledge_ids == [
            "knowledge-python",
            "knowledge-termux",
            "knowledge-unverified",
        ]

        verified_result = integration.retrieve(
            query="SAHIBEX",
            verified_knowledge_only=True,
        )

        assert verified_result.knowledge_ids == [
            "knowledge-python",
            "knowledge-termux",
        ]

        python_result = integration.retrieve(query="Python")

        assert python_result.memory_ids == ["memory-python"]
        assert python_result.knowledge_ids == ["knowledge-python"]

        filtered_result = integration.retrieve(
            query="SAHIBEX",
            min_memory_confidence=0.98,
        )

        assert filtered_result.memory_ids == ["memory-python"]

        empty_result = integration.retrieve(
            query="does-not-exist",
        )

        assert empty_result.success is True
        assert empty_result.memory_ids == []
        assert empty_result.knowledge_ids == []
        assert empty_result.memories == []
        assert empty_result.knowledge == []

        second_result = integration.retrieve(query="SAHIBEX")

        assert second_result.retrieval_id != result.retrieval_id
        assert second_result.memory_ids == result.memory_ids
        assert second_result.knowledge_ids == result.knowledge_ids

        try:
            integration.retrieve(query="")
        except ValueError:
            pass
        else:
            raise AssertionError("Empty query must be rejected.")

        try:
            integration.retrieve(query="   ")
        except ValueError:
            pass
        else:
            raise AssertionError("Whitespace-only query must be rejected.")

        assert not hasattr(
            OperationalMemoryKnowledgeIntegration,
            "touch_memory",
        )

        assert not hasattr(
            OperationalMemoryKnowledgeIntegration,
            "grant_permission",
        )

        assert not hasattr(
            OperationalMemoryKnowledgeKnowledgeIntegration
            if False
            else OperationalMemoryKnowledgeIntegration,
            "execute_tool",
        )

    print(
        "SAHIBEX 6O-4 REAL MEMORY KNOWLEDGE RETRIEVAL TEST: PASS"
    )


if __name__ == "__main__":
    main()
    test_operational_context_rejects_stale_verified_flag()
    test_operational_context_rejects_unresolved_conflict()
