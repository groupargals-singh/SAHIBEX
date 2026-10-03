from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.conflict_intelligence import ResearchConflictIntelligence
from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


def build_conflict(
    first_id: str,
    second_id: str,
    first_statement: str,
    second_statement: str,
    first_confidence: float = 0.80,
    second_confidence: float = 0.70,
):
    first = KnowledgeCandidate(
        knowledge_id=first_id,
        statement=first_statement,
        confidence=first_confidence,
    )

    second = KnowledgeCandidate(
        knowledge_id=second_id,
        statement=second_statement,
        confidence=second_confidence,
    )

    intelligence = ResearchConflictIntelligence()

    result = intelligence.analyze(
        knowledge_items=[first, second],
    )

    assert result.total_conflicts == 1
    assert len(result.assessments) == 1

    return result.assessments[0]


def test_conflict_history_retrieval():
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"

        storage = ResearchStorage(database_path)

        resolved = build_conflict(
            "knowledge-a",
            "knowledge-b",
            "The system is online.",
            "The system is not online.",
            0.90,
            0.60,
        )

        unresolved = build_conflict(
            "knowledge-a",
            "knowledge-c",
            "The system is online.",
            "The system is not online.",
            0.70,
            0.70,
        )

        storage.save_conflict_assessment(resolved)
        storage.save_conflict_assessment(unresolved)

        all_a = storage.conflicts_for_knowledge(
            "knowledge-a"
        )

        assert len(all_a) == 2

        conflict_ids = {
            conflict.conflict_id
            for conflict in all_a
        }

        assert (
            storage._conflict_pair_id(
                "knowledge-a",
                "knowledge-b",
            )
            in conflict_ids
        )

        assert (
            storage._conflict_pair_id(
                "knowledge-a",
                "knowledge-c",
            )
            in conflict_ids
        )

        resolved_a = storage.conflicts_for_knowledge(
            "knowledge-a",
            resolution_status="RESOLVED",
        )

        assert len(resolved_a) == 1
        assert (
            resolved_a[0].second_knowledge_id
            == "knowledge-b"
        )

        unresolved_a = storage.conflicts_for_knowledge(
            "knowledge-a",
            resolution_status="UNRESOLVED",
        )

        assert len(unresolved_a) == 1
        assert (
            unresolved_a[0].second_knowledge_id
            == "knowledge-c"
        )

        storage.close()


def test_reverse_side_retrieval():
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"

        storage = ResearchStorage(database_path)

        assessment = build_conflict(
            "knowledge-a",
            "knowledge-b",
            "The system is online.",
            "The system is not online.",
        )

        storage.save_conflict_assessment(assessment)

        reverse = storage.conflicts_for_knowledge(
            "knowledge-b"
        )

        assert len(reverse) == 1
        assert reverse[0].first_knowledge_id == "knowledge-a"
        assert reverse[0].second_knowledge_id == "knowledge-b"

        storage.close()


def test_unknown_and_invalid_knowledge_protection():
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"

        storage = ResearchStorage(database_path)

        assert (
            storage.conflicts_for_knowledge(
                "unknown-knowledge"
            )
            == []
        )

        try:
            storage.conflicts_for_knowledge("")
        except ValueError:
            pass
        else:
            raise AssertionError(
                "empty knowledge ID must be rejected"
            )

        try:
            storage.conflicts_for_knowledge(
                "knowledge-a",
                resolution_status="INVALID",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "invalid resolution status must be rejected"
            )

        storage.close()


def test_history_survives_restart():
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"

        assessment = build_conflict(
            "knowledge-a",
            "knowledge-b",
            "The system is online.",
            "The system is not online.",
            0.90,
            0.60,
        )

        storage = ResearchStorage(database_path)

        storage.save_conflict_assessment(assessment)

        storage.close()

        storage = ResearchStorage(database_path)

        history = storage.conflicts_for_knowledge(
            "knowledge-a"
        )

        assert len(history) == 1
        assert (
            history[0].conflict_id
            == storage._conflict_pair_id(
                "knowledge-a",
                "knowledge-b",
            )
        )

        assert (
            history[0].selected_knowledge_id
            == assessment.selected_knowledge_id
        )

        assert (
            storage.conflict_assessment_count()
            == 1
        )

        storage.close()


def run():
    print(
        "SAHIBEX 6H-7E KNOWLEDGE CONFLICT "
        "HISTORY TEST"
    )

    test_conflict_history_retrieval()
    print("[PASS] conflict history retrieval")

    test_reverse_side_retrieval()
    print("[PASS] reverse-side conflict retrieval")

    test_unknown_and_invalid_knowledge_protection()
    print("[PASS] unknown/invalid knowledge protection")

    test_history_survives_restart()
    print("[PASS] conflict history survives restart")

    print(
        "SAHIBEX 6H-7E KNOWLEDGE CONFLICT "
        "HISTORY TEST: PASS"
    )


if __name__ == "__main__":
    run()
