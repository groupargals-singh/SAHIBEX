from core.brain.distraction_filter import (
    DistractionDecision,
    DistractionFilterEngine,
    DistractionFilterInput,
)


def main() -> None:
    engine = DistractionFilterEngine()

    allow = engine.evaluate(
        DistractionFilterInput(
            content="Directly relevant active task information",
            relevance=1.0,
            goal_relevance=1.0,
            urgency=0.8,
            priority=1.0,
            distraction_strength=0.0,
        )
    )

    assert allow.decision == DistractionDecision.ALLOW
    assert allow.filtered is False
    assert allow.signal_score >= 0.60

    hold = engine.evaluate(
        DistractionFilterInput(
            content="Useful but non-critical information",
            relevance=0.5,
            goal_relevance=0.5,
            urgency=0.3,
            priority=0.4,
            distraction_strength=0.4,
        )
    )

    assert hold.decision == DistractionDecision.HOLD
    assert hold.filtered is False

    filtered = engine.evaluate(
        DistractionFilterInput(
            content="Unrelated distracting information",
            relevance=0.0,
            goal_relevance=0.0,
            urgency=0.0,
            priority=0.0,
            distraction_strength=1.0,
        )
    )

    assert filtered.decision == DistractionDecision.FILTER
    assert filtered.filtered is True

    try:
        DistractionFilterInput(
            content="Invalid",
            relevance=2.0,
            goal_relevance=0.0,
            urgency=0.0,
            priority=0.0,
            distraction_strength=0.0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "out-of-range distraction value was accepted"
        )

    print(
        "SAHIBEX PHASE 1 #42 "
        "DISTRACTION-FILTER ENGINE TEST: PASS"
    )


if __name__ == "__main__":
    main()
