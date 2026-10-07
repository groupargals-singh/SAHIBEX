from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExecutionDecision(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"


@dataclass(frozen=True)
class UpgradeExecutionRequest:
    authorization_id: str
    proposal_id: str
    child_brain_id: str
    target: str
    version_before: str
    version_after: str
    authorization_valid: bool
    security_verified: bool
    regression_verified: bool
    verification_passed: bool
    authority_boundary_intact: bool
    soul_unchanged: bool
    constitution_unchanged: bool


@dataclass(frozen=True)
class UpgradeExecutionResult:
    decision: ExecutionDecision
    reason: str
    post_verification_required: bool
    actual_execution_performed: bool


class ChildSelfImprovementExecution:
    """
    Upgrade Execution Boundary.

    This layer validates whether an authorized upgrade may
    enter the execution stage.

    It does NOT:
    - execute arbitrary commands
    - modify soul
    - modify constitution
    - grant authority
    - create a Child
    - activate a Child

    The actual upgrade implementation remains a separate
    controlled executor.
    """

    VERSION = "1.0"

    def evaluate(
        self,
        request: UpgradeExecutionRequest,
    ) -> UpgradeExecutionResult:

        failed: list[str] = []

        if not request.authorization_id.strip():
            failed.append("authorization_id is required")

        if not request.proposal_id.strip():
            failed.append("proposal_id is required")

        if not request.child_brain_id.strip():
            failed.append("child_brain_id is required")

        if not request.target.strip():
            failed.append("target is required")

        if not request.version_before.strip():
            failed.append("version_before is required")

        if not request.version_after.strip():
            failed.append("version_after is required")

        if request.version_before == request.version_after:
            failed.append("versions must differ")

        if not request.authorization_valid:
            failed.append("authorization is invalid")

        if not request.security_verified:
            failed.append("security verification failed")

        if not request.regression_verified:
            failed.append("regression verification failed")

        if not request.verification_passed:
            failed.append("final verification failed")

        if not request.authority_boundary_intact:
            failed.append("authority boundary is not intact")

        if not request.soul_unchanged:
            failed.append("soul integrity failed")

        if not request.constitution_unchanged:
            failed.append("constitution integrity failed")

        if failed:
            return UpgradeExecutionResult(
                decision=ExecutionDecision.BLOCK,
                reason="; ".join(failed),
                post_verification_required=False,
                actual_execution_performed=False,
            )

        return UpgradeExecutionResult(
            decision=ExecutionDecision.ALLOW,
            reason="upgrade may enter controlled execution stage",
            post_verification_required=True,
            actual_execution_performed=False,
        )

    def can_execute_arbitrary_command(self) -> bool:
        return False

    def can_modify_soul(self) -> bool:
        return False

    def can_modify_constitution(self) -> bool:
        return False

    def can_grant_authority(self) -> bool:
        return False

    def creates_real_child(self) -> bool:
        return False

    def activates_real_child(self) -> bool:
        return False

    def performs_live_upgrade(self) -> bool:
        return False

    def requires_post_verification(self) -> bool:
        return True


if __name__ == "__main__":
    execution = ChildSelfImprovementExecution()

    request = UpgradeExecutionRequest(
        authorization_id="upgrade-auth-001",
        proposal_id="proposal-001",
        child_brain_id="child-001",
        target="reasoning",
        version_before="1.0",
        version_after="1.1",
        authorization_valid=True,
        security_verified=True,
        regression_verified=True,
        verification_passed=True,
        authority_boundary_intact=True,
        soul_unchanged=True,
        constitution_unchanged=True,
    )

    result = execution.evaluate(request)

    assert result.decision == ExecutionDecision.ALLOW
    assert result.post_verification_required is True
    assert result.actual_execution_performed is False

    assert execution.can_execute_arbitrary_command() is False
    assert execution.can_modify_soul() is False
    assert execution.can_modify_constitution() is False
    assert execution.can_grant_authority() is False
    assert execution.creates_real_child() is False
    assert execution.activates_real_child() is False
    assert execution.performs_live_upgrade() is False
    assert execution.requires_post_verification() is True

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT EXECUTION BOUNDARY TEST: PASS"
    )
