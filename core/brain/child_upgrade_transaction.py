from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class UpgradeStage(str, Enum):
    PREPARE = "prepare"
    VALIDATE = "validate"
    SANDBOX = "sandbox"
    APPLY = "apply"
    POST_VERIFY = "post_verify"
    COMMIT = "commit"
    ROLLBACK = "rollback"
    ABORTED = "aborted"


class UpgradeDecision(str, Enum):
    READY = "ready"
    BLOCK = "block"
    COMMIT = "commit"
    ROLLBACK = "rollback"


@dataclass(frozen=True)
class UpgradeTransaction:
    transaction_id: str
    proposal_id: str
    child_brain_id: str
    stage: UpgradeStage
    mother_approved: bool
    security_passed: bool
    regression_passed: bool
    verification_passed: bool
    sandbox_passed: bool
    post_verification_passed: bool
    rollback_available: bool
    committed: bool


@dataclass(frozen=True)
class UpgradeTransactionResult:
    decision: UpgradeDecision
    transaction: UpgradeTransaction
    reason: str


class ChildUpgradeTransaction:
    """
    Atomic and permission-gated Child upgrade transaction boundary.

    This layer:
    - accepts only an approved improvement proposal
    - requires security/regression/verification gates
    - requires sandbox validation
    - supports rollback
    - requires post-upgrade verification
    - commits only after every gate passes
    - never changes soul or constitution
    - never grants authority
    """

    VERSION = "1.0"

    def __init__(self) -> None:
        self._transactions: dict[str, UpgradeTransaction] = {}

    def prepare(
        self,
        proposal_id: str,
        child_brain_id: str,
        mother_approved: bool,
        security_passed: bool,
        regression_passed: bool,
        verification_passed: bool,
    ) -> UpgradeTransactionResult:
        transaction = UpgradeTransaction(
            transaction_id=f"upgrade-{uuid4()}",
            proposal_id=proposal_id,
            child_brain_id=child_brain_id,
            stage=UpgradeStage.PREPARE,
            mother_approved=mother_approved,
            security_passed=security_passed,
            regression_passed=regression_passed,
            verification_passed=verification_passed,
            sandbox_passed=False,
            post_verification_passed=False,
            rollback_available=True,
            committed=False,
        )

        self._transactions[transaction.transaction_id] = transaction

        if not mother_approved:
            return self._result(
                UpgradeDecision.BLOCK,
                transaction,
                "Mother approval is required",
            )

        if not security_passed:
            return self._result(
                UpgradeDecision.BLOCK,
                transaction,
                "Security verification failed",
            )

        if not regression_passed:
            return self._result(
                UpgradeDecision.BLOCK,
                transaction,
                "Regression verification failed",
            )

        if not verification_passed:
            return self._result(
                UpgradeDecision.BLOCK,
                transaction,
                "Upgrade verification failed",
            )

        return self._result(
            UpgradeDecision.READY,
            transaction,
            "Upgrade transaction prepared",
        )

    def validate(self, transaction_id: str) -> UpgradeTransactionResult:
        transaction = self._get(transaction_id)

        if not self._all_preconditions_pass(transaction):
            return self._result(
                UpgradeDecision.BLOCK,
                transaction,
                "Upgrade preconditions failed",
            )

        updated = self._replace(
            transaction,
            stage=UpgradeStage.VALIDATE,
        )

        return self._result(
            UpgradeDecision.READY,
            updated,
            "Upgrade transaction validated",
        )

    def sandbox(
        self,
        transaction_id: str,
        sandbox_passed: bool,
    ) -> UpgradeTransactionResult:
        transaction = self._get(transaction_id)

        if transaction.stage != UpgradeStage.VALIDATE:
            return self._result(
                UpgradeDecision.BLOCK,
                transaction,
                "Transaction must be validated before sandbox",
            )

        if not sandbox_passed:
            updated = self._replace(
                transaction,
                stage=UpgradeStage.ABORTED,
                sandbox_passed=False,
            )

            return self._result(
                UpgradeDecision.BLOCK,
                updated,
                "Sandbox validation failed",
            )

        updated = self._replace(
            transaction,
            stage=UpgradeStage.SANDBOX,
            sandbox_passed=True,
        )

        return self._result(
            UpgradeDecision.READY,
            updated,
            "Sandbox validation passed",
        )

    def apply(self, transaction_id: str) -> UpgradeTransactionResult:
        transaction = self._get(transaction_id)

        if transaction.stage != UpgradeStage.SANDBOX:
            return self._result(
                UpgradeDecision.BLOCK,
                transaction,
                "Sandbox must pass before apply",
            )

        if not transaction.rollback_available:
            return self._result(
                UpgradeDecision.BLOCK,
                transaction,
                "Rollback protection is required",
            )

        updated = self._replace(
            transaction,
            stage=UpgradeStage.APPLY,
        )

        return self._result(
            UpgradeDecision.READY,
            updated,
            "Upgrade may enter controlled apply stage",
        )

    def post_verify(
        self,
        transaction_id: str,
        post_verification_passed: bool,
    ) -> UpgradeTransactionResult:
        transaction = self._get(transaction_id)

        if transaction.stage != UpgradeStage.APPLY:
            return self._result(
                UpgradeDecision.BLOCK,
                transaction,
                "Apply stage is required before post-verification",
            )

        if not post_verification_passed:
            updated = self._replace(
                transaction,
                stage=UpgradeStage.ROLLBACK,
                post_verification_passed=False,
            )

            return self._result(
                UpgradeDecision.ROLLBACK,
                updated,
                "Post-verification failed; rollback required",
            )

        updated = self._replace(
            transaction,
            stage=UpgradeStage.POST_VERIFY,
            post_verification_passed=True,
        )

        return self._result(
            UpgradeDecision.READY,
            updated,
            "Post-upgrade verification passed",
        )

    def commit(self, transaction_id: str) -> UpgradeTransactionResult:
        transaction = self._get(transaction_id)

        if transaction.stage != UpgradeStage.POST_VERIFY:
            return self._result(
                UpgradeDecision.BLOCK,
                transaction,
                "Post-verification is required before commit",
            )

        if not self._all_commit_gates_pass(transaction):
            return self._result(
                UpgradeDecision.BLOCK,
                transaction,
                "Commit gates failed",
            )

        updated = self._replace(
            transaction,
            stage=UpgradeStage.COMMIT,
            committed=True,
        )

        return self._result(
            UpgradeDecision.COMMIT,
            updated,
            "Upgrade transaction committed",
        )

    def rollback(self, transaction_id: str) -> UpgradeTransactionResult:
        transaction = self._get(transaction_id)

        if not transaction.rollback_available:
            return self._result(
                UpgradeDecision.BLOCK,
                transaction,
                "Rollback is unavailable",
            )

        updated = self._replace(
            transaction,
            stage=UpgradeStage.ROLLBACK,
            committed=False,
        )

        return self._result(
            UpgradeDecision.ROLLBACK,
            updated,
            "Upgrade transaction rolled back",
        )

    def can_modify_soul(self) -> bool:
        return False

    def can_modify_constitution(self) -> bool:
        return False

    def can_escalate_authority(self) -> bool:
        return False

    def can_bypass_mother(self) -> bool:
        return False

    def requires_mother_approval(self) -> bool:
        return True

    def requires_sandbox(self) -> bool:
        return True

    def requires_post_verification(self) -> bool:
        return True

    def requires_rollback_protection(self) -> bool:
        return True

    def atomic_commit_required(self) -> bool:
        return True

    def creates_real_child(self) -> bool:
        return False

    def activates_real_child(self) -> bool:
        return False

    def _all_preconditions_pass(
        self,
        transaction: UpgradeTransaction,
    ) -> bool:
        return (
            transaction.mother_approved
            and transaction.security_passed
            and transaction.regression_passed
            and transaction.verification_passed
        )

    def _all_commit_gates_pass(
        self,
        transaction: UpgradeTransaction,
    ) -> bool:
        return (
            self._all_preconditions_pass(transaction)
            and transaction.sandbox_passed
            and transaction.post_verification_passed
            and transaction.rollback_available
        )

    def _get(self, transaction_id: str) -> UpgradeTransaction:
        try:
            return self._transactions[transaction_id]
        except KeyError as exc:
            raise ValueError("unknown upgrade transaction") from exc

    def _replace(
        self,
        transaction: UpgradeTransaction,
        **changes: object,
    ) -> UpgradeTransaction:
        values = {
            "transaction_id": transaction.transaction_id,
            "proposal_id": transaction.proposal_id,
            "child_brain_id": transaction.child_brain_id,
            "stage": transaction.stage,
            "mother_approved": transaction.mother_approved,
            "security_passed": transaction.security_passed,
            "regression_passed": transaction.regression_passed,
            "verification_passed": transaction.verification_passed,
            "sandbox_passed": transaction.sandbox_passed,
            "post_verification_passed": transaction.post_verification_passed,
            "rollback_available": transaction.rollback_available,
            "committed": transaction.committed,
        }

        values.update(changes)

        updated = UpgradeTransaction(**values)
        self._transactions[updated.transaction_id] = updated
        return updated

    def _result(
        self,
        decision: UpgradeDecision,
        transaction: UpgradeTransaction,
        reason: str,
    ) -> UpgradeTransactionResult:
        self._transactions[transaction.transaction_id] = transaction
        return UpgradeTransactionResult(
            decision=decision,
            transaction=transaction,
            reason=reason,
        )


if __name__ == "__main__":
    engine = ChildUpgradeTransaction()

    prepared = engine.prepare(
        proposal_id="improvement-demo",
        child_brain_id="child-demo",
        mother_approved=True,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
    )

    assert prepared.decision == UpgradeDecision.READY

    validated = engine.validate(
        prepared.transaction.transaction_id,
    )

    assert validated.decision == UpgradeDecision.READY

    sandboxed = engine.sandbox(
        prepared.transaction.transaction_id,
        sandbox_passed=True,
    )

    assert sandboxed.decision == UpgradeDecision.READY

    applied = engine.apply(
        prepared.transaction.transaction_id,
    )

    assert applied.decision == UpgradeDecision.READY

    verified = engine.post_verify(
        prepared.transaction.transaction_id,
        post_verification_passed=True,
    )

    assert verified.decision == UpgradeDecision.READY

    committed = engine.commit(
        prepared.transaction.transaction_id,
    )

    assert committed.decision == UpgradeDecision.COMMIT

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

    print("SAHIBEX CHILD UPGRADE TRANSACTION TEST: PASS")
