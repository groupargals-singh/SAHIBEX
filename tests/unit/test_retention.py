from core.brain.retention import (
    RetentionControlEngine,
    RetentionInput,
    RetentionLevel,
)


def main() -> None:
    engine = RetentionControlEngine()

    retain = engine.evaluate(
        RetentionInput(
            content="Critical active task information",
            importance=1.0,
            urgency=0.9,
            risk=0.9,
            goal_relevance=1.0,
            priority=1.0,
        )
    )

    assert retain.level == RetentionLevel.RETAIN
    assert retain.retained is True
    assert retain.retention_score >= 0.70

    temporary = engine.evaluate(
        RetentionInput(
            content="Moderately useful information",
            importance=0.5,
            urgency=0.4,
            risk=0.4,
            goal_relevance=0.5,
            priority=0.4,
        )
    )

    assert temporary.level == RetentionLevel.TEMPORARY
    assert temporary.retained is True

    release = engine.evaluate(
        RetentionInput(
            content="Low-value information",
            importance=0.0,
            urgency=0.0,
            risk=0.0,
            goal_relevance=0.0,
            priority=0.0,
        )
    )

    assert release.level == RetentionLevel.RELEASE
    assert release.retained is False

    try:
        RetentionInput(
            content="Invalid",
            importance=2.0,
            urgency=0.0,
            risk=0.0,
            goal_relevance=0.0,
            priority=0.0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "out-of-range retention value was accepted"
        )

    print(
        "SAHIBEX PHASE 1 #41 "
        "RETENTION-CONTROL ENGINE TEST: PASS"
    )


if __name__ == "__main__":
    main()
