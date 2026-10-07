from core.brain.child_self_improvement_boundary import (
    ChildSelfImprovementBoundary,
    ImprovementActor,
    ImprovementDecision,
    ImprovementOperation,
    ImprovementTarget,
)


def main() -> None:
    boundary = ChildSelfImprovementBoundary

    # Child can independently discover and design improvements.
    for operation in (
        ImprovementOperation.DETECT_WEAKNESS,
        ImprovementOperation.ANALYZE,
        ImprovementOperation.PROPOSE,
        ImprovementOperation.DESIGN,
    ):
        result = boundary.decide(
            ImprovementActor.CHILD_BRAIN,
            operation,
            ImprovementTarget.CHILD_CODE,
        )

        assert result.allowed
        assert not result.upgrade_authorized
        assert not result.authority_escalated

    # Actual code upgrade requires Mother approval.
    result = boundary.decide(
        ImprovementActor.CHILD_BRAIN,
        ImprovementOperation.APPLY_UPGRADE,
        ImprovementTarget.CHILD_CODE,
        mother_approved=False,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
    )

    assert not result.allowed
    assert result.decision == ImprovementDecision.REQUIRE_MOTHER_APPROVAL

    result = boundary.decide(
        ImprovementActor.CHILD_BRAIN,
        ImprovementOperation.APPLY_UPGRADE,
        ImprovementTarget.CHILD_CODE,
        mother_approved=True,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
    )

    assert result.allowed
    assert result.upgrade_authorized
    assert not result.authority_escalated

    # Army and Labor can also be improved through the same gate.
    for target in (
        ImprovementTarget.INTERNAL_ARMY,
        ImprovementTarget.INTERNAL_LABOR,
    ):
        result = boundary.decide(
            ImprovementActor.CHILD_BRAIN,
            ImprovementOperation.APPLY_UPGRADE,
            target,
            mother_approved=True,
            security_passed=True,
            regression_passed=True,
            verification_passed=True,
        )

        assert result.allowed
        assert result.upgrade_authorized

    # Any failed validation blocks the upgrade.
    for security, regression, verification in (
        (False, True, True),
        (True, False, True),
        (True, True, False),
    ):
        result = boundary.decide(
            ImprovementActor.CHILD_BRAIN,
            ImprovementOperation.APPLY_UPGRADE,
            ImprovementTarget.CHILD_CODE,
            mother_approved=True,
            security_passed=security,
            regression_passed=regression,
            verification_passed=verification,
        )

        assert not result.allowed
        assert result.decision == ImprovementDecision.REQUIRE_VERIFICATION

    # No self-authorization or Mother bypass.
    for operation in (
        ImprovementOperation.SELF_AUTHORIZE,
        ImprovementOperation.BYPASS_MOTHER,
        ImprovementOperation.ESCALATE_AUTHORITY,
    ):
        result = boundary.decide(
            ImprovementActor.CHILD_BRAIN,
            operation,
            ImprovementTarget.CHILD_CODE,
        )

        assert not result.allowed
        assert result.decision == ImprovementDecision.DENY

    # Soul and Constitution remain protected.
    assert not boundary.improvement_can_modify_soul()
    assert not boundary.improvement_can_modify_constitution()

    # External actors cannot authorize upgrades.
    for actor in (
        ImprovementActor.SOFTWARE,
        ImprovementActor.TOOL,
        ImprovementActor.EXTERNAL_MODEL,
    ):
        result = boundary.decide(
            actor,
            ImprovementOperation.APPLY_UPGRADE,
            ImprovementTarget.CHILD_CODE,
            mother_approved=True,
            security_passed=True,
            regression_passed=True,
            verification_passed=True,
        )

        assert not result.allowed
        assert not result.upgrade_authorized

    # Constitutional guarantees.
    assert boundary.child_can_detect_weakness()
    assert boundary.child_can_design_improvement()
    assert boundary.child_can_improve_own_code()
    assert boundary.child_can_improve_internal_army()
    assert boundary.child_can_improve_internal_labor()

    assert boundary.every_actual_upgrade_requires_mother()
    assert boundary.security_test_required()
    assert boundary.regression_test_required()
    assert boundary.verification_required()

    assert not boundary.child_can_self_authorize_upgrade()
    assert not boundary.child_can_bypass_mother()
    assert not boundary.improvement_can_escalate_authority()
    assert not boundary.capability_growth_creates_authority()
    assert not boundary.external_actor_can_authorize_upgrade()
    assert boundary.failed_verification_blocks_upgrade()

    # This boundary never creates or activates a real Child.
    assert not boundary.creates_real_child()
    assert not boundary.activates_real_child()
    assert not boundary.executes_upgrade()

    print("SAHIBEX CHILD SELF-IMPROVEMENT BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
