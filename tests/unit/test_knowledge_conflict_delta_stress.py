from __future__ import annotations

from datetime import datetime, timezone

from core.research.conflict_intelligence import ResearchConflictIntelligence
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)


def test_multi_evidence_and_source_deltas():
    first = KnowledgeCandidate(
        knowledge_id="knowledge-a",
        statement="The system is online.",
        confidence=0.80,
        evidence=[
            "evidence-a1",
            "evidence-a2",
            "evidence-a3",
        ],
    )

    second = KnowledgeCandidate(
        knowledge_id="knowledge-b",
        statement="The system is not online.",
        confidence=0.70,
        evidence=[
            "evidence-b1",
        ],
    )

    evidence_items = [
        Evidence(
            evidence_id="evidence-a1",
            finding_id="finding-a1",
            source_id="source-a1",
            evidence_text="The system is online.",
            supports=True,
            strength=1.0,
        ),
        Evidence(
            evidence_id="evidence-a2",
            finding_id="finding-a2",
            source_id="source-a2",
            evidence_text="The system is online.",
            supports=True,
            strength=1.0,
        ),
        Evidence(
            evidence_id="evidence-a3",
            finding_id="finding-a3",
            source_id="source-a3",
            evidence_text="The system is online.",
            supports=True,
            strength=1.0,
        ),
        Evidence(
            evidence_id="evidence-b1",
            finding_id="finding-b1",
            source_id="source-b1",
            evidence_text="The system is not online.",
            supports=True,
            strength=0.1,
        ),
    ]

    now = datetime.now(timezone.utc)

    sources = [
        ResearchSource(
            source_id="source-a1",
            title="Source A1",
            source_type="test",
            locator="test://a1",
            reliability=1.0,
            accessed_at=now,
        ),
        ResearchSource(
            source_id="source-a2",
            title="Source A2",
            source_type="test",
            locator="test://a2",
            reliability=1.0,
            accessed_at=now,
        ),
        ResearchSource(
            source_id="source-a3",
            title="Source A3",
            source_type="test",
            locator="test://a3",
            reliability=1.0,
            accessed_at=now,
        ),
        ResearchSource(
            source_id="source-b1",
            title="Source B1",
            source_type="test",
            locator="test://b1",
            reliability=0.1,
            accessed_at=now,
        ),
    ]

    intelligence = ResearchConflictIntelligence()

    result = intelligence.analyze(
        knowledge_items=[first, second],
        evidence_items=evidence_items,
        sources=sources,
    )

    assert result.total_conflicts == 1

    assessment = result.assessments[0]

    print(
        "[INFO] evidence_score_delta="
        f"{assessment.evidence_score_delta}"
    )

    print(
        "[INFO] source_reliability_delta="
        f"{assessment.source_reliability_delta}"
    )

    print(
        "[INFO] knowledge_confidence_delta="
        f"{assessment.knowledge_confidence_delta}"
    )

    print(
        "[INFO] resolution_status="
        f"{assessment.resolution_status}"
    )

    assert assessment.evidence_score_delta >= 0.0
    assert assessment.source_reliability_delta >= 0.0
    assert assessment.knowledge_confidence_delta >= 0.0


def run():
    print(
        "SAHIBEX 6H-7D KNOWLEDGE CONFLICT DELTA STRESS TEST"
    )

    test_multi_evidence_and_source_deltas()

    print("[PASS] multi-evidence delta calculation")
    print("[PASS] multi-source delta calculation")
    print("[PASS] confidence delta calculation")

    print(
        "SAHIBEX 6H-7D KNOWLEDGE CONFLICT DELTA STRESS TEST: PASS"
    )


if __name__ == "__main__":
    run()
