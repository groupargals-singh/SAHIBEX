from core.brain.attention import (
    AttentionDecision,
    AttentionEngine,
    AttentionInput,
)


def main() -> None:
    engine = AttentionEngine()

    high = engine.evaluate(
        AttentionInput(
            content="Critical user task",
            relevance=1.0,
            urgency=1.0,
            risk=0.8,
            goal_relevance=1.0,
            priority=1.0,
        )
    )

    assert high.decision == AttentionDecision.FOCUS
    assert high.focused is True
    assert high.attention_score >= 0.60

    medium = engine.evaluate(
        AttentionInput(
            content="Potentially useful information",
            relevance=0.6,
            urgency=0.4,
            risk=0.3,
            goal_relevance=0.6,
            priority=0.5,
        )
    )

    assert medium.decision == AttentionDecision.HOLD
    assert medium.focused is False

    low = engine.evaluate(
        AttentionInput(
            content="Irrelevant distraction",
            relevance=0.0,
            urgency=0.0,
            risk=0.0,
            goal_relevance=0.0,
            priority=0.0,
        )
    )

    assert low.decision == AttentionDecision.IGNORE
    assert low.ignored is True

    try:
        AttentionInput(
            content="invalid",
            relevance=2.0,
            urgency=0.0,
            risk=0.0,
            goal_relevance=0.0,
            priority=0.0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "out-of-range attention value was accepted"
        )

    print(
        "SAHIBEX PHASE 1 #35 "
        "ATTENTION ENGINE TEST: PASS"
    )


if __name__ == "__main__":
    main()
