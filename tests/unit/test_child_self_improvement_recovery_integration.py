from core.brain.child_self_improvement_recovery_integration import (
    ChildSelfImprovementRecoveryIntegration,
    FailureType,
    RecoveryDecision,
    RecoveryRequest,
)


def make_request(**overrides):
    values = {
        "recovery_id": "recovery-001",
        "child_brain_id": "child-001",
        "failed_transaction_id": "transaction-001",
        "failure_type": FailureType.VERIFICATION,
        "failure_detected": True,
        "safe_state_entered": True,
        "trusted_recovery_point": True,
        "mother_approved": True,
        "integrity_verified": True,
        "restoration_verified": True,
        "audit_complete": True,
    }

    values.update(overrides)
    return RecoveryRequest(**values)


def test_valid_recovery():
    recovery = ChildSelfImprovementRecoveryIntegration()

    result = recovery.evaluate(make_request())

    assert result.decision == RecoveryDecision.RECOVER
    assert result.recovery_allowed is True
    assert result.execution_performed is False


def test_missing_recovery_id_blocks():
    recovery = ChildSelfImprovementRecoveryIntegration()

    result = recovery.evaluate(
        make_request(recovery_id="")
    )

    assert result.decision == RecoveryDecision.BLOCK


def test_failure_not_detected_blocks():
    recovery = ChildSelfImprovementRecoveryIntegration()

    result = recovery.evaluate(
        make_request(failure_detected=False)
    )

    assert result.decision == RecoveryDecision.BLOCK


def test_safe_state_required():
    recovery = ChildSelfImprovementRecoveryIntegration()

    result = recovery.evaluate(
        make_request(safe_state_entered=False)
    )

    assert result.decision == RecoveryDecision.BLOCK


def test_untrusted_recovery_point_blocks():
    recovery = ChildSelfImprovementRecoveryIntegration()

    result = recovery.evaluate(
        make_request(trusted_recovery_point=False)
    )

    assert result.decision == RecoveryDecision.BLOCK


def test_mother_approval_required():
    recovery = ChildSelfImprovementRecoveryIntegration()

    result = recovery.evaluate(
        make_request(mother_approved=False)
    )

    assert result.decision == RecoveryDecision.BLOCK


def test_integrity_failure_blocks():
    recovery = ChildSelfImprovementRecoveryIntegration()

    result = recovery.evaluate(
        make_request(integrity_verified=False)
    )

    assert result.decision == RecoveryDecision.BLOCK


def test_restoration_failure_blocks():
    recovery = ChildSelfImprovementRecoveryIntegration()

    result = recovery.evaluate(
        make_request(restoration_verified=False)
    )

    assert result.decision == RecoveryDecision.BLOCK


def test_audit_failure_blocks():
    recovery = ChildSelfImprovementRecoveryIntegration()

    result = recovery.evaluate(
        make_request(audit_complete=False)
    )

    assert result.decision == RecoveryDecision.BLOCK


def test_security_failure_type_supported():
    recovery = ChildSelfImprovementRecoveryIntegration()

    result = recovery.evaluate(
        make_request(failure_type=FailureType.SECURITY)
    )

    assert result.decision == RecoveryDecision.RECOVER


def test_unknown_failure_still_requires_all_gates():
    recovery = ChildSelfImprovementRecoveryIntegration()

    result = recovery.evaluate(
        make_request(failure_type=FailureType.UNKNOWN)
    )

    assert result.decision == RecoveryDecision.RECOVER


def test_safe_recovery_rules():
    recovery = ChildSelfImprovementRecoveryIntegration()

    assert recovery.requires_safe_state() is True
    assert recovery.requires_trusted_recovery_point() is True
    assert recovery.requires_mother_approval() is True
    assert recovery.requires_integrity_verification() is True
    assert recovery.requires_restoration_verification() is True
    assert recovery.recovery_failure_blocks_completion() is True


def test_no_live_execution():
    recovery = ChildSelfImprovementRecoveryIntegration()

    assert recovery.execution_performed() is False


def test_soul_constitution_protected():
    recovery = ChildSelfImprovementRecoveryIntegration()

    assert recovery.modifies_soul() is False
    assert recovery.modifies_constitution() is False


def test_no_authority_grant():
    recovery = ChildSelfImprovementRecoveryIntegration()

    assert recovery.grants_authority() is False


def test_no_child_creation_or_activation():
    recovery = ChildSelfImprovementRecoveryIntegration()

    assert recovery.creates_real_child() is False
    assert recovery.activates_real_child() is False


if __name__ == "__main__":
    test_valid_recovery()
    test_missing_recovery_id_blocks()
    test_failure_not_detected_blocks()
    test_safe_state_required()
    test_untrusted_recovery_point_blocks()
    test_mother_approval_required()
    test_integrity_failure_blocks()
    test_restoration_failure_blocks()
    test_audit_failure_blocks()
    test_security_failure_type_supported()
    test_unknown_failure_still_requires_all_gates()
    test_safe_recovery_rules()
    test_no_live_execution()
    test_soul_constitution_protected()
    test_no_authority_grant()
    test_no_child_creation_or_activation()

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT RECOVERY INTEGRATION TEST: PASS"
    )
