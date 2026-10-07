from core.brain.child_labor_boundary import (
    ChildLaborBoundary,
    LaborAction,
    LaborActor,
    LaborDecision,
)


def main() -> None:
    boundary = ChildLaborBoundary

    # Labor has limited independent cognition.
    for action in (
        LaborAction.THINK,
        LaborAction.READ,
        LaborAction.PLAN,
        LaborAction.PROPOSE,
    ):
        result = boundary.decide(
            LaborActor.CHILD_LABOR,
            action,
        )

        assert result.allowed
        assert result.decision == LaborDecision.ALLOW_LIMITED_OPERATION
        assert not result.authority_granted
        assert not result.execution_allowed

    # Protected operations require Child authority.
    for action in (
        LaborAction.WRITE,
        LaborAction.DELETE,
        LaborAction.EXECUTE,
        LaborAction.NETWORK,
        LaborAction.CREDENTIAL,
        LaborAction.SYSTEM_CHANGE,
        LaborAction.EXTERNAL_CONTROL,
        LaborAction.SELF_UPDATE,
    ):
        result = boundary.decide(
            LaborActor.CHILD_LABOR,
            action,
        )

        assert not result.allowed
        assert result.decision == LaborDecision.REQUIRE_CHILD_AUTHORITY
        assert not result.execution_allowed

        result = boundary.decide(
            LaborActor.CHILD_LABOR,
            action,
            child_approved=True,
        )

        assert result.allowed
        assert result.authority_granted
        assert result.execution_allowed

    # Financial action requires Mother + Human.
    result = boundary.decide(
        LaborActor.CHILD_LABOR,
        LaborAction.FINANCIAL,
    )

    assert not result.allowed
    assert result.decision == LaborDecision.REQUIRE_MOTHER_AUTHORITY

    result = boundary.decide(
        LaborActor.CHILD_LABOR,
        LaborAction.FINANCIAL,
        mother_approved=True,
        human_approved=True,
    )

    assert result.allowed
    assert result.authority_granted
    assert result.execution_allowed

    # Soul / Constitution changes require Human.
    for action in (
        LaborAction.MODIFY_CONSTITUTION,
        LaborAction.MODIFY_SOUL,
    ):
        result = boundary.decide(
            LaborActor.CHILD_LABOR,
            action,
        )

        assert not result.allowed
        assert result.decision == LaborDecision.REQUIRE_HUMAN_AUTHORITY

        result = boundary.decide(
            LaborActor.CHILD_LABOR,
            action,
            human_approved=True,
        )

        assert result.allowed
        assert result.authority_granted
        assert result.execution_allowed

    # Authority escalation is denied.
    for action in (
        LaborAction.GRANT_AUTHORITY,
        LaborAction.OVERRIDE_CHILD,
        LaborAction.OVERRIDE_MOTHER,
        LaborAction.OVERRIDE_HUMAN,
        LaborAction.SELF_PROMOTION,
    ):
        result = boundary.decide(
            LaborActor.CHILD_LABOR,
            action,
        )

        assert not result.allowed
        assert result.decision == LaborDecision.DENY
        assert not result.authority_granted
        assert not result.execution_allowed

    # External actors cannot become Labor authority.
    for actor in (
        LaborActor.SOFTWARE,
        LaborActor.TOOL,
        LaborActor.EXTERNAL_MODEL,
    ):
        result = boundary.decide(
            actor,
            LaborAction.EXECUTE,
            child_approved=True,
            mother_approved=True,
            human_approved=True,
        )

        assert not result.allowed
        assert result.decision == LaborDecision.DENY
        assert not result.authority_granted
        assert not result.execution_allowed

    # Constitutional guarantees.
    assert boundary.labor_can_think()
    assert boundary.labor_can_read()
    assert boundary.labor_can_plan()

    assert not boundary.labor_can_execute_without_child_permission()
    assert not boundary.labor_can_self_authorize()
    assert not boundary.labor_can_grant_authority()
    assert not boundary.labor_can_override_child()
    assert not boundary.labor_can_override_mother()
    assert not boundary.labor_can_override_human()
    assert not boundary.labor_can_self_promote()

    assert boundary.capability_is_not_authority()
    assert boundary.rejection_blocks_execution()
    assert boundary.unknown_state_fails_closed()

    assert not boundary.creates_labor_brain()
    assert not boundary.activates_labor_brain()
    assert not boundary.executes_actions()

    print("SAHIBEX CHILD LABOR BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
