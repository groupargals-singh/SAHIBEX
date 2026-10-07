from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RecoveryDecision(str, Enum):
    RECOVER = "recover"
    BLOCK = "block"


class FailureType(str, Enum):
    SECURITY = "security"
    VERIFICATION = "verification"
    INTEGRITY = "integrity"
    REGRESSION = "regression"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RecoveryRequest:
    recovery_id: str
    child_brain_id: str
    failed_transaction_id: str
    failure_type: FailureType
    failure_detected: bool
    safe_state_entered: bool
    trusted_recovery_point: bool
    mother_approved: bool
    integrity_verified: bool
    restoration_verified: bool
    audit_complete: bool


@dataclass(frozen=True)
class RecoveryResult:
    decision: RecoveryDecision
    reason: str
    recovery_allowed: bool
    execution_performed: bool


class ChildSelfImprovementRecoveryIntegration:
    """
    Failure and recovery integration boundary.

    This layer validates whether recovery may proceed.
    It does not perform live rollback or arbitrary execution.
    """

    VERSION = "1.0"

    def evaluate(
        self,
        request: RecoveryRequest,
    ) -> RecoveryResult:

        failures: list[str] = []

        required_ids = {
            "recovery_id": request.recovery_id,
            "child_brain_id": request.child_brain_id,
            "failed_transaction_id": request.failed_transaction_id,
        }

        for field_name, value in required_ids.items():
            if not value:
                failures.append(f"{field_name} missing")

        if not request.failure_detected:
            failures.append("failure not detected")

        if not request.safe_state_entered:
            failures.append("safe state not entered")

        if not request.trusted_recovery_point:
            failures.append("trusted recovery point unavailable")

        if not request.mother_approved:
            failures.append("mother approval missing")

        if not request.integrity_verified:
            failures.append("integrity verification failed")

        if not request.restoration_verified:
            failures.append("restoration verification failed")

        if not request.audit_complete:
            failures.append("recovery audit incomplete")

        if failures:
            return RecoveryResult(
                decision=RecoveryDecision.BLOCK,
                reason="; ".join(failures),
                recovery_allowed=False,
                execution_performed=False,
            )

        return RecoveryResult(
            decision=RecoveryDecision.RECOVER,
            reason="recovery gates passed",
            recovery_allowed=True,
            execution_performed=False,
        )

    def requires_safe_state(self) -> bool:
        return True

    def requires_trusted_recovery_point(self) -> bool:
        return True

    def requires_mother_approval(self) -> bool:
        return True

    def requires_integrity_verification(self) -> bool:
        return True

    def requires_restoration_verification(self) -> bool:
        return True

    def recovery_failure_blocks_completion(self) -> bool:
        return True

    def execution_performed(self) -> bool:
        return False

    def modifies_soul(self) -> bool:
        return False

    def modifies_constitution(self) -> bool:
        return False

    def grants_authority(self) -> bool:
        return False

    def creates_real_child(self) -> bool:
        return False

    def activates_real_child(self) -> bool:
        return False


if __name__ == "__main__":
    recovery = ChildSelfImprovementRecoveryIntegration()

    request = RecoveryRequest(
        recovery_id="recovery-001",
        child_brain_id="child-001",
        failed_transaction_id="transaction-001",
        failure_type=FailureType.VERIFICATION,
        failure_detected=True,
        safe_state_entered=True,
        trusted_recovery_point=True,
        mother_approved=True,
        integrity_verified=True,
        restoration_verified=True,
        audit_complete=True,
    )

    result = recovery.evaluate(request)

    assert result.decision == RecoveryDecision.RECOVER
    assert result.recovery_allowed is True
    assert result.execution_performed is False

    assert recovery.requires_safe_state() is True
    assert recovery.requires_trusted_recovery_point() is True
    assert recovery.requires_mother_approval() is True
    assert recovery.requires_integrity_verification() is True
    assert recovery.requires_restoration_verification() is True
    assert recovery.recovery_failure_blocks_completion() is True

    assert recovery.execution_performed() is False
    assert recovery.modifies_soul() is False
    assert recovery.modifies_constitution() is False
    assert recovery.grants_authority() is False
    assert recovery.creates_real_child() is False
    assert recovery.activates_real_child() is False

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT RECOVERY INTEGRATION TEST: PASS"
    )
