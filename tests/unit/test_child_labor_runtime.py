from core.brain.child_labor_runtime import (
    ChildLaborRuntime,
    LaborAction,
    LaborDecision,
)


def main() -> None:
    runtime = ChildLaborRuntime()

    result = runtime.evaluate(LaborAction.THINK)

    assert result.allowed is True
    assert result.decision == LaborDecision.ALLOW_COGNITION

    result = runtime.evaluate(LaborAction.READ)

    assert result.allowed is True

    result = runtime.evaluate(
        LaborAction.EXECUTE,
        child_authority_approved=False,
    )

    assert result.allowed is False
    assert result.decision == LaborDecision.REQUIRE_CHILD_AUTHORITY

    result = runtime.evaluate(
        LaborAction.EXECUTE,
        child_authority_approved=True,
    )

    assert result.allowed is True

    result = runtime.evaluate(
        LaborAction.FINANCIAL,
        child_authority_approved=True,
        mother_authority_approved=True,
        human_authority_approved=False,
    )

    assert result.allowed is False
    assert result.decision == LaborDecision.REQUIRE_HUMAN_AUTHORITY

    result = runtime.evaluate(
        LaborAction.FINANCIAL,
        child_authority_approved=True,
        mother_authority_approved=True,
        human_authority_approved=True,
    )

    assert result.allowed is True

    result = runtime.evaluate(
        LaborAction.SOUL_CHANGE,
        human_authority_approved=False,
    )

    assert result.allowed is False
    assert result.decision == LaborDecision.REQUIRE_HUMAN_AUTHORITY

    result = runtime.evaluate(
        LaborAction.SOUL_CHANGE,
        human_authority_approved=True,
    )

    assert result.allowed is True

    assert not runtime.can_self_authorize()
    assert not runtime.can_grant_authority()
    assert not runtime.can_override_child()
    assert not runtime.can_override_mother()
    assert not runtime.can_override_human()
    assert not runtime.can_self_promote()
    assert not runtime.can_modify_own_soul()
    assert not runtime.can_modify_own_constitution()
    assert not runtime.can_execute_without_authority()
    assert not runtime.can_execute_tools()

    print("SAHIBEX CHILD LABOR RUNTIME TEST: PASS")


if __name__ == "__main__":
    main()
