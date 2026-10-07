from core.research.memory_importance import (
    MemoryImportanceEngine,
    MemoryImportanceInput,
    MemoryImportanceLevel,
)


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)

    print(f"[PASS] {label}")


def main() -> None:
    print("SAHIBEX PHASE 2 #54 MEMORY IMPORTANCE TEST")

    engine = MemoryImportanceEngine()

    critical = engine.evaluate(
        MemoryImportanceInput(
            content="Critical SAHIBEX constitutional requirement.",
            existing_importance=1.0,
            goal_relevance=1.0,
            recurrence=0.9,
            consequence=1.0,
            future_reuse=1.0,
        )
    )

    check(
        critical.level == MemoryImportanceLevel.CRITICAL,
        "critical importance classification",
    )

    check(
        0.85 <= critical.importance_score <= 1.0,
        "critical importance score range",
    )

    high = engine.evaluate(
        MemoryImportanceInput(
            content="Important SAHIBEX project decision.",
            existing_importance=0.8,
            goal_relevance=0.8,
            recurrence=0.7,
            consequence=0.7,
            future_reuse=0.8,
        )
    )

    check(
        high.level == MemoryImportanceLevel.HIGH,
        "high importance classification",
    )

    low = engine.evaluate(
        MemoryImportanceInput(
            content="Low-value temporary information.",
            existing_importance=0.1,
            goal_relevance=0.1,
            recurrence=0.1,
            consequence=0.1,
            future_reuse=0.1,
        )
    )

    check(
        low.level == MemoryImportanceLevel.LOW,
        "low importance classification",
    )

    check(
        critical.importance_score
        > high.importance_score
        > low.importance_score,
        "importance ordering is deterministic",
    )

    try:
        MemoryImportanceInput(
            content="Invalid",
            existing_importance=1.5,
            goal_relevance=0.5,
            recurrence=0.5,
            consequence=0.5,
            future_reuse=0.5,
        )
    except ValueError:
        print("[PASS] invalid importance range blocked")
    else:
        raise AssertionError(
            "invalid importance range was not blocked"
        )

    try:
        engine.evaluate("invalid")
    except TypeError:
        print("[PASS] invalid engine input blocked")
    else:
        raise AssertionError(
            "invalid engine input was not blocked"
        )

    check(
        critical.level != MemoryImportanceLevel.LOW,
        "importance result remains independent of authority",
    )

    print("SAHIBEX PHASE 2 #54 MEMORY IMPORTANCE TEST: PASS")


if __name__ == "__main__":
    main()
