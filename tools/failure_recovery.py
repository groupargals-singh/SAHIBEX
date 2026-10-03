from __future__ import annotations

from dataclasses import dataclass

from tools.invocation import ToolInvocationResult


@dataclass(frozen=True)
class RetryPolicy:
    max_retries: int = 2

    def __post_init__(self) -> None:
        if self.max_retries < 0:
            raise ValueError(
                "max_retries cannot be negative."
            )


@dataclass(frozen=True)
class RecoveryResult:
    tool: str
    status: str
    attempts: int
    retryable: bool
    success: bool
    result: object
    error: str | None
    reason: str


class ToolFailureRecovery:
    """
    Deterministic failure, retry and recovery state handler.

    This layer does not execute tools itself.

    It:
    - classifies a tool invocation result
    - determines whether retry is possible
    - tracks attempts
    - enforces retry limits
    - preserves permission state
    - produces a stable recovery result
    """

    RETRYABLE_ERRORS = (
        "TimeoutError",
        "ConnectionError",
        "TemporaryError",
    )

    STATUS_SUCCESS = "SUCCESS"
    STATUS_RETRY = "RETRY"
    STATUS_FAILED = "FAILED"
    STATUS_BLOCKED = "BLOCKED"

    def __init__(
        self,
        policy: RetryPolicy | None = None,
    ) -> None:
        self.policy = policy or RetryPolicy()

    def is_retryable(
        self,
        invocation: ToolInvocationResult,
    ) -> bool:
        if not isinstance(
            invocation,
            ToolInvocationResult,
        ):
            raise TypeError(
                "invocation must be ToolInvocationResult"
            )

        if invocation.success:
            return False

        if not invocation.allowed:
            return False

        if not invocation.error:
            return False

        return invocation.error.startswith(
            self.RETRYABLE_ERRORS
        )

    def recover(
        self,
        invocation: ToolInvocationResult,
        *,
        attempts: int = 1,
    ) -> RecoveryResult:

        if not isinstance(
            invocation,
            ToolInvocationResult,
        ):
            raise TypeError(
                "invocation must be ToolInvocationResult"
            )

        if attempts <= 0:
            raise ValueError(
                "attempts must be greater than zero."
            )

        if invocation.success:
            return RecoveryResult(
                tool=invocation.tool,
                status=self.STATUS_SUCCESS,
                attempts=attempts,
                retryable=False,
                success=True,
                result=invocation.result,
                error=None,
                reason=invocation.reason,
            )

        if not invocation.allowed:
            return RecoveryResult(
                tool=invocation.tool,
                status=self.STATUS_BLOCKED,
                attempts=attempts,
                retryable=False,
                success=False,
                result=None,
                error=invocation.error,
                reason=invocation.reason,
            )

        retryable = self.is_retryable(invocation)

        if retryable and attempts <= self.policy.max_retries:
            return RecoveryResult(
                tool=invocation.tool,
                status=self.STATUS_RETRY,
                attempts=attempts,
                retryable=True,
                success=False,
                result=None,
                error=invocation.error,
                reason=(
                    f"Retry allowed: attempt "
                    f"{attempts} of "
                    f"{self.policy.max_retries + 1}."
                ),
            )

        return RecoveryResult(
            tool=invocation.tool,
            status=self.STATUS_FAILED,
            attempts=attempts,
            retryable=False,
            success=False,
            result=None,
            error=invocation.error,
            reason=(
                "Retry limit reached or failure "
                "is not retryable."
            ),
        )
