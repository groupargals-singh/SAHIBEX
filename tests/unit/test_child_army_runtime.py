from core.brain.child_army_runtime import (
    ArmyAction,
    ArmyDecision,
    ChildArmyRuntime,
)


def main() -> None:
    army = ChildArmyRuntime()

    result = army.evaluate(ArmyAction.THINK)
    assert result.allowed is True
    assert result.decision == ArmyDecision.ALLOW_COGNITION

    result = army.evaluate(ArmyAction.RESEARCH)
    assert result.allowed is True

    result = army.evaluate(ArmyAction.ANALYZE)
    assert result.allowed is True

    result = army.evaluate(
        ArmyAction.EXECUTE,
        child_approved=False,
    )
    assert result.allowed is False
    assert result.decision == ArmyDecision.REQUIRE_CHILD_AUTHORITY

    result = army.evaluate(
        ArmyAction.EXECUTE,
        child_approved=True,
    )
    assert result.allowed is True

    result = army.evaluate(
        ArmyAction.FINANCIAL,
        child_approved=False,
        mother_approved=False,
        human_approved=False,
    )
    assert result.allowed is False
    assert result.decision == ArmyDecision.REQUIRE_CHILD_AUTHORITY

    result = army.evaluate(
        ArmyAction.FINANCIAL,
        child_approved=True,
        mother_approved=False,
        human_approved=False,
    )
    assert result.allowed is False
    assert result.decision == ArmyDecision.REQUIRE_MOTHER_AUTHORITY

    result = army.evaluate(
        ArmyAction.FINANCIAL,
        child_approved=True,
        mother_approved=True,
        human_approved=False,
    )
    assert result.allowed is False
    assert result.decision == ArmyDecision.REQUIRE_HUMAN_AUTHORITY

    result = army.evaluate(
        ArmyAction.FINANCIAL,
        child_approved=True,
        mother_approved=True,
        human_approved=True,
    )
    assert result.allowed is True

    assert army.can_think_independently()
    assert army.can_research_independently()
    assert army.can_analyze_independently()
    assert army.can_verify_independently()
    assert army.can_plan_independently()
    assert army.can_propose_independently()

    assert not army.can_self_authorize()
    assert not army.can_grant_authority()
    assert not army.can_override_child()
    assert not army.can_override_mother()
    assert not army.can_override_human()
    assert not army.can_self_promote()
    assert not army.executes_tools()
    assert not army.modifies_soul()
    assert not army.modifies_constitution()

    print("SAHIBEX CHILD ARMY RUNTIME TEST: PASS")


if __name__ == "__main__":
    main()
