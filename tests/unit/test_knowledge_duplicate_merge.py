from core.research.knowledge_merge import (
    KnowledgeDuplicateDetector,
    KnowledgeMergePlan,
)


def main() -> None:
    print("SAHIBEX 6H-6 KNOWLEDGE DUPLICATE / MERGE TEST")

    detector = KnowledgeDuplicateDetector()

    # 1. Exact duplicate
    first = detector.compare(
        "Python is a programming language.",
        "Python is a programming language.",
    )

    assert first.is_duplicate is True
    assert first.similarity_score == 1.0
    print("[PASS] exact duplicate detection")

    # 2. Normalized duplicate
    normalized = detector.compare(
        "Python   is a programming language.",
        " python is a programming language. ",
    )

    assert normalized.is_duplicate is True
    assert normalized.similarity_score == 1.0
    print("[PASS] normalized duplicate detection")

    # 3. Similar but not duplicate
    similar = detector.compare(
        "Python is a programming language.",
        "Python is a popular programming language.",
    )

    assert similar.is_duplicate is False
    assert 0.0 < similar.similarity_score < 1.0
    print("[PASS] similar knowledge is not automatically duplicate")

    # 4. Clearly different knowledge
    different = detector.compare(
        "Python is a programming language.",
        "The Earth orbits the Sun.",
    )

    assert different.is_duplicate is False
    assert different.similarity_score < 0.6
    print("[PASS] unrelated knowledge separation")

    # 5. Empty statement protection
    try:
        detector.compare(
            "",
            "Python is a programming language.",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "empty first statement should be rejected"
        )
    print("[PASS] empty first statement protection")

    try:
        detector.compare(
            "Python is a programming language.",
            "",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "empty second statement should be rejected"
        )
    print("[PASS] empty second statement protection")

    # 6. Merge planning
    plan = detector.plan_merge(
        primary_knowledge_id="knowledge_001",
        duplicate_knowledge_id="knowledge_002",
        primary_statement="Python is a programming language.",
        duplicate_statement="Python   is a programming language.",
    )

    assert isinstance(plan, KnowledgeMergePlan)
    assert plan.primary_knowledge_id == "knowledge_001"
    assert plan.duplicate_knowledge_id == "knowledge_002"
    assert plan.similarity_score == 1.0
    assert plan.safe_to_merge is True
    print("[PASS] safe merge planning")

    # 7. Different knowledge must not be mergeable
    unsafe_plan = detector.plan_merge(
        primary_knowledge_id="knowledge_001",
        duplicate_knowledge_id="knowledge_003",
        primary_statement="Python is a programming language.",
        duplicate_statement="The Earth orbits the Sun.",
    )

    assert unsafe_plan.safe_to_merge is False
    print("[PASS] unsafe merge protection")

    # 8. Empty knowledge ID protection
    try:
        detector.plan_merge(
            primary_knowledge_id="",
            duplicate_knowledge_id="knowledge_002",
            primary_statement="Python is a programming language.",
            duplicate_statement="Python is a programming language.",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "empty primary knowledge ID should be rejected"
        )
    print("[PASS] empty primary knowledge ID protection")

    # 9. Same knowledge cannot be merged into itself
    try:
        detector.plan_merge(
            primary_knowledge_id="knowledge_001",
            duplicate_knowledge_id="knowledge_001",
            primary_statement="Python is a programming language.",
            duplicate_statement="Python is a programming language.",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "self merge should be rejected"
        )
    print("[PASS] self merge protection")

    print(
        "SAHIBEX 6H-6 KNOWLEDGE DUPLICATE / MERGE TEST: PASS"
    )


if __name__ == "__main__":
    main()
