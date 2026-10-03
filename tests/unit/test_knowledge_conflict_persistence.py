from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.knowledge_conflict import (
    CONFLICT_TYPE_EXPLICIT_NEGATION,
    RESOLUTION_RESOLVED,
    RESOLUTION_UNRESOLVED,
    KnowledgeConflictRecord,
)
from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


def _knowledge(
    knowledge_id: str,
    statement: str,
    confidence: float,
) -> KnowledgeCandidate:
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        confidence=confidence,
    )


def test_resolved_conflict_persistence() -> None:
    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "knowledge_conflict.db"

        storage = ResearchStorage(database_path)

        first = _knowledge(
            "knowledge-first",
            "The system is online.",
            0.80,
        )

        second = _knowledge(
            "knowledge-second",
            "The system is not online.",
            0.60,
        )

        storage.save_knowledge(first)
        storage.save_knowledge(second)

        created_at = datetime.now(timezone.utc)

        record = KnowledgeConflictRecord(
            conflict_id="conflict-001",
            first_knowledge_id=first.knowledge_id,
            second_knowledge_id=second.knowledge_id,
            conflict_type=CONFLICT_TYPE_EXPLICIT_NEGATION,
            conflict_reason=(
                "same statement with opposite explicit negation"
            ),
            resolution_status=RESOLUTION_RESOLVED,
            selected_knowledge_id=first.knowledge_id,
            evidence_score_delta=0.20,
            source_reliability_delta=0.10,
            knowledge_confidence_delta=0.20,
            resolution_reason="stronger supporting evidence",
            created_at=created_at,
            metadata={"test": True},
        )

        storage.save_knowledge_conflict(record)

        loaded = storage.get_knowledge_conflict(
            "conflict-001"
        )

        assert loaded is not None
        assert loaded.conflict_id == "conflict-001"
        assert (
            loaded.first_knowledge_id
            == "knowledge-first"
        )
        assert (
            loaded.second_knowledge_id
            == "knowledge-second"
        )
        assert (
            loaded.conflict_type
            == CONFLICT_TYPE_EXPLICIT_NEGATION
        )
        assert (
            loaded.resolution_status
            == RESOLUTION_RESOLVED
        )
        assert (
            loaded.selected_knowledge_id
            == "knowledge-first"
        )
        assert loaded.evidence_score_delta == 0.20
        assert loaded.source_reliability_delta == 0.10
        assert loaded.knowledge_confidence_delta == 0.20
        assert (
            loaded.resolution_reason
            == "stronger supporting evidence"
        )
        assert loaded.created_at == created_at
        assert loaded.metadata == {"test": True}

        assert storage.knowledge_conflict_count() == 1

        assert storage.get_knowledge(
            "knowledge-first"
        ) == first

        assert storage.get_knowledge(
            "knowledge-second"
        ) == second

        storage.close()


def test_unresolved_conflict_persistence() -> None:
    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "knowledge_conflict.db"

        storage = ResearchStorage(database_path)

        record = KnowledgeConflictRecord(
            conflict_id="conflict-002",
            first_knowledge_id="knowledge-a",
            second_knowledge_id="knowledge-b",
            conflict_type=CONFLICT_TYPE_EXPLICIT_NEGATION,
            conflict_reason=(
                "same statement with opposite explicit negation"
            ),
            resolution_status=RESOLUTION_UNRESOLVED,
            selected_knowledge_id=None,
            evidence_score_delta=0.0,
            source_reliability_delta=0.0,
            knowledge_confidence_delta=0.0,
            resolution_reason="insufficient evidence",
            metadata={"requires_review": True},
        )

        storage.save_knowledge_conflict(record)

        loaded = storage.get_knowledge_conflict(
            "conflict-002"
        )

        assert loaded is not None
        assert (
            loaded.resolution_status
            == RESOLUTION_UNRESOLVED
        )
        assert loaded.selected_knowledge_id is None
        assert loaded.metadata == {
            "requires_review": True
        }

        assert storage.knowledge_conflict_count() == 1

        storage.close()


def test_conflict_persistence_survives_restart() -> None:
    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "knowledge_conflict.db"

        record = KnowledgeConflictRecord(
            conflict_id="conflict-003",
            first_knowledge_id="knowledge-x",
            second_knowledge_id="knowledge-y",
            conflict_type=CONFLICT_TYPE_EXPLICIT_NEGATION,
            conflict_reason=(
                "same statement with opposite explicit negation"
            ),
            resolution_status=RESOLUTION_RESOLVED,
            selected_knowledge_id="knowledge-y",
            evidence_score_delta=-0.10,
            source_reliability_delta=0.30,
            knowledge_confidence_delta=0.05,
            resolution_reason="higher source reliability",
            created_at=datetime.now(timezone.utc),
            metadata={"restart_test": True},
        )

        storage = ResearchStorage(database_path)
        storage.save_knowledge_conflict(record)

        assert storage.knowledge_conflict_count() == 1

        storage.close()

        restarted = ResearchStorage(database_path)

        loaded = restarted.get_knowledge_conflict(
            "conflict-003"
        )

        assert loaded is not None
        assert loaded.conflict_id == "conflict-003"
        assert (
            loaded.selected_knowledge_id
            == "knowledge-y"
        )
        assert (
            loaded.resolution_reason
            == "higher source reliability"
        )
        assert loaded.metadata == {
            "restart_test": True
        }

        assert restarted.knowledge_conflict_count() == 1

        restarted.close()


def test_empty_conflict_id_protection() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = ResearchStorage(
            Path(temp_dir) / "knowledge_conflict.db"
        )

        try:
            storage.get_knowledge_conflict("")
        except ValueError:
            pass
        else:
            raise AssertionError(
                "empty conflict ID must be rejected"
            )

        storage.close()


def test_unknown_conflict_returns_none() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = ResearchStorage(
            Path(temp_dir) / "knowledge_conflict.db"
        )

        assert (
            storage.get_knowledge_conflict(
                "does-not-exist"
            )
            is None
        )

        storage.close()


def run() -> None:
    print(
        "SAHIBEX 6H-7B KNOWLEDGE CONFLICT "
        "PERSISTENCE TEST"
    )

    tests = [
        (
            "resolved conflict persistence",
            test_resolved_conflict_persistence,
        ),
        (
            "unresolved conflict persistence",
            test_unresolved_conflict_persistence,
        ),
        (
            "conflict persistence survives restart",
            test_conflict_persistence_survives_restart,
        ),
        (
            "empty conflict ID protection",
            test_empty_conflict_id_protection,
        ),
        (
            "unknown conflict returns none",
            test_unknown_conflict_returns_none,
        ),
    ]

    for name, test in tests:
        test()
        print(f"[PASS] {name}")

    print(
        "SAHIBEX 6H-7B KNOWLEDGE CONFLICT "
        "PERSISTENCE TEST: PASS"
    )


if __name__ == "__main__":
    run()
