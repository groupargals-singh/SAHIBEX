from datetime import datetime, timezone

from core.research.conflict import ResearchConflictDetector
from core.research.models import KnowledgeCandidate


def knowledge(
    knowledge_id: str,
    statement: str,
    confidence: float = 0.8,
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


def main() -> None:
    detector = ResearchConflictDetector()

    safe = knowledge(
        "k1",
        "the system is safe",
    )

    unsafe = knowledge(
        "k2",
        "the system is unsafe",
    )

    enabled = knowledge(
        "k3",
        "network access is enabled",
    )

    disabled = knowledge(
        "k4",
        "network access is disabled",
    )

    unrelated = knowledge(
        "k5",
        "the system uses Python",
    )

    negated = knowledge(
        "k6",
        "the system is not safe",
    )

    positive = knowledge(
        "k7",
        "the system is safe",
    )

    # ---------------------------------------------------------
    # 1. Lexical contradiction
    # ---------------------------------------------------------
    result = detector.analyze([safe, unsafe])

    assert result.status == "CONFLICT_DETECTED"
    assert result.conflict_count == 1
    assert set(result.conflict_ids) == {"k1", "k2"}

    print("[PASS] lexical contradiction detection")

    # ---------------------------------------------------------
    # 2. Another contradiction pair
    # ---------------------------------------------------------
    result = detector.analyze([enabled, disabled])

    assert result.status == "CONFLICT_DETECTED"
    assert result.conflict_count == 1
    assert set(result.conflict_ids) == {"k3", "k4"}

    print("[PASS] enabled/disabled contradiction")

    # ---------------------------------------------------------
    # 3. Explicit negation
    # ---------------------------------------------------------
    result = detector.analyze([positive, negated])

    assert result.status == "CONFLICT_DETECTED"
    assert result.conflict_count == 1

    print("[PASS] explicit negation contradiction")

    # ---------------------------------------------------------
    # 4. Unrelated statements must not conflict
    # ---------------------------------------------------------
    result = detector.analyze([safe, unrelated])

    assert result.status == "CONSISTENT"
    assert result.conflict_count == 0

    print("[PASS] unrelated statements remain consistent")

    # ---------------------------------------------------------
    # 5. Consistent duplicate meaning
    # ---------------------------------------------------------
    same_a = knowledge(
        "k8",
        "the system is safe",
    )

    same_b = knowledge(
        "k9",
        "the system is safe",
    )

    result = detector.analyze([same_a, same_b])

    assert result.status == "CONSISTENT"
    assert result.conflict_count == 0

    print("[PASS] identical statements are not conflicts")

    # ---------------------------------------------------------
    # 6. Mixed knowledge set
    # ---------------------------------------------------------
    result = detector.analyze(
        [
            safe,
            unsafe,
            enabled,
            disabled,
            unrelated,
        ]
    )

    assert result.status == "CONFLICT_DETECTED"
    assert result.conflict_count == 2
    assert set(result.conflict_ids) == {
        "k1",
        "k2",
        "k3",
        "k4",
    }
    assert result.consistent_ids == ["k5"]

    print("[PASS] mixed conflict analysis")

    # ---------------------------------------------------------
    # 7. Empty input
    # ---------------------------------------------------------
    result = detector.analyze([])

    assert result.status == "NO_RESULT"
    assert result.total_candidates == 0
    assert result.conflict_count == 0

    print("[PASS] empty input handling")

    print("SAHIBEX RESEARCH CONFLICT TEST: PASS")


if __name__ == "__main__":
    main()
