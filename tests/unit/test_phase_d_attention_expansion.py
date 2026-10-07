from core.brain.attention_expansion import (
    AttentionExpansionEngine,
    AttentionState,
)


def main() -> None:
    engine = AttentionExpansionEngine()

    # 1-6: selection, relevance, priority, urgency, risk, goal relevance
    active = engine.assess(
        selection=1.0,
        relevance=0.9,
        priority=0.9,
        urgency=0.8,
        risk=0.7,
        goal_relevance=1.0,
    )
    assert active.state == AttentionState.ACTIVE
    assert active.selection_score >= 0.55

    # 7: attention retention
    retained = engine.assess(
        selection=0.8,
        relevance=0.7,
        priority=0.7,
        urgency=0.6,
        risk=0.5,
        goal_relevance=0.8,
    )
    assert retained.state == AttentionState.ACTIVE

    # 8-9: switching/distraction support
    distracted = engine.assess(
        selection=0.0,
        relevance=0.1,
        priority=0.1,
        urgency=0.0,
        risk=0.0,
        goal_relevance=0.1,
    )
    assert distracted.state == AttentionState.DISTRACTED

    # 10: conflict handling
    conflict = engine.resolve_conflict(
        current_score=0.40,
        competing_score=0.80,
    )
    assert conflict.conflict is True
    assert conflict.preferred == "competing"

    stable = engine.resolve_conflict(
        current_score=0.60,
        competing_score=0.64,
    )
    assert stable.conflict is False
    assert stable.preferred == "current"

    # 11: recovery / re-focus
    recovered = engine.recover(
        previous_state=AttentionState.DISTRACTED,
        recovery_signal=0.90,
    )
    assert recovered.recovered is True

    not_recovered = engine.recover(
        previous_state=AttentionState.DISTRACTED,
        recovery_signal=0.30,
    )
    assert not_recovered.recovered is False

    # Boundary validation
    try:
        engine.assess(
            selection=2.0,
            relevance=0.0,
            priority=0.0,
            urgency=0.0,
            risk=0.0,
            goal_relevance=0.0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("out-of-range attention value was accepted")

    print("PHASE_D_ATTENTION_EXPANSION_TEST: PASS")


if __name__ == "__main__":
    main()
