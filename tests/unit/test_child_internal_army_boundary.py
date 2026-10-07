from core.brain.child_internal_army_boundary import (
    ArmyAction,
    ArmyActor,
    ArmyDecision,
    ChildInternalArmyBoundary,
)


def main() -> None:
    boundary = ChildInternalArmyBoundary

    # Army cognitive independence.
    for action in (
        ArmyAction.THINK,
        ArmyAction.RESEARCH,
        ArmyAction.ANALYZE,
        ArmyAction.VERIFY,
        ArmyAction.PLAN,
        ArmyAction.PROPOSE,
        ArmyAction.READ,
    ):
        result = boundary.decide(
            ArmyActor.CHILD_ARMY,
            action,
        )

        assert result.allowed
        assert result.decision == ArmyDecision.ALLOW_COGNITIVE
        assert not result.authority_granted

    # Protected actions require Child authority.
    for action in (
        ArmyAction.WRITE,
        ArmyAction.DELETE,
        ArmyAction.EXECUTE,
        ArmyAction.NETWORK,
        ArmyAction.CREDENTIAL,
        ArmyAction.SYSTEM_CHANGE,
        ArmyAction.EXTERNAL_CONTROL,
        ArmyAction.SELF_UPDATE,
    ):
        result = boundary.decide(
            ArmyActor.CHILD_ARMY,
            action,
        )

        assert not result.allowed
        assert result.decision == ArmyDecision.REQUIRE_CHILD_AUTHORITY

        result = boundary.decide(
            ArmyActor.CHILD_ARMY,
            action,
            child_approved=True,
        )

        assert result.allowed
        assert result.authority_granted

    # Financial action requires Mother + Human.
    result = boundary.decide(
        ArmyActor.CHILD_ARMY,
        ArmyAction.FINANCIAL,
    )

    assert not result.allowed
    assert result.decision == ArmyDecision.REQUIRE_HUMAN_AUTHORITY

    result = boundary.decide(
        ArmyActor.CHILD_ARMY,
        ArmyAction.FINANCIAL,
        mother_approved=True,
        human_approved=True,
    )

    assert result.allowed
    assert result.authority_granted

    # Authority escalation is always denied.
    for action in (
        ArmyAction.GRANT_AUTHORITY,
        ArmyAction.OVERRIDE_CHILD,
        ArmyAction.OVERRIDE_MOTHER,
        ArmyAction.OVERRIDE_HUMAN,
        ArmyAction.SELF_PROMOTION,
    ):
        result = boundary.decide(
            ArmyActor.CHILD_ARMY,
            action,
        )

        assert not result.allowed
        assert result.decision == ArmyDecision.DENY
        assert not result.authority_granted

    # External actors can never become Army authority.
    for actor in (
        ArmyActor.SOFTWARE,
        ArmyActor.TOOL,
        ArmyActor.EXTERNAL_MODEL,
    ):
        result = boundary.decide(
            actor,
            ArmyAction.EXECUTE,
            child_approved=True,
            mother_approved=True,
            human_approved=True,
        )

        assert not result.allowed
        assert result.decision == ArmyDecision.DENY
        assert not result.authority_granted

    # Constitutional guarantees.
    assert boundary.army_can_think_independently()
    assert boundary.army_can_research_independently()
    assert boundary.army_can_verify_independently()

    assert not boundary.army_can_override_child()
    assert not boundary.army_can_override_mother()
    assert not boundary.army_can_override_human()
    assert not boundary.army_can_grant_authority()
    assert not boundary.army_can_self_promote()
    assert not boundary.army_can_self_authorize_protected_action()

    assert boundary.capability_is_not_authority()
    assert boundary.rejection_blocks_execution()
    assert boundary.unknown_state_fails_closed()

    assert not boundary.creates_army_brain()
    assert not boundary.activates_army_brain()
    assert not boundary.executes_actions()

    print("SAHIBEX CHILD INTERNAL ARMY BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
