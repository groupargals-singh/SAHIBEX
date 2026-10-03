from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.conflict_intelligence import ResearchConflictIntelligence
from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


def build_assessment():
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
    assert len(result.assessments) == 1

    return result.assessments[0]


def test_delta_persistence():
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"

        assessment = build_assessment()

        storage = ResearchStorage(database_path)

        storage.save_conflict_assessment(assessment)

        stored = storage.get_conflict_assessment(
            "knowledge-a",
            "knowledge-b",
        )

        assert stored is not None

        assert (
            stored.evidence_score_delta
            == assessment.evidence_score_delta
        )

        assert (
            stored.source_reliability_delta
            == assessment.source_reliability_delta
        )

        assert (
            stored.knowledge_confidence_delta
            == assessment.knowledge_confidence_delta
        )

        assert (
            stored.resolution_status
            == assessment.resolution_status
        )

        assert (
            stored.selected_knowledge_id
            == assessment.selected_knowledge_id
        )

        assert (
            stored.conflict_type
            == assessment.conflict_type
        )

        assert (
            stored.conflict_reason
            == assessment.conflict_reason
        )

        storage.close()

        storage = ResearchStorage(database_path)

        restored = storage.get_conflict_assessment(
            "knowledge-a",
            "knowledge-b",
        )

        assert restored is not None

        assert (
            restored.evidence_score_delta
            == assessment.evidence_score_delta
        )

        assert (
            restored.source_reliability_delta
            == assessment.source_reliability_delta
        )

        assert (
            restored.knowledge_confidence_delta
            == assessment.knowledge_confidence_delta
        )

        assert (
            restored.resolution_status
            == assessment.resolution_status
        )

        assert (
            restored.selected_knowledge_id
            == assessment.selected_knowledge_id
        )

        assert storage.conflict_assessment_count() == 1

        storage.close()


def run():
    print(
        "SAHIBEX 6H-7D KNOWLEDGE CONFLICT DELTA "
        "PERSISTENCE TEST"
    )

    test_delta_persistence()

    print("[PASS] delta values persisted")
    print("[PASS] resolution metadata persisted")
    print("[PASS] delta values survive restart")
    print("[PASS] resolution survives restart")
    print("[PASS] conflict assessment count")

    print(
        "SAHIBEX 6H-7D KNOWLEDGE CONFLICT DELTA "
        "PERSISTENCE TEST: PASS"
    )


if __name__ == "__main__":
    run()
