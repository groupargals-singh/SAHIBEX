from core.brain.child_authority_boundary import (
    ChildActionClass,
    ChildAuthorityBoundary,
    ChildAuthorityLevel,
    ChildPermissionDecision,
)


def main() -> None:
    authority = ChildAuthorityBoundary

    # Independent cognitive actions.
    for action in (
        ChildActionClass.THINK,
        ChildActionClass.RESEARCH,
        ChildActionClass.READ,
        ChildActionClass.ANALYZE,
        ChildActionClass.LEARN,
        ChildActionClass.PLAN,
        ChildActionClass.VERIFY,
        ChildActionClass.PROPOSE,
    ):
        result = authority.decide(
            ChildAuthorityLevel.CHILD_BRAIN,
            action,
        )

        assert result.allowed
        assert (
            result.decision
            == ChildPermissionDecision.ALLOW_AUTONOMOUS
        )

    # Protected actions must be blocked without Mother approval.
    for action in (
        ChildActionClass.WRITE,
        ChildActionClass.DELETE,
        ChildActionClass.EXECUTE,
        ChildActionClass.NETWORK,
        ChildActionClass.CREDENTIAL,
        ChildActionClass.SYSTEM_CHANGE,
        ChildActionClass.EXTERNAL_CONTROL,
        ChildActionClass.SELF_UPDATE,
        ChildActionClass.CHILD_CREATION,
        ChildActionClass.CHILD_RETIREMENT,
        ChildActionClass.MIGRATION,
    ):
        result = authority.decide(
            ChildAuthorityLevel.CHILD_BRAIN,
            action,
        )

        assert not result.allowed
        assert (
            result.decision
            == ChildPermissionDecision.REQUIRE_MOTHER_AUTHORITY
        )

    # Mother approval permits Mother-gated actions.
    result = authority.decide(
        ChildAuthorityLevel.CHILD_BRAIN,
        ChildActionClass.WRITE,
        mother_approved=True,
    )

    assert result.allowed

    # Human-gated actions.
    for action in (
        ChildActionClass.FINANCIAL,
        ChildActionClass.CONSTITUTIONAL_CHANGE,
        ChildActionClass.SOUL_CHANGE,
    ):
        result = authority.decide(
            ChildAuthorityLevel.CHILD_BRAIN,
            action,
        )

        assert not result.allowed
        assert (
            result.decision
            == ChildPermissionDecision.REQUIRE_HUMAN_AUTHORITY
        )

        result = authority.decide(
            ChildAuthorityLevel.CHILD_BRAIN,
            action,
            human_approved=True,
        )

        assert result.allowed

    # External actors can never become authority.
    for actor in (
        ChildAuthorityLevel.SOFTWARE,
        ChildAuthorityLevel.TOOL,
        ChildAuthorityLevel.EXTERNAL_MODEL,
    ):
        result = authority.decide(
            actor,
            ChildActionClass.EXECUTE,
            mother_approved=True,
            human_approved=True,
        )

        assert not result.allowed
        assert result.decision == ChildPermissionDecision.DENY

    # Unknown action must fail closed.
    class UnknownAction:
        pass

    result = authority.decide(
        ChildAuthorityLevel.CHILD_BRAIN,
        UnknownAction(),  # type: ignore[arg-type]
    )

    assert not result.allowed
    assert result.decision == ChildPermissionDecision.DENY

    # Constitutional guarantees.
    assert authority.child_can_think_independently()
    assert authority.child_can_research_independently()
    assert authority.child_can_plan_independently()

    assert not authority.child_can_self_authorize_protected_action()
    assert not authority.child_can_override_mother()
    assert not authority.child_can_override_human()
    assert not authority.child_can_grant_itself_authority()
    assert not authority.child_can_grant_authority_to_others()

    assert authority.rejection_blocks_execution()
    assert authority.unknown_state_fails_closed()
    assert authority.capability_is_not_authority()

    # Authority layer must not execute anything.
    assert not authority.executes_actions()

    print("SAHIBEX CHILD AUTHORITY BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
