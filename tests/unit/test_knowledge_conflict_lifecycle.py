from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.conflict_intelligence import (
    ResearchConflictIntelligence,
)
from core.research.knowledge_conflict import (
    RESOLUTION_RESOLVED,
    RESOLUTION_UNRESOLVED,
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


def test_resolved_conflict_lifecycle() -> None:
    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "conflict_lifecycle.db"

        first = _knowledge(
            "knowledge-a",
            "The system is online.",
            0.90,
        )

        second = _knowledge(
            "knowledge-b",
            "The system is not online.",
            0.60,
        )

        intelligence = ResearchConflictIntelligence()

        result = intelligence.analyze(
            [first, second]
        )

        assert result.total_conflicts == 1
        assert result.resolved_count == 1
        assert result.unresolved_count == 0
        assert result.status == "ALL_RESOLVED"

        assessment = result.assessments[0]

        assert (
            assessment.first_knowledge_id
            == "knowledge-a"
        )
        assert (
            assessment.second_knowledge_id
            == "knowledge-b"
        )
        assert (
            assessment.resolution_status
            == RESOLUTION_RESOLVED
        )
        assert (
            assessment.selected_knowledge_id
            == "knowledge-a"
        )

        with ResearchStorage(database_path) as storage:
            storage.save_knowledge(first)
            storage.save_knowledge(second)

            storage.save_conflict_assessment(
                assessment
            )

            loaded = storage.get_conflict_assessment(
                "knowledge-a",
                "knowledge-b",
            )

            assert loaded is not None

            assert (
                loaded.first_knowledge_id
                == assessment.first_knowledge_id
            )

            assert (
                loaded.second_knowledge_id
                == assessment.second_knowledge_id
            )

            assert (
                loaded.conflict_type
                == assessment.conflict_type
            )

            assert (
                loaded.resolution_status
                == assessment.resolution_status
            )

            assert (
                loaded.selected_knowledge_id
                == assessment.selected_knowledge_id
            )

            assert (
                loaded.resolution_reason
                == assessment.resolution_reason
            )

            assert (
                storage.conflict_assessment_count()
                == 1
            )

            assert (
                storage.get_knowledge("knowledge-a")
                == first
            )

            assert (
                storage.get_knowledge("knowledge-b")
                == second
            )


def test_unresolved_conflict_is_preserved() -> None:
    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "conflict_lifecycle.db"

        first = _knowledge(
            "knowledge-a",
            "The system is online.",
            0.70,
        )

        second = _knowledge(
            "knowledge-b",
            "The system is not online.",
            0.70,
        )

        intelligence = ResearchConflictIntelligence()

        result = intelligence.analyze(
            [first, second]
        )

        assert result.total_conflicts == 1
        assert result.resolved_count == 0
        assert result.unresolved_count == 1
        assert result.status == "UNRESOLVED"

        assessment = result.assessments[0]

        assert (
            assessment.resolution_status
            == RESOLUTION_UNRESOLVED
        )
        assert assessment.selected_knowledge_id is None

        with ResearchStorage(database_path) as storage:
            storage.save_conflict_assessment(
                assessment
            )

            loaded = storage.get_conflict_assessment(
                "knowledge-a",
                "knowledge-b",
            )

            assert loaded is not None
            assert (
                loaded.resolution_status
                == RESOLUTION_UNRESOLVED
            )
            assert loaded.selected_knowledge_id is None
            assert (
                storage.conflict_assessment_count()
                == 1
            )


def test_lifecycle_survives_restart() -> None:
    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "conflict_lifecycle.db"

        first = _knowledge(
            "knowledge-a",
            "The system is online.",
            0.80,
        )

        second = _knowledge(
            "knowledge-b",
            "The system is not online.",
            0.50,
        )

        intelligence = ResearchConflictIntelligence()

        result = intelligence.analyze(
            [first, second]
        )

        assessment = result.assessments[0]

        storage = ResearchStorage(database_path)
        storage.save_conflict_assessment(
            assessment
        )
        storage.close()

        restarted = ResearchStorage(database_path)

        loaded = restarted.get_conflict_assessment(
            "knowledge-a",
            "knowledge-b",
        )

        assert loaded is not None
        assert (
            loaded.resolution_status
            == assessment.resolution_status
        )
        assert (
            loaded.selected_knowledge_id
            == assessment.selected_knowledge_id
        )

        assert (
            restarted.conflict_assessment_count()
            == 1
        )

        restarted.close()


def test_non_conflicting_knowledge_creates_no_record() -> None:
    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "conflict_lifecycle.db"

        first = _knowledge(
            "knowledge-a",
            "The system is online.",
            0.80,
        )

        second = _knowledge(
            "knowledge-b",
            "The system uses Python.",
            0.80,
        )

        intelligence = ResearchConflictIntelligence()

        result = intelligence.analyze(
            [first, second]
        )

        assert result.total_conflicts == 0
        assert result.assessments == []

        with ResearchStorage(database_path) as storage:
            assert (
                storage.conflict_assessment_count()
                == 0
            )


def run() -> None:
    print(
        "SAHIBEX 6H-7C KNOWLEDGE CONFLICT "
        "LIFECYCLE TEST"
    )

    tests = [
        (
            "resolved conflict lifecycle",
            test_resolved_conflict_lifecycle,
        ),
        (
            "unresolved conflict preservation",
            test_unresolved_conflict_is_preserved,
        ),
        (
            "lifecycle survives restart",
            test_lifecycle_survives_restart,
        ),
        (
            "non-conflicting knowledge creates no record",
            test_non_conflicting_knowledge_creates_no_record,
        ),
    ]

    for name, test in tests:
        test()
        print(f"[PASS] {name}")

    print(
        "SAHIBEX 6H-7C KNOWLEDGE CONFLICT "
        "LIFECYCLE TEST: PASS"
    )


if __name__ == "__main__":
    run()
