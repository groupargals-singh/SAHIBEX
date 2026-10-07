from core.brain.child_failure_recovery_boundary import (
    ChildFailureRecoveryBoundary,
    FailureSeverity,
    FailureType,
    RecoveryActor,
    RecoveryDecision,
    RecoveryOperation,
)


def main() -> None:
    boundary = ChildFailureRecoveryBoundary

    # Failure reporting does not grant authority.
    result = boundary.decide(
        RecoveryActor.CHILD_BRAIN,
        RecoveryOperation.REPORT_FAILURE,
        FailureSeverity.MAJOR,
        FailureType.SOFTWARE,
    )

    assert result.allowed
    assert result.decision == RecoveryDecision.ALLOW_REPORT
    assert not result.authority_granted

    # Diagnosis does not grant authority.
    result = boundary.decide(
        RecoveryActor.CHILD_BRAIN,
        RecoveryOperation.DIAGNOSE,
        FailureSeverity.MAJOR,
        FailureType.SOFTWARE,
    )

    assert result.allowed
    assert not result.authority_granted

    # Critical/security failure requires safe state.
    result = boundary.decide(
        RecoveryActor.CHILD_BRAIN,
        RecoveryOperation.REPORT_FAILURE,
        FailureSeverity.CRITICAL,
        FailureType.SECURITY,
    )

    assert result.allowed
    assert result.safe_state_required

    # Mother controls containment.
    result = boundary.decide(
        RecoveryActor.SAHIBEX_MOTHER,
        RecoveryOperation.CONTAIN,
        FailureSeverity.CRITICAL,
        FailureType.SECURITY,
        mother_approved=False,
    )

    assert not result.allowed
    assert result.decision == RecoveryDecision.REQUIRE_MOTHER_AUTHORITY

    result = boundary.decide(
        RecoveryActor.SAHIBEX_MOTHER,
        RecoveryOperation.CONTAIN,
        FailureSeverity.CRITICAL,
        FailureType.SECURITY,
        mother_approved=True,
    )

    assert result.allowed
    assert result.authority_granted
    assert result.safe_state_required

    # Verification requires containment.
    result = boundary.decide(
        RecoveryActor.SAHIBEX_MOTHER,
        RecoveryOperation.VERIFY_RECOVERY,
        FailureSeverity.MAJOR,
        FailureType.SOFTWARE,
        containment_active=False,
        verification_passed=True,
    )

    assert not result.allowed
    assert result.decision == RecoveryDecision.REQUIRE_VERIFICATION

    result = boundary.decide(
        RecoveryActor.SAHIBEX_MOTHER,
        RecoveryOperation.VERIFY_RECOVERY,
        FailureSeverity.MAJOR,
        FailureType.SOFTWARE,
        containment_active=True,
        verification_passed=True,
    )

    assert result.allowed
    assert not result.authority_granted

    # Human is required to complete recovery.
    result = boundary.decide(
        RecoveryActor.HUMAN,
        RecoveryOperation.COMPLETE_RECOVERY,
        FailureSeverity.MAJOR,
        FailureType.SOFTWARE,
        human_approved=True,
        verification_passed=True,
        containment_active=True,
    )

    assert result.allowed
    assert result.authority_granted

    # Failed verification blocks completion.
    result = boundary.decide(
        RecoveryActor.HUMAN,
        RecoveryOperation.COMPLETE_RECOVERY,
        FailureSeverity.MAJOR,
        FailureType.SOFTWARE,
        human_approved=True,
        verification_passed=False,
        containment_active=True,
    )

    assert not result.allowed
    assert result.decision == RecoveryDecision.REQUIRE_VERIFICATION

    # Unknown failure fails closed.
    result = boundary.decide(
        RecoveryActor.CHILD_ARMY,
        RecoveryOperation.ENTER_RECOVERY,
        FailureSeverity.UNKNOWN,
        FailureType.UNKNOWN,
        mother_approved=False,
    )

    assert not result.allowed
    assert result.safe_state_required

    # Forbidden recovery shortcuts.
    for operation in (
        RecoveryOperation.BYPASS_CONTAINMENT,
        RecoveryOperation.BYPASS_VERIFICATION,
        RecoveryOperation.MODIFY_SOUL,
        RecoveryOperation.MODIFY_CONSTITUTION,
        RecoveryOperation.SELF_AUTHORIZE_RECOVERY,
    ):
        result = boundary.decide(
            RecoveryActor.CHILD_BRAIN,
            operation,
        )

        assert not result.allowed
        assert result.decision == RecoveryDecision.DENY

    # Constitutional guarantees.
    assert not boundary.child_can_self_authorize_recovery()
    assert not boundary.army_can_control_recovery()
    assert not boundary.labor_can_control_recovery()

    assert not boundary.failure_creates_authority()
    assert not boundary.recovery_creates_constitutional_authority()
    assert not boundary.recovery_can_modify_soul()
    assert not boundary.recovery_can_modify_constitution()

    assert boundary.recovery_requires_verification()
    assert boundary.security_failure_requires_containment()
    assert boundary.unknown_failure_fails_closed()
    assert boundary.recovery_completion_requires_human()

    assert not boundary.creates_real_child()
    assert not boundary.activates_real_child()
    assert not boundary.executes_child_actions()

    print("SAHIBEX CHILD FAILURE & RECOVERY BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
