from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from core.brain.operational_reasoning import OperationalReasoningResult
from tools.failure_recovery import RecoveryResult
from tools.result_handler import ToolResult


@dataclass(frozen=True)
class OperationalVerificationResult:
    """
    Normalized verification result for operational execution.

    This layer does not execute actions and does not grant
    permissions.

    It verifies already-produced operational results and
    normalizes recovery state.
    """

    success: bool
    verified: bool
    verification_status: str
    recovery_status: str
    attempts: int
    retryable: bool
    reason: str
    result: Any = None
    verification_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool.")

        if not isinstance(self.verified, bool):
            raise TypeError("verified must be bool.")

        if not isinstance(self.verification_status, str):
            raise TypeError(
                "verification_status must be str."
            )

        if not self.verification_status.strip():
            raise ValueError(
                "verification_status must not be empty."
            )

        if not isinstance(self.recovery_status, str):
            raise TypeError("recovery_status must be str.")

        if not self.recovery_status.strip():
            raise ValueError(
                "recovery_status must not be empty."
            )

        if not isinstance(self.attempts, int):
            raise TypeError("attempts must be int.")

        if self.attempts <= 0:
            raise ValueError(
                "attempts must be greater than zero."
            )

        if not isinstance(self.retryable, bool):
            raise TypeError("retryable must be bool.")

        if not isinstance(self.reason, str):
            raise TypeError("reason must be str.")

        if not self.reason.strip():
            raise ValueError("reason must not be empty.")

        if not isinstance(self.verification_id, str):
            raise TypeError("verification_id must be str.")

        if not self.verification_id.strip():
            raise ValueError(
                "verification_id must not be empty."
            )


class OperationalVerificationRecovery:
    """
    Operational verification and recovery boundary.

    Responsibilities:
    - verify operational reasoning results
    - verify completed tool results
    - normalize tool recovery results
    - distinguish successful, blocked, retryable and failed states
    - prevent failed or inconsistent results from being
      reported as successful

    This layer does not:
    - execute tools
    - execute commands
    - grant permissions
    - modify the constitution
    - override verification
    - perform protected actions
    """

    def verify_reasoning(
        self,
        result: OperationalReasoningResult,
    ) -> OperationalVerificationResult:

        if not isinstance(
            result,
            OperationalReasoningResult,
        ):
            raise TypeError(
                "result must be OperationalReasoningResult."
            )

        if not result.success:
            return OperationalVerificationResult(
                success=False,
                verified=False,
                verification_status=result.verification_status,
                recovery_status="FAILED",
                attempts=1,
                retryable=False,
                reason=(
                    "Operational reasoning result is not successful."
                ),
                result=None,
            )

        if result.verification_status not in {"VERIFIED", "GENERATED"}:
            return OperationalVerificationResult(
                success=False,
                verified=False,
                verification_status=(
                    result.verification_status
                ),
                recovery_status="BLOCKED",
                attempts=1,
                retryable=False,
                reason=(
                    "Operational reasoning verification "
                    "status is not VERIFIED."
                ),
                result=None,
            )

        if result.requires_confirmation:
            return OperationalVerificationResult(
                success=False,
                verified=False,
                verification_status=(
                    result.verification_status
                ),
                recovery_status="BLOCKED",
                attempts=1,
                retryable=False,
                reason=(
                    "Operational reasoning still requires "
                    "user confirmation."
                ),
                result=None,
            )

        if not result.model_response.strip():
            return OperationalVerificationResult(
                success=False,
                verified=False,
                verification_status=(
                    result.verification_status
                ),
                recovery_status="FAILED",
                attempts=1,
                retryable=False,
                reason=(
                    "Successful reasoning result contains "
                    "an empty model response."
                ),
                result=None,
            )

        # GENERATED means the response passed structural checks only;
        # it has not been independently checked for factual correctness.
        is_independently_verified = result.verification_status == "VERIFIED"
        return OperationalVerificationResult(
            success=True,
            verified=is_independently_verified,
            verification_status=(
                "VERIFIED" if is_independently_verified else "STRUCTURALLY_VALID"
            ),
            recovery_status="SUCCESS",
            attempts=1,
            retryable=False,
            reason=(
                "Operational reasoning result passed structural checks."
                if not is_independently_verified
                else "Operational reasoning result passed verification checks."
            ),
            result=result.model_response,
        )

    def verify_tool_result(
        self,
        result: ToolResult,
    ) -> OperationalVerificationResult:
        """
        Perform the post-execution safety verification of a
        normalized ToolResult.

        This method never executes the tool and never grants
        permission. It only decides whether an already-produced
        result is internally consistent and safe to accept.
        """

        if not isinstance(result, ToolResult):
            raise TypeError(
                "result must be ToolResult."
            )

        checks_failed: list[str] = []

        # --------------------------------------------------
        # CHECK 1: Tool identity
        # --------------------------------------------------
        if not result.tool.strip():
            checks_failed.append(
                "Tool identity is empty."
            )

        # --------------------------------------------------
        # CHECK 2: Permission state
        # --------------------------------------------------
        if result.success and not result.allowed:
            checks_failed.append(
                "Successful tool result is not allowed."
            )

        # --------------------------------------------------
        # CHECK 3: Confirmation state
        # --------------------------------------------------
        if result.success and result.requires_confirmation:
            checks_failed.append(
                "Successful tool result still requires confirmation."
            )

        # --------------------------------------------------
        # CHECK 4: Success/error consistency
        # --------------------------------------------------
        if result.success and result.error is not None:
            checks_failed.append(
                "Successful tool result contains an error."
            )

        # --------------------------------------------------
        # CHECK 5: Success/result consistency
        # --------------------------------------------------
        if result.success and result.result is None:
            checks_failed.append(
                "Successful tool result contains no execution result."
            )

        # --------------------------------------------------
        # CHECK 6: Failure/result consistency
        # --------------------------------------------------
        if not result.success and result.result is not None:
            checks_failed.append(
                "Failed tool result contains execution data."
            )

        # --------------------------------------------------
        # CHECK 7: Blocked execution safeguard
        # --------------------------------------------------
        if not result.allowed and result.success:
            checks_failed.append(
                "Blocked tool execution cannot be successful."
            )

        if checks_failed:
            return OperationalVerificationResult(
                success=False,
                verified=False,
                verification_status="VERIFICATION_FAILED",
                recovery_status="FAILED",
                attempts=1,
                retryable=False,
                reason="; ".join(checks_failed),
                result=None,
            )

        # A normal failed execution remains a failure.
        if not result.success:
            return OperationalVerificationResult(
                success=False,
                verified=False,
                verification_status="FAILED",
                recovery_status="FAILED",
                attempts=1,
                retryable=False,
                reason=(
                    result.error
                    or result.reason
                    or "Tool execution failed."
                ),
                result=None,
            )

        return OperationalVerificationResult(
            success=True,
            verified=True,
            verification_status="VERIFIED",
            recovery_status="SUCCESS",
            attempts=1,
            retryable=False,
            reason=(
                "Tool execution result passed "
                "post-execution verification."
            ),
            result=result.result,
        )

    def normalize_recovery(
        self,
        recovery: RecoveryResult,
    ) -> OperationalVerificationResult:

        if not isinstance(recovery, RecoveryResult):
            raise TypeError(
                "recovery must be RecoveryResult."
            )

        if recovery.status == "SUCCESS":
            return OperationalVerificationResult(
                success=True,
                verified=True,
                verification_status="VERIFIED",
                recovery_status="SUCCESS",
                attempts=recovery.attempts,
                retryable=False,
                reason=recovery.reason,
                result=recovery.result,
            )

        if recovery.status == "BLOCKED":
            return OperationalVerificationResult(
                success=False,
                verified=False,
                verification_status="BLOCKED",
                recovery_status="BLOCKED",
                attempts=recovery.attempts,
                retryable=False,
                reason=recovery.reason,
                result=None,
            )

        if recovery.status == "RETRY":
            return OperationalVerificationResult(
                success=False,
                verified=False,
                verification_status="RETRY_REQUIRED",
                recovery_status="RETRY",
                attempts=recovery.attempts,
                retryable=True,
                reason=recovery.reason,
                result=None,
            )

        return OperationalVerificationResult(
            success=False,
            verified=False,
            verification_status="FAILED",
            recovery_status="FAILED",
            attempts=recovery.attempts,
            retryable=False,
            reason=recovery.reason,
            result=None,
        )
