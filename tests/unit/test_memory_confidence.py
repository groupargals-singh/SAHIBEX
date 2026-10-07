from core.research.memory_confidence import (
    MemoryConfidenceEngine,
    MemoryConfidenceInput,
    MemoryConfidenceLevel,
)


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)

    print(f"[PASS] {label}")


def main() -> None:
    print("SAHIBEX PHASE 2 #55 MEMORY CONFIDENCE TEST")

    engine = MemoryConfidenceEngine()

    very_high = engine.assess(
        MemoryConfidenceInput(
            content="Strongly verified memory.",
            existing_confidence=1.0,
            verification_score=1.0,
            provenance_score=1.0,
            evidence_score=1.0,
            source_reliability=1.0,
            freshness_score=0.95,
            conflict_score=1.0,
        )
    )

    check(
        very_high.level == MemoryConfidenceLevel.VERY_HIGH,
        "very-high confidence classification",
    )

    check(
        0.85 <= very_high.confidence_score <= 1.0,
        "very-high confidence score range",
    )

    high = engine.assess(
        MemoryConfidenceInput(
            content="Well-supported memory.",
            existing_confidence=0.85,
            verification_score=0.80,
            provenance_score=0.80,
            evidence_score=0.80,
            source_reliability=0.80,
            freshness_score=0.75,
            conflict_score=0.80,
        )
    )

    check(
        high.level == MemoryConfidenceLevel.HIGH,
        "high confidence classification",
    )

    low = engine.assess(
        MemoryConfidenceInput(
            content="Weakly supported memory.",
            existing_confidence=0.10,
            verification_score=0.10,
            provenance_score=0.10,
            evidence_score=0.10,
            source_reliability=0.10,
            freshness_score=0.10,
            conflict_score=0.10,
        )
    )

    check(
        low.level == MemoryConfidenceLevel.LOW,
        "low confidence classification",
    )

    check(
        very_high.confidence_score
        > high.confidence_score
        > low.confidence_score,
        "confidence ordering is deterministic",
    )

    try:
        MemoryConfidenceInput(
            content="Invalid",
            existing_confidence=1.5,
            verification_score=0.5,
            provenance_score=0.5,
            evidence_score=0.5,
            source_reliability=0.5,
            freshness_score=0.5,
            conflict_score=0.5,
        )
    except ValueError:
        print("[PASS] invalid confidence range blocked")
    else:
        raise AssertionError(
            "invalid confidence range was not blocked"
        )

    try:
        engine.assess("invalid")
    except TypeError:
        print("[PASS] invalid engine input blocked")
    else:
        raise AssertionError(
            "invalid engine input was not blocked"
        )

    check(
        very_high.level != MemoryConfidenceLevel.LOW,
        "confidence assessment remains independent of authority",
    )

    print("SAHIBEX PHASE 2 #55 MEMORY CONFIDENCE TEST: PASS")


if __name__ == "__main__":
    main()
