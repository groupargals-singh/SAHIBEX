from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExecutionDecision(str, Enum):
    ALLOW = "allow"
    REQUIRE_PERMISSION = "require_permission"
    DENY = "deny"


@dataclass(frozen=True)
class ToolExecutionRequest:
    request_id: str
    child_brain_id: str
    tool_id: str
    tool_name: str
    permission_granted: bool
    purpose: str


@dataclass(frozen=True)
class ToolExecutionResult:
    allowed: bool
    decision: ExecutionDecision
    request: ToolExecutionRequest
    reason: str


class ChildToolExecutionBoundary:
    VERSION = "1.0"

    def evaluate(
        self,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResult:

        if not request.request_id:
            return ToolExecutionResult(
                False,
                ExecutionDecision.DENY,
                request,
                "request identity is required",
            )

        if not request.child_brain_id:
            return ToolExecutionResult(
                False,
                ExecutionDecision.DENY,
                request,
                "child brain identity is required",
            )

        if not request.tool_id:
            return ToolExecutionResult(
                False,
                ExecutionDecision.DENY,
                request,
                "tool identity is required",
            )

        if not request.tool_name:
            return ToolExecutionResult(
                False,
                ExecutionDecision.DENY,
                request,
                "tool name is required",
            )

        if not request.purpose:
            return ToolExecutionResult(
                False,
                ExecutionDecision.DENY,
                request,
                "execution purpose is required",
            )

        if not request.permission_granted:
            return ToolExecutionResult(
                False,
                ExecutionDecision.REQUIRE_PERMISSION,
                request,
                "tool permission is required",
            )

        return ToolExecutionResult(
            True,
            ExecutionDecision.ALLOW,
            request,
            "execution boundary approved",
        )

    def execute_tool(self) -> bool:
        return False

    def execute_shell_command(self) -> bool:
        return False

    def execute_unknown_tool(self) -> bool:
        return False

    def bypass_permission(self) -> bool:
        return False

    def grant_permission(self) -> bool:
        return False

    def grant_authority(self) -> bool:
        return False

    def modify_constitution(self) -> bool:
        return False

    def modify_soul(self) -> bool:
        return False

    def fails_closed(self) -> bool:
        return True

    def capability_is_authority(self) -> bool:
        return False
