from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.conflict_intelligence import (
    ResearchConflictIntelligence,
)
from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


def build_resolved_conflict():
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

    intelligence = ResearchConflictIntelligence()

    result = intelligence.analyze(
        knowledge_items=[first, second],
    )

    assert result.total_conflicts == 1
    assert result.resolved_count == 1

    return first, second, result.assessments[0]


def build_unresolved_conflict():
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

    return first, second, result.assessments[0]


def test_resolved_conflict_verification_context():
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"

        first, second, assessment = build_resolved_conflict()

        storage = ResearchStorage(database_path)

        storage.save_knowledge(first)
        storage.save_knowledge(second)
        storage.save_conflict_assessment(assessment)

        verification_context = (
            storage.knowledge_verification_context(
                "knowledge-a"
            )
        )

        assert (
            verification_context["knowledge_id"]
            == "knowledge-a"
        )

        assert (
            verification_context["conflict_count"]
            == 1
        )

        assert (
            verification_context[
                "unresolved_conflict_count"
            ]
            == 0
        )

        assert (
            verification_context[
                "resolved_conflict_count"
            ]
            == 1
        )

        assert (
            verification_context[
                "conflict_status"
            ]
            == "RESOLVED"
        )

        assert (
            verification_context[
                "selected_knowledge_id"
            ]
            == "knowledge-a"
        )

        storage.close()


def test_unresolved_conflict_verification_context():
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"

        first, second, assessment = (
            build_unresolved_conflict()
        )

        storage = ResearchStorage(database_path)

        storage.save_knowledge(first)
        storage.save_knowledge(second)
        storage.save_conflict_assessment(assessment)

        verification_context = (
            storage.knowledge_verification_context(
                "knowledge-a"
            )
        )

        assert (
            verification_context["conflict_count"]
            == 1
        )

        assert (
            verification_context[
                "resolved_conflict_count"
            ]
            == 0
        )

        assert (
            verification_context[
                "unresolved_conflict_count"
            ]
            == 1
        )

        assert (
            verification_context[
                "conflict_status"
            ]
            == "UNRESOLVED"
        )

        assert (
            verification_context[
                "selected_knowledge_id"
            ]
            is None
        )

        storage.close()


def test_no_conflict_verification_context():
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"

        knowledge = KnowledgeCandidate(
            knowledge_id="knowledge-a",
            statement="The system uses Python.",
            confidence=0.95,
        )

        storage = ResearchStorage(database_path)

        storage.save_knowledge(knowledge)

        verification_context = (
            storage.knowledge_verification_context(
                "knowledge-a"
            )
        )

        assert (
            verification_context["knowledge_id"]
            == "knowledge-a"
        )

        assert (
            verification_context["conflict_count"]
            == 0
        )

        assert (
            verification_context[
                "resolved_conflict_count"
            ]
            == 0
        )

        assert (
            verification_context[
                "unresolved_conflict_count"
            ]
            == 0
        )

        assert (
            verification_context["conflict_status"]
            == "NO_CONFLICT"
        )

        assert (
            verification_context[
                "selected_knowledge_id"
            ]
            is None
        )

        storage.close()


def test_verification_context_survives_restart():
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"

        first, second, assessment = (
            build_resolved_conflict()
        )

        storage = ResearchStorage(database_path)

        storage.save_knowledge(first)
        storage.save_knowledge(second)
        storage.save_conflict_assessment(assessment)

        storage.close()

        storage = ResearchStorage(database_path)

        context = (
            storage.knowledge_verification_context(
                "knowledge-a"
            )
        )

        assert context["conflict_count"] == 1
        assert (
            context["conflict_status"]
            == "RESOLVED"
        )
        assert (
            context["selected_knowledge_id"]
            == "knowledge-a"
        )

        storage.close()


def test_empty_knowledge_protection():
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"

        storage = ResearchStorage(database_path)

        try:
            storage.knowledge_verification_context("")
        except ValueError:
            pass
        else:
            raise AssertionError(
                "empty knowledge ID must be rejected"
            )

        storage.close()


def run():
    print(
        "SAHIBEX 6H-7G KNOWLEDGE CONFLICT "
        "VERIFICATION TEST"
    )

    test_resolved_conflict_verification_context()
    print(
        "[PASS] resolved conflict verification context"
    )

    test_unresolved_conflict_verification_context()
    print(
        "[PASS] unresolved conflict verification context"
    )

    test_no_conflict_verification_context()
    print(
        "[PASS] no-conflict verification context"
    )

    test_verification_context_survives_restart()
    print(
        "[PASS] verification context survives restart"
    )

    test_empty_knowledge_protection()
    print(
        "[PASS] empty knowledge protection"
    )

    print(
        "SAHIBEX 6H-7G KNOWLEDGE CONFLICT "
        "VERIFICATION TEST: PASS"
    )


if __name__ == "__main__":
    run()
