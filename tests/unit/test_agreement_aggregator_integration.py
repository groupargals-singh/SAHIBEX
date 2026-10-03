from datetime import datetime, timezone

from core.research.aggregator import (
    ResearchResultAggregator,
)
from core.research.agreement import (
    AGREEMENT_VERSION,
)
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)


def knowledge(
    knowledge_id: str,
    statement: str,
    confidence: float = 0.90,
    verified: bool = True,
) -> KnowledgeCandidate:
    now = datetime.now(timezone.utc)

    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        findings=[],
        evidence=[],
        confidence=confidence,
        verified=verified,
        created_at=now,
        last_verified_at=now if verified else None,
        metadata={},
    )


def source(
    source_id: str,
    reliability: float = 0.80,
) -> ResearchSource:
    now = datetime.now(timezone.utc)

    return ResearchSource(
        source_id=source_id,
        title=source_id,
        source_type="test",
        locator=f"https://example.com/{source_id}",
        publisher="test",
        author=None,
        published_at=None,
        accessed_at=now,
        reliability=reliability,
        metadata={},
    )


def evidence(
    evidence_id: str,
    knowledge_id: str,
    source_id: str,
    supports: bool = True,
) -> Evidence:
    now = datetime.now(timezone.utc)

    return Evidence(
        evidence_id=evidence_id,
        finding_id=f"finding-{evidence_id}",
        source_id=source_id,
        evidence_text="the system is safe",
        supports=supports,
        strength=0.80,
        created_at=now,
        metadata={
            "knowledge_id": knowledge_id,
        },
    )


def main() -> None:
    aggregator = ResearchResultAggregator()

    safe = knowledge(
        "k1",
        "the system is safe",
    )

    # ---------------------------------------------------------
    # 1. Two independent source IDs support same knowledge
    # ---------------------------------------------------------
    result = aggregator.aggregate(
        [safe],
        evidence_items=[
            evidence(
                "e1",
                "k1",
                "source-a",
            ),
            evidence(
                "e2",
                "k1",
                "source-b",
            ),
        ],
        sources=[
            source("source-a"),
            source("source-b"),
        ],
    )

    assert len(result.agreement_assessments) == 1

    assessment = result.agreement_assessments[0]

    assert assessment.knowledge_id == "k1"
    assert assessment.total_source_count == 2
    assert assessment.supporting_source_count == 2
    assert assessment.contradicting_source_count == 0
    assert assessment.agreement_score == 1.0
    assert assessment.version == AGREEMENT_VERSION

    print("[PASS] aggregator exposes multi-source agreement")

    # ---------------------------------------------------------
    # 2. Multiple evidence records from same source count once
    # ---------------------------------------------------------
    result = aggregator.aggregate(
        [safe],
        evidence_items=[
            evidence(
                "e3",
                "k1",
                "source-a",
            ),
            evidence(
                "e4",
                "k1",
                "source-a",
            ),
        ],
        sources=[
            source("source-a"),
        ],
    )

    assessment = result.agreement_assessments[0]

    assert assessment.total_source_count == 1
    assert assessment.supporting_source_count == 1
    assert assessment.agreement_score == 0.0

    print("[PASS] same source is counted once")

    # ---------------------------------------------------------
    # 3. Contradicting source is counted separately
    # ---------------------------------------------------------
    result = aggregator.aggregate(
        [safe],
        evidence_items=[
            evidence(
                "e5",
                "k1",
                "source-a",
                supports=True,
            ),
            evidence(
                "e6",
                "k1",
                "source-b",
                supports=False,
            ),
        ],
        sources=[
            source("source-a"),
            source("source-b"),
        ],
    )

    assessment = result.agreement_assessments[0]

    assert assessment.total_source_count == 2
    assert assessment.supporting_source_count == 1
    assert assessment.contradicting_source_count == 1
    assert assessment.agreement_score == 0.0

    print("[PASS] contradiction remains visible")

    # ---------------------------------------------------------
    # 4. Agreement does not change aggregation selection
    # ---------------------------------------------------------
    result = aggregator.aggregate(
        [safe],
        evidence_items=[
            evidence(
                "e7",
                "k1",
                "source-a",
            ),
            evidence(
                "e8",
                "k1",
                "source-b",
            ),
        ],
        sources=[
            source("source-a"),
            source("source-b"),
        ],
    )

    assert len(result.results) == 1
    assert result.results[0].knowledge_id == "k1"
    assert result.results[0].verified is True

    print("[PASS] agreement does not alter aggregation behavior")

    # ---------------------------------------------------------
    # 5. Different knowledge candidates get separate
    #    agreement assessments
    # ---------------------------------------------------------
    second = knowledge(
        "k2",
        "the service is active",
        confidence=0.85,
    )

    result = aggregator.aggregate(
        [safe, second],
        verified_only=False,
        evidence_items=[
            evidence(
                "e9",
                "k1",
                "source-a",
            ),
            evidence(
                "e10",
                "k1",
                "source-b",
            ),
            evidence(
                "e11",
                "k2",
                "source-c",
            ),
        ],
        sources=[
            source("source-a"),
            source("source-b"),
            source("source-c"),
        ],
    )

    assert len(result.agreement_assessments) == 2

    assessments = {
        item.knowledge_id: item
        for item in result.agreement_assessments
    }

    assert assessments["k1"].total_source_count == 2
    assert assessments["k1"].agreement_score == 1.0

    assert assessments["k2"].total_source_count == 1
    assert assessments["k2"].agreement_score == 0.0

    print("[PASS] per-knowledge agreement separation")

    # ---------------------------------------------------------
    # 6. Existing conflict metadata remains intact
    # ---------------------------------------------------------
    unsafe = knowledge(
        "k3",
        "the system is unsafe",
    )

    result = aggregator.aggregate(
        [safe, unsafe],
        evidence_items=[
            evidence(
                "e12",
                "k1",
                "source-a",
            ),
            evidence(
                "e13",
                "k3",
                "source-b",
            ),
        ],
        sources=[
            source("source-a"),
            source("source-b"),
        ],
    )

    assert result.conflict_count == 1
    assert len(result.agreement_assessments) == 2

    print("[PASS] conflict pipeline remains intact")

    print(
        "SAHIBEX 6G-4 AGREEMENT AGGREGATOR "
        "INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
