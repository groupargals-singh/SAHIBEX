from core.brain.child_upgrade_recovery_registry import (
    ChildUpgradeRecoveryRegistry,
    RecoveryDecision,
    RecoveryStage,
)


def make_registry_and_point():
    registry = ChildUpgradeRecoveryRegistry()

    point = registry.register_recovery_point(
        child_brain_id="child-001",
        version="1.0",
        integrity="trusted-hash-1",
        source_transaction_id="upgrade-000",
        audit_reference="audit-000",
        trusted=True,
    )

    return registry, point


def make_authorized_recovery():
    registry, point = make_registry_and_point()

    result = registry.start_recovery(
        child_brain_id="child-001",
        failed_transaction_id="upgrade-001",
        recovery_point_id=point.recovery_point_id,
        mother_approved=True,
    )

    assert result.decision == RecoveryDecision.READY

    return registry, result.transaction.recovery_id


def test_full_recovery_flow() -> None:
    registry, recovery_id = make_authorized_recovery()

    result = registry.verify_recovery_integrity(
        recovery_id,
        current_integrity_matches=True,
    )
    assert result.decision == RecoveryDecision.READY

    result = registry.restore(recovery_id)
    assert result.decision == RecoveryDecision.READY
    assert result.transaction.stage == RecoveryStage.RESTORING

    result = registry.verify_restoration(
        recovery_id,
        restoration_verified=True,
    )
    assert result.decision == RecoveryDecision.READY
    assert result.transaction.stage == RecoveryStage.VERIFIED

    result = registry.commit_recovery(recovery_id)

    assert result.decision == RecoveryDecision.RECOVER
    assert result.transaction.committed is True
    assert result.transaction.stage == RecoveryStage.RECOVERED


def test_unapproved_recovery_is_blocked() -> None:
    registry, point = make_registry_and_point()

    result = registry.start_recovery(
        child_brain_id="child-001",
        failed_transaction_id="upgrade-002",
        recovery_point_id=point.recovery_point_id,
        mother_approved=False,
    )

    assert result.decision == RecoveryDecision.BLOCK


def test_untrusted_recovery_point_is_rejected() -> None:
    registry = ChildUpgradeRecoveryRegistry()

    try:
        registry.register_recovery_point(
            child_brain_id="child-001",
            version="1.0",
            integrity="hash",
            source_transaction_id="upgrade-000",
            audit_reference="audit-000",
            trusted=False,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "untrusted recovery point must be rejected"
        )


def test_integrity_failure_blocks_recovery() -> None:
    registry, recovery_id = make_authorized_recovery()

    result = registry.verify_recovery_integrity(
        recovery_id,
        current_integrity_matches=False,
    )

    assert result.decision == RecoveryDecision.FAILED
    assert result.transaction.stage == RecoveryStage.FAILED


def test_restoration_failure_blocks_commit() -> None:
    registry, recovery_id = make_authorized_recovery()

    registry.verify_recovery_integrity(
        recovery_id,
        current_integrity_matches=True,
    )

    registry.restore(recovery_id)

    result = registry.verify_restoration(
        recovery_id,
        restoration_verified=False,
    )

    assert result.decision == RecoveryDecision.FAILED
    assert result.transaction.committed is False


def test_security_boundaries() -> None:
    registry = ChildUpgradeRecoveryRegistry()

    assert registry.recovery_read_grants_authority() is False
    assert registry.unknown_state_is_recoverable() is False
    assert registry.untrusted_state_is_recoverable() is False
    assert registry.bypass_mother_is_allowed() is False
    assert registry.can_modify_soul() is False
    assert registry.can_modify_constitution() is False
    assert registry.can_escalate_authority() is False
    assert registry.executes_arbitrary_commands() is False
    assert registry.creates_real_child() is False
    assert registry.activates_real_child() is False


if __name__ == "__main__":
    test_full_recovery_flow()
    test_unapproved_recovery_is_blocked()
    test_untrusted_recovery_point_is_rejected()
    test_integrity_failure_blocks_recovery()
    test_restoration_failure_blocks_commit()
    test_security_boundaries()

    print("SAHIBEX CHILD UPGRADE RECOVERY & ROLLBACK TEST: PASS")
