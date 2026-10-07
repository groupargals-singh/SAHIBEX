from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.brain.child_tool_permission_gateway import (
    ChildToolPermissionGateway,
    ToolAction,
    ToolPermissionRequest,
)

from core.brain.child_tool_registry import (
    ChildToolRegistry,
    ToolDefinition,
)

from core.brain.child_tool_execution_boundary import (
    ChildToolExecutionBoundary,
    ToolExecutionRequest,
)


class OrchestratorDecision(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"


@dataclass(frozen=True)
class ToolOrchestrationRequest:
    request_id: str
    child_brain_id: str
    tool_id: str
    tool_name: str
    action: ToolAction
    purpose: str
    mother_approved: bool = False
    human_approved: bool = False


@dataclass(frozen=True)
class ToolOrchestrationResult:
    allowed: bool
    decision: OrchestratorDecision
    request: ToolOrchestrationRequest
    reason: str


class ChildToolExecutionOrchestrator:
    VERSION = "1.0"

    def __init__(
        self,
        permission_gateway: ChildToolPermissionGateway,
        registry: ChildToolRegistry,
        execution_boundary: ChildToolExecutionBoundary,
    ) -> None:
        self.permission_gateway = permission_gateway
        self.registry = registry
        self.execution_boundary = execution_boundary

    def evaluate(
        self,
        request: ToolOrchestrationRequest,
    ) -> ToolOrchestrationResult:

        if not request.request_id:
            return ToolOrchestrationResult(
                False,
                OrchestratorDecision.BLOCK,
                request,
                "request identity is required",
            )

        if not request.child_brain_id:
            return ToolOrchestrationResult(
                False,
                OrchestratorDecision.BLOCK,
                request,
                "child brain identity is required",
            )

        if not request.tool_id:
            return ToolOrchestrationResult(
                False,
                OrchestratorDecision.BLOCK,
                request,
                "tool identity is required",
            )

        if not request.tool_name:
            return ToolOrchestrationResult(
                False,
                OrchestratorDecision.BLOCK,
                request,
                "tool name is required",
            )

        if not request.purpose:
            return ToolOrchestrationResult(
                False,
                OrchestratorDecision.BLOCK,
                request,
                "purpose is required",
            )

        # -----------------------------------------------------
        # 1. Registry validation
        # -----------------------------------------------------
        registry_result = self.registry.get(
            request.tool_id
        )

        if not registry_result.allowed:
            return ToolOrchestrationResult(
                False,
                OrchestratorDecision.BLOCK,
                request,
                "tool is not registered or enabled",
            )

        tool: ToolDefinition = registry_result.tool

        if tool.tool_name != request.tool_name:
            return ToolOrchestrationResult(
                False,
                OrchestratorDecision.BLOCK,
                request,
                "tool identity mismatch",
            )

        # -----------------------------------------------------
        # 2. Permission validation
        # -----------------------------------------------------
        permission_request = ToolPermissionRequest(
            request_id=request.request_id,
            child_brain_id=request.child_brain_id,
            tool_name=request.tool_name,
            action=request.action,
            purpose=request.purpose,
        )

        permission_result = self.permission_gateway.evaluate(
            permission_request,
            mother_approved=request.mother_approved,
            human_approved=request.human_approved,
        )

        if not permission_result.allowed:
            return ToolOrchestrationResult(
                False,
                OrchestratorDecision.BLOCK,
                request,
                permission_result.reason,
            )

        # -----------------------------------------------------
        # 3. Execution boundary validation
        # -----------------------------------------------------
        execution_request = ToolExecutionRequest(
            request_id=request.request_id,
            child_brain_id=request.child_brain_id,
            tool_id=tool.tool_id,
            tool_name=tool.tool_name,
            permission_granted=permission_result.allowed,
            purpose=request.purpose,
        )

        execution_result = self.execution_boundary.evaluate(
            execution_request
        )

        if not execution_result.allowed:
            return ToolOrchestrationResult(
                False,
                OrchestratorDecision.BLOCK,
                request,
                execution_result.reason,
            )

        return ToolOrchestrationResult(
            True,
            OrchestratorDecision.ALLOW,
            request,
            "tool execution request passed all permission boundaries",
        )

    def execute_real_tool(self) -> bool:
        return False

    def execute_shell_command(self) -> bool:
        return False

    def execute_network_request(self) -> bool:
        return False

    def execute_filesystem_write(self) -> bool:
        return False

    def grant_authority(self) -> bool:
        return False

    def bypass_permission(self) -> bool:
        return False

    def fails_closed(self) -> bool:
        return True

    def capability_is_authority(self) -> bool:
        return False
