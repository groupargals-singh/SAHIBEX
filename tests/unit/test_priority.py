from core.brain.priority import (
    PRIORITY_VERSION,
    PriorityEngine,
    PriorityInput,
    PriorityLevel,
)


def test_low_priority() -> None:
    engine = PriorityEngine()

    result = engine.assess(
        PriorityInput(
            urgency=0.10,
            risk=0.10,
            goal_relevance=0.10,
            importance=0.10,
            consequence=0.10,
            user_priority=0.10,
            input_id="input_001",
        )
    )

    assert result.priority_score < 0.35
    assert result.level == PriorityLevel.LOW
    assert result.is_high_priority is False
    assert result.version == PRIORITY_VERSION


def test_high_priority() -> None:
    engine = PriorityEngine()

    result = engine.assess(
        PriorityInput(
            urgency=0.80,
            risk=0.70,
            goal_relevance=0.80,
            importance=0.70,
            consequence=0.70,
            user_priority=0.80,
            input_id="input_002",
        )
    )

    assert result.priority_score >= 0.60
    assert result.level == PriorityLevel.HIGH
    assert result.is_high_priority is True


def test_critical_priority() -> None:
    engine = PriorityEngine()

    result = engine.assess(
        PriorityInput(
            urgency=1.0,
            risk=1.0,
            goal_relevance=1.0,
            importance=1.0,
            consequence=1.0,
            user_priority=1.0,
            input_id="input_003",
        )
    )

    assert result.priority_score == 1.0
    assert result.level == PriorityLevel.CRITICAL


def test_security_and_scope_boundary() -> None:
    engine = PriorityEngine()

    assert engine.schedules_tasks() is False
    assert engine.executes_actions() is False
    assert engine.grants_permission() is False
    assert engine.modifies_tasks() is False
    assert engine.overrides_human_authority() is False


def test_invalid_signal_rejected() -> None:
    engine = PriorityEngine()

    try:
        engine.assess(
            PriorityInput(
                urgency=1.5,
                risk=0.5,
                goal_relevance=0.5,
                importance=0.5,
                consequence=0.5,
                user_priority=0.5,
                input_id="input_004",
            )
        )
    except ValueError:
        pass
    else:
        raise AssertionError("invalid priority signal was not rejected")


if __name__ == "__main__":
    test_low_priority()
    test_high_priority()
    test_critical_priority()
    test_security_and_scope_boundary()
    test_invalid_signal_rejected()

    print("SAHIBEX PHASE 1 #36 PRIORITY TEST: PASS")
