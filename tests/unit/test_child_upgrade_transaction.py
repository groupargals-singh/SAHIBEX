from core.brain.child_upgrade_transaction import (
    ChildUpgradeTransaction,
    UpgradeDecision,
    UpgradeStage,
)


def make_ready_transaction() -> tuple[
    ChildUpgradeTransaction,
    str,
]:
    engine = ChildUpgradeTransaction()

    result = engine.prepare(
        proposal_id="proposal-001",
        child_brain_id="child-001",
        mother_approved=True,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
    )

    assert result.decision == UpgradeDecision.READY

    return engine, result.transaction.transaction_id


def test_full_upgrade_transaction() -> None:
    engine, transaction_id = make_ready_transaction()

    result = engine.validate(transaction_id)
    assert result.decision == UpgradeDecision.READY

    result = engine.sandbox(
        transaction_id,
        sandbox_passed=True,
    )
    assert result.decision == UpgradeDecision.READY
    assert result.transaction.sandbox_passed is True

    result = engine.apply(transaction_id)
    assert result.decision == UpgradeDecision.READY
    assert result.transaction.stage == UpgradeStage.APPLY

    result = engine.post_verify(
        transaction_id,
        post_verification_passed=True,
    )
    assert result.decision == UpgradeDecision.READY

    result = engine.commit(transaction_id)

    assert result.decision == UpgradeDecision.COMMIT
    assert result.transaction.committed is True
    assert result.transaction.stage == UpgradeStage.COMMIT


def test_mother_approval_required() -> None:
    engine = ChildUpgradeTransaction()

    result = engine.prepare(
        proposal_id="proposal-002",
        child_brain_id="child-002",
        mother_approved=False,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
    )

    assert result.decision == UpgradeDecision.BLOCK


def test_failed_sandbox_blocks_upgrade() -> None:
    engine, transaction_id = make_ready_transaction()

    engine.validate(transaction_id)

    result = engine.sandbox(
        transaction_id,
        sandbox_passed=False,
    )

    assert result.decision == UpgradeDecision.BLOCK
    assert result.transaction.stage == UpgradeStage.ABORTED


def test_failed_post_verification_requires_rollback() -> None:
    engine, transaction_id = make_ready_transaction()

    engine.validate(transaction_id)
    engine.sandbox(transaction_id, sandbox_passed=True)
    engine.apply(transaction_id)

    result = engine.post_verify(
        transaction_id,
        post_verification_passed=False,
    )

    assert result.decision == UpgradeDecision.ROLLBACK
    assert result.transaction.stage == UpgradeStage.ROLLBACK
    assert result.transaction.committed is False


def test_commit_without_post_verification_is_blocked() -> None:
    engine, transaction_id = make_ready_transaction()

    engine.validate(transaction_id)
    engine.sandbox(transaction_id, sandbox_passed=True)
    engine.apply(transaction_id)

    result = engine.commit(transaction_id)

    assert result.decision == UpgradeDecision.BLOCK
    assert result.transaction.committed is False


def test_security_invariants() -> None:
    engine = ChildUpgradeTransaction()

    assert engine.can_modify_soul() is False
    assert engine.can_modify_constitution() is False
    assert engine.can_escalate_authority() is False
    assert engine.can_bypass_mother() is False
    assert engine.requires_mother_approval() is True
    assert engine.requires_sandbox() is True
    assert engine.requires_post_verification() is True
    assert engine.requires_rollback_protection() is True
    assert engine.atomic_commit_required() is True
    assert engine.creates_real_child() is False
    assert engine.activates_real_child() is False


if __name__ == "__main__":
    test_full_upgrade_transaction()
    test_mother_approval_required()
    test_failed_sandbox_blocks_upgrade()
    test_failed_post_verification_requires_rollback()
    test_commit_without_post_verification_is_blocked()
    test_security_invariants()

    print("SAHIBEX CHILD UPGRADE TRANSACTION TEST: PASS")
