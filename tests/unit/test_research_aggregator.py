from __future__ import annotations

from core.research.aggregator import (
    ResearchResultAggregator,
)
from core.research.models import KnowledgeCandidate


def make_knowledge(
    knowledge_id: str,
    statement: str,
    confidence: float,
    verified: bool,
) -> KnowledgeCandidate:
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        findings=[],
        evidence=[],
        confidence=confidence,
        verified=verified,
    )


def main() -> None:
    print("SAHIBEX RESEARCH AGGREGATOR TEST")

    aggregator = ResearchResultAggregator()

    knowledge = [
        make_knowledge(
            "k1",
            "SAHIBEX uses verified research.",
            0.95,
            True,
        ),
        make_knowledge(
            "k2",
            "SAHIBEX uses persistent knowledge.",
            0.85,
            True,
        ),
        make_knowledge(
            "k3",
            "This knowledge is unverified.",
            0.40,
            False,
        ),
    ]

    # ---------------------------------------------------------
    # 1. Basic aggregation
    # ---------------------------------------------------------
    result = aggregator.aggregate(
        knowledge,
        verified_only=True,
    )

    assert result.total_candidates == 3
    assert result.verified_count == 2
    assert result.unverified_count == 1
    assert len(result.results) == 2

    print("[PASS] basic aggregation")

    # ---------------------------------------------------------
    # 2. Verified-only protection
    # ---------------------------------------------------------
    assert all(
        item.verified
        for item in result.results
    )

    print("[PASS] verified-only filtering")

    # ---------------------------------------------------------
    # 3. Confidence ranking
    # ---------------------------------------------------------
    assert result.results[0].knowledge_id == "k1"
    assert result.results[1].knowledge_id == "k2"

    print("[PASS] confidence ranking")

    # ---------------------------------------------------------
    # 4. Overall confidence
    # ---------------------------------------------------------
    expected = (0.95 + 0.85) / 2

    assert abs(
        result.overall_confidence - expected
    ) < 0.000001

    print("[PASS] overall confidence")

    # ---------------------------------------------------------
    # 5. Explicit unverified retrieval
    # ---------------------------------------------------------
    all_result = aggregator.aggregate(
        knowledge,
        verified_only=False,
    )

    assert len(all_result.results) == 3
    assert any(
        not item.verified
        for item in all_result.results
    )

    print("[PASS] explicit unverified retrieval")

    # ---------------------------------------------------------
    # 6. Duplicate protection
    # ---------------------------------------------------------
    duplicated = knowledge + [
        make_knowledge(
            "k1",
            "Duplicate record.",
            0.10,
            False,
        )
    ]

    duplicate_result = aggregator.aggregate(
        duplicated,
        verified_only=False,
    )

    assert duplicate_result.total_candidates == 3

    print("[PASS] duplicate knowledge protection")

    # ---------------------------------------------------------
    # 7. Limit
    # ---------------------------------------------------------
    limited = aggregator.aggregate(
        knowledge,
        verified_only=False,
        limit=1,
    )

    assert len(limited.results) == 1
    assert limited.results[0].knowledge_id == "k1"

    print("[PASS] result limit")

    # ---------------------------------------------------------
    # 8. Empty result
    # ---------------------------------------------------------
    empty = aggregator.aggregate(
        [],
        verified_only=True,
    )

    assert empty.status == "NO_RESULT"
    assert empty.total_candidates == 0
    assert empty.overall_confidence == 0.0

    print("[PASS] empty result handling")

    # ---------------------------------------------------------
    # 9. Invalid limit
    # ---------------------------------------------------------
    try:
        aggregator.aggregate(
            knowledge,
            limit=0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "invalid limit was not rejected"
        )

    print("[PASS] invalid limit protection")

    print("SAHIBEX RESEARCH AGGREGATOR TEST: PASS")


if __name__ == "__main__":
    main()
