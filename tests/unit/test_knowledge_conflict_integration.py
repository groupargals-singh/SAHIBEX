from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.conflict_intelligence import (
    ResearchConflictIntelligence,
)
from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


def build_knowledge():
    first = KnowledgeCandidate(
        knowledge_id="knowledge-a",
        statement="The system is online.",
        confidence=0.90,
    )

    second = KnowledgeCandidate(
        knowledge_id="knowledge-b",
        statement="The system is not online.",
        confidence=0.60,
    )

    third = KnowledgeCandidate(
        knowledge_id="knowledge-c",
        statement="The system uses Python.",
        confidence=0.95,
    )

    return first, second, third


def test_conflict_history_is_part_of_knowledge_context():
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"

        first, second, third = build_knowledge()

        intelligence = ResearchConflictIntelligence()

        result = intelligence.analyze(
            knowledge_items=[
                first,
                second,
                third,
            ],
        )

        assert result.total_conflicts == 1
        assert len(result.assessments) == 1

        storage = ResearchStorage(database_path)

        storage.save_knowledge(first)
        storage.save_knowledge(second)
        storage.save_knowledge(third)

        storage.save_conflict_assessment(
            result.assessments[0]
        )

        context = storage.knowledge_conflict_context(
            "knowledge-a"
        )

        assert context["knowledge_id"] == "knowledge-a"

        assert context["conflict_count"] == 1

        assert context["resolved_conflict_count"] == 1

        assert context["unresolved_conflict_count"] == 0

        assert len(context["conflicts"]) == 1

        conflict = context["conflicts"][0]

        assert conflict.first_knowledge_id == "knowledge-a"
        assert conflict.second_knowledge_id == "knowledge-b"

        assert (
            conflict.selected_knowledge_id
            == "knowledge-a"
        )

        storage.close()


def test_unresolved_conflict_context():
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"

        first = KnowledgeCandidate(
            knowledge_id="knowledge-a",
            statement="The system is online.",
            confidence=0.70,
        )

        second = KnowledgeCandidate(
            knowledge_id="knowledge-b",
            statement="The system is not online.",
            confidence=0.70,
        )

        intelligence = ResearchConflictIntelligence()

        result = intelligence.analyze(
            knowledge_items=[first, second],
        )

        assert result.total_conflicts == 1
        assert result.unresolved_count == 1

        storage = ResearchStorage(database_path)

        storage.save_knowledge(first)
        storage.save_knowledge(second)

        storage.save_conflict_assessment(
            result.assessments[0]
        )

        context = storage.knowledge_conflict_context(
            "knowledge-a"
        )

        assert context["conflict_count"] == 1
        assert context["resolved_conflict_count"] == 0
        assert context["unresolved_conflict_count"] == 1

        conflict = context["conflicts"][0]

        assert conflict.resolution_status == "UNRESOLVED"
        assert conflict.selected_knowledge_id is None

        storage.close()


def test_non_conflicting_knowledge_context():
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"

        knowledge = KnowledgeCandidate(
            knowledge_id="knowledge-a",
            statement="The system uses Python.",
            confidence=0.95,
        )

        storage = ResearchStorage(database_path)

        storage.save_knowledge(knowledge)

        context = storage.knowledge_conflict_context(
            "knowledge-a"
        )

        assert context["knowledge_id"] == "knowledge-a"
        assert context["conflict_count"] == 0
        assert context["resolved_conflict_count"] == 0
        assert context["unresolved_conflict_count"] == 0
        assert context["conflicts"] == []

        storage.close()


def test_unknown_knowledge_protection():
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"

        storage = ResearchStorage(database_path)

        try:
            storage.knowledge_conflict_context("")
        except ValueError:
            pass
        else:
            raise AssertionError(
                "empty knowledge ID must be rejected"
            )

        context = storage.knowledge_conflict_context(
            "unknown-knowledge"
        )

        assert context["knowledge_id"] == "unknown-knowledge"
        assert context["conflict_count"] == 0
        assert context["resolved_conflict_count"] == 0
        assert context["unresolved_conflict_count"] == 0
        assert context["conflicts"] == []

        storage.close()


def test_conflict_context_survives_restart():
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"

        first, second, _ = build_knowledge()

        intelligence = ResearchConflictIntelligence()

        result = intelligence.analyze(
            knowledge_items=[first, second],
        )

        storage = ResearchStorage(database_path)

        storage.save_knowledge(first)
        storage.save_knowledge(second)

        storage.save_conflict_assessment(
            result.assessments[0]
        )

        storage.close()

        storage = ResearchStorage(database_path)

        context = storage.knowledge_conflict_context(
            "knowledge-a"
        )

        assert context["conflict_count"] == 1
        assert context["resolved_conflict_count"] == 1
        assert context["unresolved_conflict_count"] == 0

        storage.close()


def run():
    print(
        "SAHIBEX 6H-7F KNOWLEDGE CONFLICT "
        "INTEGRATION TEST"
    )

    test_conflict_history_is_part_of_knowledge_context()
    print("[PASS] resolved conflict knowledge context")

    test_unresolved_conflict_context()
    print("[PASS] unresolved conflict knowledge context")

    test_non_conflicting_knowledge_context()
    print("[PASS] non-conflicting knowledge context")

    test_unknown_knowledge_protection()
    print("[PASS] unknown knowledge protection")

    test_conflict_context_survives_restart()
    print("[PASS] conflict context survives restart")

    print(
        "SAHIBEX 6H-7F KNOWLEDGE CONFLICT "
        "INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    run()
