from core.research.answer import ResearchAnswerSynthesizer
from core.research.aggregator import (
    AggregatedKnowledge,
    ResearchAggregationResult,
)
from core.research.models import Evidence


def make_aggregation(
    results,
    *,
    status="VERIFIED",
    conflict_count=0,
    resolved_conflict_count=0,
    unresolved_conflict_count=0,
):
    verified_count = sum(
        1
        for item in results
        if item.verified
    )

    overall_confidence = (
        sum(item.confidence for item in results) / len(results)
        if results
        else 0.0
    )

    return ResearchAggregationResult(
        total_candidates=len(results),
        verified_count=verified_count,
        unverified_count=len(results) - verified_count,
        results=results,
        overall_confidence=overall_confidence,
        status=status,
        conflict_count=conflict_count,
        conflict_ids=[],
        resolved_conflict_count=resolved_conflict_count,
        unresolved_conflict_count=unresolved_conflict_count,
        resolved_knowledge_ids=[],
    )


def assert_confidence(actual, expected):
    assert abs(actual - expected) < 1e-9, (
        f"confidence mismatch: "
        f"actual={actual}, expected={expected}"
    )


def main():
    print("SAHIBEX RESEARCH ANSWER TEST")

    synthesizer = ResearchAnswerSynthesizer()

    # =========================================================
    # 1. Basic synthesis
    # =========================================================
    aggregation = make_aggregation(
        [
            AggregatedKnowledge(
                knowledge_id="k1",
                statement="Python is a programming language.",
                confidence=0.90,
                verified=True,
            ),
        ]
    )

    result = synthesizer.synthesize(
        "What is Python?",
        aggregation,
    )

    assert result.answer == (
        "Python is a programming language."
    )
    assert result.knowledge_ids == ["k1"]
    assert_confidence(result.confidence, 0.90)
    assert result.verified is True
    assert result.status == "VERIFIED"

    print("[PASS] basic answer synthesis")

    # =========================================================
    # 2. Multiple knowledge synthesis
    # =========================================================
    aggregation = make_aggregation(
        [
            AggregatedKnowledge(
                knowledge_id="k1",
                statement="Python is a programming language.",
                confidence=0.90,
                verified=True,
            ),
            AggregatedKnowledge(
                knowledge_id="k2",
                statement=(
                    "Python supports multiple programming styles."
                ),
                confidence=0.80,
                verified=True,
            ),
        ]
    )

    result = synthesizer.synthesize(
        "Tell me about Python.",
        aggregation,
    )

    assert "Python is a programming language." in result.answer
    assert (
        "Python supports multiple programming styles."
        in result.answer
    )
    assert result.knowledge_ids == ["k1", "k2"]
    assert_confidence(result.confidence, 0.85)
    assert result.verified is True
    assert result.status == "VERIFIED"

    print("[PASS] multiple knowledge synthesis")

    # =========================================================
    # 3. Evidence attachment
    # =========================================================
    evidence = Evidence(
        evidence_id="e1",
        finding_id="f1",
        source_id="source1",
        evidence_text=(
            "Official documentation describes Python as a language."
        ),
        supports=True,
        strength=0.95,
        metadata={"knowledge_id": "k1"},
    )

    result = synthesizer.synthesize(
        "What is Python?",
        aggregation,
        evidence_items=[evidence],
    )

    attached = [
        item
        for item in result.evidence
        if item.knowledge_id == "k1"
    ]

    assert len(attached) == 1
    assert attached[0].evidence_texts == [
        "Official documentation describes Python as a language."
    ]
    assert attached[0].source_ids == ["source1"]

    print("[PASS] evidence attachment")

    # =========================================================
    # 4. Unverified result
    # =========================================================
    unverified_aggregation = make_aggregation(
        [
            AggregatedKnowledge(
                knowledge_id="u1",
                statement=(
                    "This is an unverified research statement."
                ),
                confidence=0.60,
                verified=False,
            ),
        ],
        status="UNVERIFIED",
    )

    result = synthesizer.synthesize(
        "Research statement",
        unverified_aggregation,
    )

    assert result.verified is False
    assert result.status == "UNVERIFIED"
    assert_confidence(result.confidence, 0.60)

    print("[PASS] unverified answer handling")

    # =========================================================
    # 5. Resolved conflict
    # =========================================================
    resolved_aggregation = make_aggregation(
        [
            AggregatedKnowledge(
                knowledge_id="selected",
                statement="The selected claim is supported.",
                confidence=0.92,
                verified=True,
            ),
        ],
        status="CONFLICT_RESOLVED",
        conflict_count=1,
        resolved_conflict_count=1,
        unresolved_conflict_count=0,
    )

    result = synthesizer.synthesize(
        "Which claim is supported?",
        resolved_aggregation,
    )

    assert result.status == "CONFLICT_RESOLVED"
    assert result.verified is True
    assert result.knowledge_ids == ["selected"]

    print("[PASS] resolved conflict synthesis")

    # =========================================================
    # 6. Partially resolved conflict
    # =========================================================
    partial_aggregation = make_aggregation(
        [
            AggregatedKnowledge(
                knowledge_id="selected",
                statement="One supported claim.",
                confidence=0.90,
                verified=True,
            ),
            AggregatedKnowledge(
                knowledge_id="other",
                statement="Another available claim.",
                confidence=0.70,
                verified=True,
            ),
        ],
        status="PARTIALLY_RESOLVED",
        conflict_count=2,
        resolved_conflict_count=1,
        unresolved_conflict_count=1,
    )

    result = synthesizer.synthesize(
        "Research question",
        partial_aggregation,
    )

    assert result.status == "PARTIALLY_RESOLVED"
    assert result.verified is True

    print("[PASS] partially resolved handling")

    # =========================================================
    # 7. Unresolved conflict
    # =========================================================
    unresolved_aggregation = make_aggregation(
        [
            AggregatedKnowledge(
                knowledge_id="safe",
                statement="The system is safe.",
                confidence=0.80,
                verified=True,
            ),
        ],
        status="CONFLICT_UNRESOLVED",
        conflict_count=1,
        resolved_conflict_count=0,
        unresolved_conflict_count=1,
    )

    result = synthesizer.synthesize(
        "Is the system safe?",
        unresolved_aggregation,
    )

    assert result.status == "CONFLICT_UNRESOLVED"

    print("[PASS] unresolved conflict status")

    # =========================================================
    # 8. Empty result
    # =========================================================
    empty_aggregation = make_aggregation([])

    result = synthesizer.synthesize(
        "Unknown research query",
        empty_aggregation,
    )

    assert result.answer
    assert_confidence(result.confidence, 0.0)
    assert result.verified is False
    assert result.status == "NO_RESULT"
    assert result.knowledge_ids == []
    assert result.evidence == []

    print("[PASS] empty result handling")

    # =========================================================
    # 9. Empty query protection
    # =========================================================
    try:
        synthesizer.synthesize(
            "",
            aggregation,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty query should raise ValueError"
        )

    print("[PASS] empty query protection")

    print("SAHIBEX RESEARCH ANSWER TEST: PASS")


if __name__ == "__main__":
    main()
