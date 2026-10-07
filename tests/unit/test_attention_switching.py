from core.brain.attention_switching import (
    AttentionSwitchDecision,
    AttentionSwitchingEngine,
    AttentionSwitchInput,
)


def main() -> None:
    engine = AttentionSwitchingEngine()

    switch = engine.evaluate(
        AttentionSwitchInput(
            current_focus_score=0.4,
            new_input_score=1.0,
            current_focus_urgency=0.3,
            new_input_urgency=1.0,
            current_focus_risk=0.2,
            new_input_risk=0.9,
            current_goal_relevance=0.4,
            new_goal_relevance=1.0,
            current_priority=0.3,
            new_priority=1.0,
        )
    )

    assert switch.decision == AttentionSwitchDecision.SWITCH
    assert switch.should_switch is True
    assert switch.new_score > switch.current_score

    hold = engine.evaluate(
        AttentionSwitchInput(
            current_focus_score=0.8,
            new_input_score=0.75,
            current_focus_urgency=0.7,
            new_input_urgency=0.7,
            current_focus_risk=0.6,
            new_input_risk=0.6,
            current_goal_relevance=0.9,
            new_goal_relevance=0.8,
            current_priority=0.8,
            new_priority=0.7,
        )
    )

    assert hold.decision == AttentionSwitchDecision.HOLD
    assert hold.should_switch is False

    no_focus = engine.evaluate(
        AttentionSwitchInput(
            current_focus_score=0.8,
            new_input_score=0.0,
            current_focus_urgency=0.8,
            new_input_urgency=0.0,
            current_focus_risk=0.8,
            new_input_risk=0.0,
            current_goal_relevance=0.8,
            new_goal_relevance=0.0,
            current_priority=0.8,
            new_priority=0.0,
        )
    )

    assert (
        no_focus.decision
        == AttentionSwitchDecision.NO_FOCUS
    )
    assert no_focus.should_switch is False

    try:
        AttentionSwitchInput(
            current_focus_score=2.0,
            new_input_score=0.0,
            current_focus_urgency=0.0,
            new_input_urgency=0.0,
            current_focus_risk=0.0,
            new_input_risk=0.0,
            current_goal_relevance=0.0,
            new_goal_relevance=0.0,
            current_priority=0.0,
            new_priority=0.0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "out-of-range attention value was accepted"
        )

    print(
        "SAHIBEX PHASE 1 #40 "
        "ATTENTION-SWITCHING ENGINE TEST: PASS"
    )


if __name__ == "__main__":
    main()
