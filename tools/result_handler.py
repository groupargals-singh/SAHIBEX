from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tools.invocation import ToolInvocationResult


@dataclass(frozen=True)
class ToolResult:
    """
    Normalized result returned by the SAHIBEX
    tool-result handling boundary.
    """

    tool: str
    success: bool
    allowed: bool
    requires_confirmation: bool
    result: Any
    error: str | None
    risk: str
    reason: str


class ToolResultHandler:
    """
    Controlled tool-result normalization layer.

    Responsibilities:
    - accept a ToolInvocationResult
    - validate its identity
    - preserve execution state
    - preserve result/error information
    - expose a stable ToolResult object

    This layer:
    - never executes tools
    - never grants permission
    - never changes permission decisions
    - never retries execution
    - never modifies the original invocation result
    """

    def handle(
        self,
        invocation: ToolInvocationResult,
    ) -> ToolResult:

        if not isinstance(
            invocation,
            ToolInvocationResult,
        ):
            raise TypeError(
                "invocation must be ToolInvocationResult"
            )

        if not invocation.tool:
            raise ValueError(
                "Tool name cannot be empty."
            )

        if invocation.success and invocation.error is not None:
            raise ValueError(
                "Successful tool result cannot contain an error."
            )

        if not invocation.success and invocation.result is not None:
            raise ValueError(
                "Failed tool result cannot contain execution result."
            )

        if not invocation.allowed and invocation.success:
            raise ValueError(
                "Blocked tool invocation cannot be successful."
            )

        return ToolResult(
            tool=invocation.tool,
            success=invocation.success,
            allowed=invocation.allowed,
            requires_confirmation=(
                invocation.requires_confirmation
            ),
            result=invocation.result,
            error=invocation.error,
            risk=invocation.risk,
            reason=invocation.reason,
        )
