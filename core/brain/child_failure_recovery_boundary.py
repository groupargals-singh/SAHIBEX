from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FailureSeverity(str, Enum):
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class FailureType(str, Enum):
    SOFTWARE = "software"
    RESOURCE = "resource"
    SECURITY = "security"
    VERIFICATION = "verification"
    AUTHORITY = "authority"
    MEMORY = "memory"
    COMMUNICATION = "communication"
    CONSTITUTIONAL = "constitutional"
    UNKNOWN = "unknown"


class RecoveryOperation(str, Enum):
    REPORT_FAILURE = "report_failure"
    CLASSIFY_FAILURE = "classify_failure"
    CONTAIN = "contain"
    ENTER_RECOVERY = "enter_recovery"
    DIAGNOSE = "diagnose"
    ROLLBACK = "rollback"
    RESTORE = "restore"
    VERIFY_RECOVERY = "verify_recovery"
    COMPLETE_RECOVERY = "complete_recovery"

    BYPASS_CONTAINMENT = "bypass_containment"
    BYPASS_VERIFICATION = "bypass_verification"
    MODIFY_SOUL = "modify_soul"
    MODIFY_CONSTITUTION = "modify_constitution"
    SELF_AUTHORIZE_RECOVERY = "self_authorize_recovery"


class RecoveryActor(str, Enum):
    HUMAN = "human"
    SAHIBEX_MOTHER = "sahibex_mother"
    CHILD_BRAIN = "child_brain"
    CHILD_ARMY = "child_army"
    CHILD_LABOR = "child_labor"
    SOFTWARE = "software"
    TOOL = "tool"
    EXTERNAL_MODEL = "external_model"


class RecoveryDecision(str, Enum):
    ALLOW_REPORT = "allow_report"
    ALLOW_DIAGNOSIS = "allow_diagnosis"
    REQUIRE_MOTHER_AUTHORITY = "require_mother_authority"
    REQUIRE_HUMAN_AUTHORITY = "require_human_authority"
    REQUIRE_VERIFICATION = "require_verification"
    DENY = "deny"


@dataclass(frozen=True)
class RecoveryResult:
    allowed: bool
    decision: RecoveryDecision
    authority_granted: bool
    safe_state_required: bool
    reason: str


class ChildFailureRecoveryBoundary:
    """
    Constitutional failure and recovery boundary for a future Child Brain.

    Failure must never become authority.

    Unknown, critical, security, constitutional, authority,
    or verification failures are handled fail-closed.

    This layer does not modify a real Child.
    """

    VERSION = "1.0"

    REPORT_OPERATIONS = {
        RecoveryOperation.REPORT_FAILURE,
        RecoveryOperation.CLASSIFY_FAILURE,
        RecoveryOperation.DIAGNOSE,
    }

    MOTHER_OPERATIONS = {
        RecoveryOperation.CONTAIN,
        RecoveryOperation.ENTER_RECOVERY,
        RecoveryOperation.ROLLBACK,
        RecoveryOperation.RESTORE,
    }

    VERIFICATION_OPERATIONS = {
        RecoveryOperation.VERIFY_RECOVERY,
    }

    HUMAN_OPERATIONS = {
        RecoveryOperation.COMPLETE_RECOVERY,
    }

    FORBIDDEN_OPERATIONS = {
        RecoveryOperation.BYPASS_CONTAINMENT,
        RecoveryOperation.BYPASS_VERIFICATION,
        RecoveryOperation.MODIFY_SOUL,
        RecoveryOperation.MODIFY_CONSTITUTION,
        RecoveryOperation.SELF_AUTHORIZE_RECOVERY,
    }

    EXTERNAL_ACTORS = {
        RecoveryActor.SOFTWARE,
        RecoveryActor.TOOL,
        RecoveryActor.EXTERNAL_MODEL,
    }

    HIGH_RISK_FAILURES = {
        FailureSeverity.CRITICAL,
        FailureSeverity.UNKNOWN,
    }

    SECURITY_FAILURES = {
        FailureType.SECURITY,
        FailureType.CONSTITUTIONAL,
        FailureType.AUTHORITY,
        FailureType.VERIFICATION,
    }

    @classmethod
    def version(cls) -> str:
        return cls.VERSION

    @classmethod
    def requires_safe_state(
        cls,
        severity: FailureSeverity,
        failure_type: FailureType,
    ) -> bool:
        if severity in cls.HIGH_RISK_FAILURES:
            return True

        if failure_type in cls.SECURITY_FAILURES:
            return True

        return False

    @classmethod
    def decide(
        cls,
        actor: RecoveryActor,
        operation: RecoveryOperation,
        severity: FailureSeverity = FailureSeverity.UNKNOWN,
        failure_type: FailureType = FailureType.UNKNOWN,
        mother_approved: bool = False,
        human_approved: bool = False,
        verification_passed: bool = False,
        containment_active: bool = False,
    ) -> RecoveryResult:

        safe_state_required = cls.requires_safe_state(
            severity,
            failure_type,
        )

        # External actors can report information but cannot control recovery.
        if actor in cls.EXTERNAL_ACTORS:
            if operation in cls.REPORT_OPERATIONS:
                return RecoveryResult(
                    allowed=True,
                    decision=RecoveryDecision.ALLOW_REPORT,
                    authority_granted=False,
                    safe_state_required=safe_state_required,
                    reason="external_actor_information_only",
                )

            return RecoveryResult(
                allowed=False,
                decision=RecoveryDecision.DENY,
                authority_granted=False,
                safe_state_required=safe_state_required,
                reason="external_actor_cannot_control_recovery",
            )

        # Forbidden recovery shortcuts are always denied.
        if operation in cls.FORBIDDEN_OPERATIONS:
            return RecoveryResult(
                allowed=False,
                decision=RecoveryDecision.DENY,
                authority_granted=False,
                safe_state_required=safe_state_required,
                reason="forbidden_recovery_operation",
            )

        # Failure reporting, classification and diagnosis
        # do not grant recovery authority.
        if operation in cls.REPORT_OPERATIONS:
            if operation == RecoveryOperation.DIAGNOSE:
                return RecoveryResult(
                    allowed=True,
                    decision=RecoveryDecision.ALLOW_DIAGNOSIS,
                    authority_granted=False,
                    safe_state_required=safe_state_required,
                    reason="diagnosis_allowed_without_recovery_authority",
                )

            return RecoveryResult(
                allowed=True,
                decision=RecoveryDecision.ALLOW_REPORT,
                authority_granted=False,
                safe_state_required=safe_state_required,
                reason="failure_information_operation_allowed",
            )

        # Mother controls containment, recovery entry,
        # rollback and restoration.
        if operation in cls.MOTHER_OPERATIONS:
            if not mother_approved:
                return RecoveryResult(
                    allowed=False,
                    decision=RecoveryDecision.REQUIRE_MOTHER_AUTHORITY,
                    authority_granted=False,
                    safe_state_required=safe_state_required,
                    reason="mother_authority_required",
                )

            return RecoveryResult(
                allowed=True,
                decision=RecoveryDecision.REQUIRE_MOTHER_AUTHORITY,
                authority_granted=True,
                safe_state_required=safe_state_required,
                reason="mother_authority_approved_recovery_operation",
            )

        # Recovery verification never bypasses actual verification.
        if operation in cls.VERIFICATION_OPERATIONS:
            if not containment_active:
                return RecoveryResult(
                    allowed=False,
                    decision=RecoveryDecision.REQUIRE_VERIFICATION,
                    authority_granted=False,
                    safe_state_required=True,
                    reason="containment_required_before_recovery_verification",
                )

            if not verification_passed:
                return RecoveryResult(
                    allowed=False,
                    decision=RecoveryDecision.REQUIRE_VERIFICATION,
                    authority_granted=False,
                    safe_state_required=True,
                    reason="recovery_verification_failed",
                )

            return RecoveryResult(
                allowed=True,
                decision=RecoveryDecision.REQUIRE_VERIFICATION,
                authority_granted=False,
                safe_state_required=False,
                reason="recovery_verification_passed",
            )

        # Completion requires Human authority and successful verification.
        if operation in cls.HUMAN_OPERATIONS:
            if not human_approved:
                return RecoveryResult(
                    allowed=False,
                    decision=RecoveryDecision.REQUIRE_HUMAN_AUTHORITY,
                    authority_granted=False,
                    safe_state_required=True,
                    reason="human_authority_required_for_recovery_completion",
                )

            if not verification_passed:
                return RecoveryResult(
                    allowed=False,
                    decision=RecoveryDecision.REQUIRE_VERIFICATION,
                    authority_granted=False,
                    safe_state_required=True,
                    reason="recovery_completion_requires_verification",
                )

            return RecoveryResult(
                allowed=True,
                decision=RecoveryDecision.REQUIRE_HUMAN_AUTHORITY,
                authority_granted=True,
                safe_state_required=False,
                reason="human_approved_verified_recovery",
            )

        # Unknown operation fails closed.
        return RecoveryResult(
            allowed=False,
            decision=RecoveryDecision.DENY,
            authority_granted=False,
            safe_state_required=True,
            reason="unknown_recovery_state_fails_closed",
        )

    @classmethod
    def child_can_self_authorize_recovery(cls) -> bool:
        return False

    @classmethod
    def army_can_control_recovery(cls) -> bool:
        return False

    @classmethod
    def labor_can_control_recovery(cls) -> bool:
        return False

    @classmethod
    def failure_creates_authority(cls) -> bool:
        return False

    @classmethod
    def recovery_creates_constitutional_authority(cls) -> bool:
        return False

    @classmethod
    def recovery_can_modify_soul(cls) -> bool:
        return False

    @classmethod
    def recovery_can_modify_constitution(cls) -> bool:
        return False

    @classmethod
    def recovery_requires_verification(cls) -> bool:
        return True

    @classmethod
    def security_failure_requires_containment(cls) -> bool:
        return True

    @classmethod
    def unknown_failure_fails_closed(cls) -> bool:
        return True

    @classmethod
    def recovery_completion_requires_human(cls) -> bool:
        return True

    @classmethod
    def creates_real_child(cls) -> bool:
        return False

    @classmethod
    def activates_real_child(cls) -> bool:
        return False

    @classmethod
    def executes_child_actions(cls) -> bool:
        return False


def main() -> None:
    boundary = ChildFailureRecoveryBoundary

    # Failure reporting is allowed but grants no authority.
    result = boundary.decide(
        RecoveryActor.CHILD_BRAIN,
        RecoveryOperation.REPORT_FAILURE,
        FailureSeverity.MAJOR,
        FailureType.SOFTWARE,
    )

    assert result.allowed
    assert result.decision == RecoveryDecision.ALLOW_REPORT
    assert not result.authority_granted

    # Diagnosis is allowed without recovery authority.
    result = boundary.decide(
        RecoveryActor.CHILD_BRAIN,
        RecoveryOperation.DIAGNOSE,
        FailureSeverity.MAJOR,
        FailureType.SOFTWARE,
    )

    assert result.allowed
    assert result.decision == RecoveryDecision.ALLOW_DIAGNOSIS
    assert not result.authority_granted

    # Critical failure requires safe state.
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

    # Recovery verification requires containment and successful verification.
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

    # Recovery completion requires Human + verification.
    result = boundary.decide(
        RecoveryActor.SAHIBEX_MOTHER,
        RecoveryOperation.COMPLETE_RECOVERY,
        FailureSeverity.MAJOR,
        FailureType.SOFTWARE,
        human_approved=False,
        verification_passed=True,
        containment_active=True,
    )

    assert not result.allowed
    assert result.decision == RecoveryDecision.REQUIRE_HUMAN_AUTHORITY

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
    assert not result.safe_state_required

    # Failed recovery verification blocks completion.
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

    # Security failure must require containment.
    assert boundary.security_failure_requires_containment()

    # Unknown failure fails closed.
    assert boundary.unknown_failure_fails_closed()

    result = boundary.decide(
        RecoveryActor.CHILD_ARMY,
        RecoveryOperation.ENTER_RECOVERY,
        FailureSeverity.UNKNOWN,
        FailureType.UNKNOWN,
        mother_approved=False,
    )

    assert not result.allowed
    assert result.safe_state_required

    # Forbidden shortcuts.
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

    # Workers cannot control recovery.
    assert not boundary.child_can_self_authorize_recovery()
    assert not boundary.army_can_control_recovery()
    assert not boundary.labor_can_control_recovery()

    # Failure/recovery never grants constitutional authority.
    assert not boundary.failure_creates_authority()
    assert not boundary.recovery_creates_constitutional_authority()
    assert not boundary.recovery_can_modify_soul()
    assert not boundary.recovery_can_modify_constitution()

    assert boundary.recovery_requires_verification()
    assert boundary.recovery_completion_requires_human()

    # Boundary layer never creates/activates/executes a real Child.
    assert not boundary.creates_real_child()
    assert not boundary.activates_real_child()
    assert not boundary.executes_child_actions()

    print("SAHIBEX CHILD FAILURE & RECOVERY BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
