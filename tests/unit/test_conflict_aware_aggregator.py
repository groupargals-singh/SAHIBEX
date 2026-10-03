from core.research.aggregator import ResearchResultAggregator
from core.research.models import KnowledgeCandidate


def make_knowledge(
    knowledge_id,
    statement,
    confidence=0.8,
    verified=True,
):
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        findings=[],
        evidence=[],
        confidence=confidence,
        verified=verified,
    )


def get_ids(result):
    return [item.knowledge_id for item in result.results]


def main():
    print("SAHIBEX CONFLICT-AWARE AGGREGATOR TEST")

    aggregator = ResearchResultAggregator()

    # =========================================================
    # 1. Conflict detection integrated
    # =========================================================
    k1 = make_knowledge(
        "k1",
        "The system is enabled.",
        confidence=0.80,
        verified=True,
    )

    k2 = make_knowledge(
        "k2",
        "The system is disabled.",
        confidence=0.70,
        verified=True,
    )

    result = aggregator.aggregate(
        [k1, k2],
        verified_only=True,
        limit=10,
    )

    assert result.conflict_count == 1
    assert set(result.conflict_ids) == {"k1", "k2"}

    print("[PASS] conflict detection integrated")

    # =========================================================
    # 2. Conflict resolution integrated
    # =========================================================
    result_ids = get_ids(result)

    assert len(result_ids) == 1
    assert result_ids[0] in {"k1", "k2"}

    assert result.resolved_conflict_count == 1
    assert result.unresolved_conflict_count == 0

    print("[PASS] conflict resolution integrated")

    # =========================================================
    # 3. Conflict metadata preserved
    # =========================================================
    assert result.conflict_count == 1
    assert "k1" in result.conflict_ids
    assert "k2" in result.conflict_ids

    print("[PASS] conflict metadata preserved")

    # =========================================================
    # 4. Resolved knowledge metadata preserved
    # =========================================================
    assert len(result.resolved_knowledge_ids) == 1
    assert result.resolved_knowledge_ids[0] in {"k1", "k2"}

    print("[PASS] resolved knowledge metadata preserved")

    # =========================================================
    # 5. Normal aggregation preserved
    # =========================================================
    normal_1 = make_knowledge(
        "normal1",
        "Python is a programming language.",
        confidence=0.90,
        verified=True,
    )

    normal_2 = make_knowledge(
        "normal2",
        "SQLite is a database engine.",
        confidence=0.85,
        verified=True,
    )

    normal_result = aggregator.aggregate(
        [normal_1, normal_2],
        verified_only=True,
        limit=10,
    )

    normal_ids = get_ids(normal_result)

    assert normal_ids == ["normal1", "normal2"]
    assert normal_result.conflict_count == 0
    assert normal_result.resolved_conflict_count == 0
    assert normal_result.unresolved_conflict_count == 0

    print("[PASS] normal aggregation preserved")

    # =========================================================
    # 6. Duplicate protection
    # =========================================================
    duplicate_result = aggregator.aggregate(
        [
            normal_1,
            normal_1,
            normal_2,
            normal_2,
        ],
        verified_only=True,
        limit=10,
    )

    duplicate_ids = get_ids(duplicate_result)

    assert len(duplicate_ids) == 2
    assert len(duplicate_ids) == len(set(duplicate_ids))
    assert set(duplicate_ids) == {"normal1", "normal2"}

    print("[PASS] duplicate protection preserved")

    # =========================================================
    # 7. Verified-only filtering
    # =========================================================
    verified = make_knowledge(
        "verified",
        "Python is widely used for software development.",
        confidence=0.90,
        verified=True,
    )

    unverified = make_knowledge(
        "unverified",
        "SQLite is commonly used as a lightweight database.",
        confidence=0.95,
        verified=False,
    )

    verified_result = aggregator.aggregate(
        [verified, unverified],
        verified_only=True,
        limit=10,
    )

    verified_ids = get_ids(verified_result)

    assert "verified" in verified_ids
    assert "unverified" not in verified_ids

    for item in verified_result.results:
        assert item.verified is True

    print("[PASS] verified-only filtering preserved")

    # =========================================================
    # 8. Explicit unverified aggregation
    # =========================================================
    all_result = aggregator.aggregate(
        [verified, unverified],
        verified_only=False,
        limit=10,
    )

    all_ids = get_ids(all_result)

    assert "verified" in all_ids
    assert "unverified" in all_ids

    print("[PASS] explicit unverified aggregation preserved")

    # =========================================================
    # 9. Result limit
    # =========================================================
    limit_items = [
        make_knowledge(
            "limit1",
            "Statement one.",
            confidence=0.90,
            verified=True,
        ),
        make_knowledge(
            "limit2",
            "Statement two.",
            confidence=0.80,
            verified=True,
        ),
        make_knowledge(
            "limit3",
            "Statement three.",
            confidence=0.70,
            verified=True,
        ),
    ]

    limit_result = aggregator.aggregate(
        limit_items,
        verified_only=True,
        limit=2,
    )

    assert len(limit_result.results) == 2

    print("[PASS] result limit preserved")

    # =========================================================
    # 10. Empty aggregation
    # =========================================================
    empty_result = aggregator.aggregate(
        [],
        verified_only=True,
        limit=10,
    )

    assert empty_result.results == []
    assert empty_result.total_candidates == 0
    assert empty_result.conflict_count == 0
    assert empty_result.resolved_conflict_count == 0
    assert empty_result.unresolved_conflict_count == 0

    print("[PASS] empty aggregation handling")

    # =========================================================
    # 11. Invalid limit protection
    # =========================================================
    try:
        aggregator.aggregate(
            [normal_1],
            verified_only=True,
            limit=0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "limit=0 should raise ValueError"
        )

    print("[PASS] invalid limit protection")

    print("SAHIBEX CONFLICT-AWARE AGGREGATOR TEST: PASS")


if __name__ == "__main__":
    main()
