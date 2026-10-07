from core.research.memory_cleanup import (
    MemoryCleanupEngine,
    MemoryCleanupInput,
)


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[PASS] {label}")


def main() -> None:
    print("SAHIBEX PHASE 2 #61 MEMORY CLEANUP TEST")

    engine = MemoryCleanupEngine()

    candidate = engine.assess(
        MemoryCleanupInput(
            memory_id="memory-old",
            importance=0.1,
            confidence=0.2,
            access_frequency=0.1,
            age_score=1.0,
            future_reuse=0.1,
        )
    )

    check(
        candidate.memory_id == "memory-old",
        "memory identity preserved",
    )

    check(
        candidate.cleanup_candidate,
        "low-retention memory identified",
    )

    check(
        candidate.action == "PROPOSAL_ONLY",
        "cleanup remains proposal only",
    )

    check(
        candidate.retention_score < 0.35,
        "low retention score detected",
    )

    retained = engine.assess(
        MemoryCleanupInput(
            memory_id="memory-important",
            importance=1.0,
            confidence=1.0,
            access_frequency=1.0,
            age_score=0.0,
            future_reuse=1.0,
        )
    )

    check(
        not retained.cleanup_candidate,
        "important memory retained",
    )

    check(
        retained.action == "RETAIN",
        "retention decision is explicit",
    )

    protected = engine.assess(
        MemoryCleanupInput(
            memory_id="memory-protected",
            importance=0.0,
            confidence=0.0,
            access_frequency=0.0,
            age_score=1.0,
            future_reuse=0.0,
            protected=True,
        )
    )

    check(
        protected.protected,
        "protected memory recognized",
    )

    check(
        not protected.cleanup_candidate,
        "protected memory cannot become cleanup candidate",
    )

    check(
        protected.action == "DENY_CLEANUP",
        "protected cleanup denied",
    )

    check(
        candidate.result_id != "",
        "cleanup result has unique identity",
    )

    check(
        candidate.input_id != "",
        "cleanup input has unique identity",
    )

    try:
        engine.assess("invalid")
    except TypeError:
        print("[PASS] invalid cleanup input blocked")
    else:
        raise AssertionError(
            "invalid cleanup input was not blocked"
        )

    try:
        MemoryCleanupInput(
            memory_id="",
            importance=0.5,
        )
    except ValueError:
        print("[PASS] empty memory identity blocked")
    else:
        raise AssertionError(
            "empty memory identity was not blocked"
        )

    try:
        MemoryCleanupInput(
            memory_id="memory-invalid",
            importance=1.5,
        )
    except ValueError:
        print("[PASS] invalid importance range blocked")
    else:
        raise AssertionError(
            "invalid importance range was not blocked"
        )

    print("SAHIBEX PHASE 2 #61 MEMORY CLEANUP TEST: PASS")


if __name__ == "__main__":
    main()
