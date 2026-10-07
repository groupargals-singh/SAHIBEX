from core.brain.urgency import (
    UrgencyEngine,
    UrgencyInput,
    UrgencyLevel,
)


def main() -> None:
    engine = UrgencyEngine()

    critical = engine.evaluate(
        UrgencyInput(
            content="Immediate critical event",
            time_pressure=1.0,
            deadline_proximity=1.0,
            consequence_of_delay=1.0,
            dependency_blocking=1.0,
            user_urgency=1.0,
        )
    )

    assert critical.level == UrgencyLevel.CRITICAL
    assert critical.urgent is True
    assert critical.urgency_score >= 0.80

    high = engine.evaluate(
        UrgencyInput(
            content="Important time-sensitive task",
            time_pressure=0.8,
            deadline_proximity=0.7,
            consequence_of_delay=0.6,
            dependency_blocking=0.5,
            user_urgency=0.7,
        )
    )

    assert high.level == UrgencyLevel.HIGH
    assert high.urgent is True

    normal = engine.evaluate(
        UrgencyInput(
            content="Normal task",
            time_pressure=0.4,
            deadline_proximity=0.4,
            consequence_of_delay=0.4,
            dependency_blocking=0.3,
            user_urgency=0.3,
        )
    )

    assert normal.level == UrgencyLevel.NORMAL

    low = engine.evaluate(
        UrgencyInput(
            content="Low urgency information",
            time_pressure=0.0,
            deadline_proximity=0.0,
            consequence_of_delay=0.0,
            dependency_blocking=0.0,
            user_urgency=0.0,
        )
    )

    assert low.level == UrgencyLevel.LOW
    assert low.urgent is False

    try:
        UrgencyInput(
            content="Invalid urgency",
            time_pressure=2.0,
            deadline_proximity=0.0,
            consequence_of_delay=0.0,
            dependency_blocking=0.0,
            user_urgency=0.0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "out-of-range urgency value was accepted"
        )

    print(
        "SAHIBEX PHASE 1 #37 "
        "URGENCY ENGINE TEST: PASS"
    )


if __name__ == "__main__":
    main()
