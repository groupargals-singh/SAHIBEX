from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class RecoveryStage(str, Enum):
    DETECTED = "detected"
    IDENTIFIED = "identified"
    AUTHORIZED = "authorized"
    RESTORING = "restoring"
    VERIFIED = "verified"
    RECOVERED = "recovered"
    FAILED = "failed"
    BLOCKED = "blocked"


class RecoveryDecision(str, Enum):
    READY = "ready"
    BLOCK = "block"
    RECOVER = "recover"
    FAILED = "failed"


@dataclass(frozen=True)
class RecoveryPoint:
    recovery_point_id: str
    child_brain_id: str
    version: str
    integrity: str
    source_transaction_id: str
    audit_reference: str
    trusted: bool


@dataclass(frozen=True)
class RecoveryTransaction:
    recovery_id: str
    child_brain_id: str
    failed_transaction_id: str
    recovery_point_id: str
    stage: RecoveryStage
    mother_approved: bool
    integrity_verified: bool
    restoration_verified: bool
    committed: bool
    immutable: bool


@dataclass(frozen=True)
class RecoveryResult:
    decision: RecoveryDecision
    transaction: RecoveryTransaction
    reason: str


class ChildUpgradeRecoveryRegistry:
    """
    Recovery and rollback registry for Child upgrades.

    This layer:
    - registers verified recovery points
    - identifies the last trusted state
    - requires Mother authorization
    - requires integrity verification
    - requires restoration verification
    - prevents rollback to unknown/untrusted states
    - records immutable recovery transactions
    - never modifies soul or constitution
    - never grants authority
    - never executes arbitrary commands
    """

    VERSION = "1.0"

    def __init__(self) -> None:
        self._points: dict[str, RecoveryPoint] = {}
        self._transactions: dict[str, RecoveryTransaction] = {}

    def register_recovery_point(
        self,
        child_brain_id: str,
        version: str,
        integrity: str,
        source_transaction_id: str,
        audit_reference: str,
        trusted: bool,
    ) -> RecoveryPoint:
        if not child_brain_id.strip():
            raise ValueError("child_brain_id is required")

        if not version.strip():
            raise ValueError("version is required")

        if not integrity.strip():
            raise ValueError("integrity is required")

        if not source_transaction_id.strip():
            raise ValueError("source_transaction_id is required")

        if not audit_reference.strip():
            raise ValueError("audit_reference is required")

        if not trusted:
            raise ValueError(
                "only trusted states can become recovery points"
            )

        point = RecoveryPoint(
            recovery_point_id=f"recovery-point-{uuid4()}",
            child_brain_id=child_brain_id,
            version=version,
            integrity=integrity,
            source_transaction_id=source_transaction_id,
            audit_reference=audit_reference,
            trusted=True,
        )

        self._points[point.recovery_point_id] = point
        return point

    def start_recovery(
        self,
        child_brain_id: str,
        failed_transaction_id: str,
        recovery_point_id: str,
        mother_approved: bool,
    ) -> RecoveryResult:
        point = self._get_point(recovery_point_id)

        transaction = RecoveryTransaction(
            recovery_id=f"recovery-{uuid4()}",
            child_brain_id=child_brain_id,
            failed_transaction_id=failed_transaction_id,
            recovery_point_id=recovery_point_id,
            stage=RecoveryStage.DETECTED,
            mother_approved=mother_approved,
            integrity_verified=False,
            restoration_verified=False,
            committed=False,
            immutable=True,
        )

        self._transactions[transaction.recovery_id] = transaction

        if point.child_brain_id != child_brain_id:
            return self._result(
                RecoveryDecision.BLOCK,
                transaction,
                "recovery point belongs to another Child Brain",
            )

        if not point.trusted:
            return self._result(
                RecoveryDecision.BLOCK,
                transaction,
                "untrusted recovery point",
            )

        if not mother_approved:
            return self._result(
                RecoveryDecision.BLOCK,
                transaction,
                "Mother approval is required",
            )

        updated = self._replace(
            transaction,
            stage=RecoveryStage.AUTHORIZED,
        )

        return self._result(
            RecoveryDecision.READY,
            updated,
            "recovery authorized",
        )

    def verify_recovery_integrity(
        self,
        recovery_id: str,
        current_integrity_matches: bool,
    ) -> RecoveryResult:
        transaction = self._get_transaction(recovery_id)

        if transaction.stage != RecoveryStage.AUTHORIZED:
            return self._result(
                RecoveryDecision.BLOCK,
                transaction,
                "recovery must be authorized first",
            )

        if not current_integrity_matches:
            updated = self._replace(
                transaction,
                stage=RecoveryStage.FAILED,
                integrity_verified=False,
            )

            return self._result(
                RecoveryDecision.FAILED,
                updated,
                "recovery point integrity verification failed",
            )

        updated = self._replace(
            transaction,
            stage=RecoveryStage.IDENTIFIED,
            integrity_verified=True,
        )

        return self._result(
            RecoveryDecision.READY,
            updated,
            "recovery point integrity verified",
        )

    def restore(
        self,
        recovery_id: str,
    ) -> RecoveryResult:
        transaction = self._get_transaction(recovery_id)

        if transaction.stage != RecoveryStage.IDENTIFIED:
            return self._result(
                RecoveryDecision.BLOCK,
                transaction,
                "verified recovery point is required",
            )

        if not transaction.integrity_verified:
            return self._result(
                RecoveryDecision.BLOCK,
                transaction,
                "integrity must be verified before restoration",
            )

        updated = self._replace(
            transaction,
            stage=RecoveryStage.RESTORING,
        )

        return self._result(
            RecoveryDecision.READY,
            updated,
            "controlled restoration stage entered",
        )

    def verify_restoration(
        self,
        recovery_id: str,
        restoration_verified: bool,
    ) -> RecoveryResult:
        transaction = self._get_transaction(recovery_id)

        if transaction.stage != RecoveryStage.RESTORING:
            return self._result(
                RecoveryDecision.BLOCK,
                transaction,
                "restoration stage is required",
            )

        if not restoration_verified:
            updated = self._replace(
                transaction,
                stage=RecoveryStage.FAILED,
                restoration_verified=False,
                committed=False,
            )

            return self._result(
                RecoveryDecision.FAILED,
                updated,
                "restoration verification failed",
            )

        updated = self._replace(
            transaction,
            stage=RecoveryStage.VERIFIED,
            restoration_verified=True,
        )

        return self._result(
            RecoveryDecision.READY,
            updated,
            "restoration verified",
        )

    def commit_recovery(
        self,
        recovery_id: str,
    ) -> RecoveryResult:
        transaction = self._get_transaction(recovery_id)

        if transaction.stage != RecoveryStage.VERIFIED:
            return self._result(
                RecoveryDecision.BLOCK,
                transaction,
                "verified restoration is required before recovery commit",
            )

        if not transaction.mother_approved:
            return self._result(
                RecoveryDecision.BLOCK,
                transaction,
                "Mother approval is required",
            )

        if not transaction.integrity_verified:
            return self._result(
                RecoveryDecision.BLOCK,
                transaction,
                "recovery integrity is not verified",
            )

        if not transaction.restoration_verified:
            return self._result(
                RecoveryDecision.BLOCK,
                transaction,
                "restoration is not verified",
            )

        updated = self._replace(
            transaction,
            stage=RecoveryStage.RECOVERED,
            committed=True,
        )

        return self._result(
            RecoveryDecision.RECOVER,
            updated,
            "recovery committed",
        )

    def get_recovery_point(
        self,
        recovery_point_id: str,
    ) -> RecoveryPoint:
        return self._get_point(recovery_point_id)

    def get_recovery(
        self,
        recovery_id: str,
    ) -> RecoveryTransaction:
        return self._get_transaction(recovery_id)

    def recovery_read_grants_authority(self) -> bool:
        return False

    def unknown_state_is_recoverable(self) -> bool:
        return False

    def untrusted_state_is_recoverable(self) -> bool:
        return False

    def bypass_mother_is_allowed(self) -> bool:
        return False

    def can_modify_soul(self) -> bool:
        return False

    def can_modify_constitution(self) -> bool:
        return False

    def can_escalate_authority(self) -> bool:
        return False

    def executes_arbitrary_commands(self) -> bool:
        return False

    def creates_real_child(self) -> bool:
        return False

    def activates_real_child(self) -> bool:
        return False

    def _get_point(
        self,
        recovery_point_id: str,
    ) -> RecoveryPoint:
        try:
            return self._points[recovery_point_id]
        except KeyError as exc:
            raise ValueError("unknown recovery point") from exc

    def _get_transaction(
        self,
        recovery_id: str,
    ) -> RecoveryTransaction:
        try:
            return self._transactions[recovery_id]
        except KeyError as exc:
            raise ValueError("unknown recovery transaction") from exc

    def _replace(
        self,
        transaction: RecoveryTransaction,
        **changes: object,
    ) -> RecoveryTransaction:
        values = {
            "recovery_id": transaction.recovery_id,
            "child_brain_id": transaction.child_brain_id,
            "failed_transaction_id": transaction.failed_transaction_id,
            "recovery_point_id": transaction.recovery_point_id,
            "stage": transaction.stage,
            "mother_approved": transaction.mother_approved,
            "integrity_verified": transaction.integrity_verified,
            "restoration_verified": transaction.restoration_verified,
            "committed": transaction.committed,
            "immutable": transaction.immutable,
        }

        values.update(changes)

        updated = RecoveryTransaction(**values)
        self._transactions[updated.recovery_id] = updated
        return updated

    def _result(
        self,
        decision: RecoveryDecision,
        transaction: RecoveryTransaction,
        reason: str,
    ) -> RecoveryResult:
        self._transactions[transaction.recovery_id] = transaction

        return RecoveryResult(
            decision=decision,
            transaction=transaction,
            reason=reason,
        )


if __name__ == "__main__":
    registry = ChildUpgradeRecoveryRegistry()

    point = registry.register_recovery_point(
        child_brain_id="child-001",
        version="1.0",
        integrity="trusted-hash-1",
        source_transaction_id="upgrade-000",
        audit_reference="audit-000",
        trusted=True,
    )

    started = registry.start_recovery(
        child_brain_id="child-001",
        failed_transaction_id="upgrade-001",
        recovery_point_id=point.recovery_point_id,
        mother_approved=True,
    )

    assert started.decision == RecoveryDecision.READY

    recovery_id = started.transaction.recovery_id

    integrity = registry.verify_recovery_integrity(
        recovery_id,
        current_integrity_matches=True,
    )

    assert integrity.decision == RecoveryDecision.READY

    restored = registry.restore(recovery_id)

    assert restored.decision == RecoveryDecision.READY

    verified = registry.verify_restoration(
        recovery_id,
        restoration_verified=True,
    )

    assert verified.decision == RecoveryDecision.READY

    recovered = registry.commit_recovery(recovery_id)

    assert recovered.decision == RecoveryDecision.RECOVER
    assert recovered.transaction.committed is True
    assert recovered.transaction.stage == RecoveryStage.RECOVERED

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

    print("SAHIBEX CHILD UPGRADE RECOVERY & ROLLBACK TEST: PASS")
