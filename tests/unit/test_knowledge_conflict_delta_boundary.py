from __future__ import annotations

from core.research.conflict import ResearchConflictDetector
from core.research.conflict_intelligence import ResearchConflictIntelligence
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)


def test_delta_boundary():
    first = KnowledgeCandidate(
        knowledge_id="knowledge-a",
        statement="The system is online.",
        confidence=0.80,
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

    assessment = result.assessments[0]

    print(
        "[INFO] no-evidence evidence_score_delta="
        f"{assessment.evidence_score_delta}"
    )
    print(
        "[INFO] no-source source_reliability_delta="
        f"{assessment.source_reliability_delta}"
    )
    print(
        "[INFO] confidence_delta="
        f"{assessment.knowledge_confidence_delta}"
    )

    assert -1.0 <= assessment.evidence_score_delta <= 1.0
    assert -1.0 <= assessment.source_reliability_delta <= 1.0
    assert -1.0 <= assessment.knowledge_confidence_delta <= 1.0


def run():
    print("SAHIBEX 6H-7D KNOWLEDGE CONFLICT DELTA BOUNDARY TEST")

    test_delta_boundary()

    print("[PASS] conflict delta boundaries")
    print(
        "SAHIBEX 6H-7D KNOWLEDGE CONFLICT DELTA BOUNDARY TEST: PASS"
    )


if __name__ == "__main__":
    run()
