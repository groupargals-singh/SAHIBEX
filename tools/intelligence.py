from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.brain.operational_verification import OperationalVerificationRecovery
from tools.failure_recovery import (
    RecoveryResult,
    RetryPolicy,
    ToolFailureRecovery,
)
from tools.invocation import ToolInvoker
from tools.result_handler import ToolResult, ToolResultHandler


@dataclass(frozen=True)
class ToolIntelligenceResult:
    tool: str
    success: bool
    allowed: bool
    requires_confirmation: bool
    attempts: int
    recovery_status: str
    retryable: bool
    result: Any
    error: str | None
    risk: str
    reason: str


class ToolIntelligence:
    """
    Intelligence-level coordinator for safe tool execution.

    Responsibilities:
    - delegate tool discovery and invocation to ToolInvoker
    - normalize valid tool results through ToolResultHandler
    - verify successful post-execution results
    - classify failures through ToolFailureRecovery
    - retry only when the recovery policy says the failure is retryable

    This class never bypasses the permission or execution layers.
    Post-execution verification cannot grant permission or execute tools.
    """

    def __init__(
        self,
        tool_invoker: ToolInvoker,
        result_handler: ToolResultHandler,
        recovery: ToolFailureRecovery | None = None,
        operational_verification: OperationalVerificationRecovery | None = None,
    ) -> None:
        self.tool_invoker = tool_invoker
        self.result_handler = result_handler
        self.recovery = recovery or ToolFailureRecovery()
        self.operational_verification = (
            operational_verification or OperationalVerificationRecovery()
        )

    def execute(
        self,
        discovery_query: str,
        *,
        max_attempts: int = 3,
        user_confirmation: bool = False,
        **kwargs: Any,
    ) -> ToolIntelligenceResult:
        if not discovery_query.strip():
            raise ValueError("discovery_query cannot be empty.")

        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")

        attempts = 0

        while attempts < max_attempts:
            attempts += 1

            invocation = self.tool_invoker.invoke(
                discovery_query,
                user_confirmation=user_confirmation,
                **kwargs,
            )

            # ToolInvoker can legitimately return an empty tool when
            # discovery finds no matching tool. ToolResultHandler
            # intentionally rejects empty tool names, so this blocked
            # discovery case must be handled here at the intelligence
            # coordination layer.
            if not invocation.tool:
                return ToolIntelligenceResult(
                    tool="",
                    success=False,
                    allowed=False,
                    requires_confirmation=False,
                    attempts=attempts,
                    recovery_status="BLOCKED",
                    retryable=False,
                    result=None,
                    error=invocation.error,
                    risk=invocation.risk,
                    reason=invocation.reason,
                )

            normalized: ToolResult = self.result_handler.handle(
                invocation
            )

            recovery: RecoveryResult = self.recovery.recover(
                invocation,
                attempts=attempts,
            )

            # 6P-9:
            # A successful execution is not accepted blindly.
            # It must pass the post-execution verification boundary.
            if normalized.success:
                post_execution = (
                    self.operational_verification.verify_tool_result(
                        normalized
                    )
                )

                if not post_execution.verified:
                    return ToolIntelligenceResult(
                        tool=normalized.tool,
                        success=False,
                        allowed=normalized.allowed,
                        requires_confirmation=normalized.requires_confirmation,
                        attempts=attempts,
                        recovery_status="FAILED",
                        retryable=False,
                        result=None,
                        error=post_execution.reason,
                        risk=normalized.risk,
                        reason=post_execution.reason,
                    )

                return ToolIntelligenceResult(
                    tool=normalized.tool,
                    success=True,
                    allowed=normalized.allowed,
                    requires_confirmation=normalized.requires_confirmation,
                    attempts=attempts,
                    recovery_status=recovery.status,
                    retryable=False,
                    result=post_execution.result,
                    error=None,
                    risk=normalized.risk,
                    reason=post_execution.reason,
                )

            # Existing recovery/retry behavior remains unchanged.
            if (
                not recovery.retryable
                or recovery.status != "RETRY"
            ):
                return ToolIntelligenceResult(
                    tool=normalized.tool,
                    success=False,
                    allowed=normalized.allowed,
                    requires_confirmation=normalized.requires_confirmation,
                    attempts=attempts,
                    recovery_status=recovery.status,
                    retryable=recovery.retryable,
                    result=None,
                    error=normalized.error,
                    risk=normalized.risk,
                    reason=recovery.reason,
                )

        return ToolIntelligenceResult(
            tool=normalized.tool,
            success=False,
            allowed=normalized.allowed,
            requires_confirmation=normalized.requires_confirmation,
            attempts=attempts,
            recovery_status="FAILED",
            retryable=True,
            result=None,
            error=normalized.error,
            risk=normalized.risk,
            reason="Maximum tool execution attempts reached.",
        )
