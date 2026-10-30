from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.brain.mother_sandbox_runtime import (
    MotherSandboxRequest,
    MotherSandboxRuntime,
)
from tools.registry import ToolRegistry
from tools.permission_gateway import ToolPermissionGateway


@dataclass(frozen=True)
class ToolExecutionResult:
    success: bool
    tool: str
    result: Any
    error: str | None = None


class SafeToolExecutor:
    """
    Controlled execution boundary for SAHIBEX.

    Only registered read-only tools may execute.

    Mother Sandbox is checked before tool execution.

    This layer does NOT:
    - execute shell commands
    - write files
    - delete files
    - modify system configuration
    - access credentials
    - perform financial actions
    - grant permissions
    - bypass Human Authority
    """

    def __init__(
        self,
        registry: ToolRegistry,
        sandbox: MotherSandboxRuntime | None = None,
        permission_gateway: ToolPermissionGateway | None = None,
    ) -> None:
        self.registry = registry
        self.sandbox = (
            sandbox
            if sandbox is not None
            else MotherSandboxRuntime()
        )
        self.permission_gateway = permission_gateway

    def bind_permission_gateway(
        self,
        permission_gateway: ToolPermissionGateway,
    ) -> None:
        if not isinstance(permission_gateway, ToolPermissionGateway):
            raise TypeError("permission_gateway must be ToolPermissionGateway")
        if (
            self.permission_gateway is not None
            and self.permission_gateway is not permission_gateway
        ):
            raise ValueError("executor is already bound to a different permission gateway")
        self.permission_gateway = permission_gateway

    def execute(
        self,
        tool_name: str,
        **kwargs: Any,
    ) -> ToolExecutionResult:

        if not self.registry.has(tool_name):
            return ToolExecutionResult(
                success=False,
                tool=tool_name,
                result=None,
                error=f"Unknown tool: {tool_name}",
            )

        tool = self.registry.get(tool_name)
        confirmation_provided = kwargs.pop("_confirmation_provided", False)
        # Never trust a caller-supplied permission boolean. The executor
        # rechecks the canonical gateway and creates the handler flag itself.
        kwargs.pop("_permission_granted", None)

        if not isinstance(confirmation_provided, bool):
            return ToolExecutionResult(
                success=False,
                tool=tool_name,
                result=None,
                error="Execution blocked: confirmation must be a boolean.",
            )

        if tool.read_only and tool.protected_action is not None:
            return ToolExecutionResult(
                success=False,
                tool=tool_name,
                result=None,
                error="Execution blocked: conflicting read-only/protected-action metadata.",
            )

        if not tool.read_only:
            if self.permission_gateway is None:
                return ToolExecutionResult(
                    success=False,
                    tool=tool_name,
                    result=None,
                    error="Execution blocked: no canonical permission gateway is bound.",
                )
            try:
                permission = self.permission_gateway.check(
                    tool_name,
                    confirmation=confirmation_provided,
                    request=kwargs,
                )
            except (KeyError, TypeError, ValueError, PermissionError) as exc:
                return ToolExecutionResult(
                    success=False,
                    tool=tool_name,
                    result=None,
                    error=f"Execution blocked: permission check failed: {exc}",
                )
            if not permission.allowed:
                return ToolExecutionResult(
                    success=False,
                    tool=tool_name,
                    result=None,
                    error=f"Execution blocked by permission gateway: {permission.reason}",
                )
            kwargs["_permission_granted"] = True
            kwargs["_confirmation_provided"] = confirmation_provided

        sandbox_result = self.sandbox.validate(
            MotherSandboxRequest(
                request_id=f"tool-execution:{tool_name}",
                action=f"tool:{tool_name}",
                isolated_filesystem=True,
                isolated_memory=True,
                isolated_credentials=True,
                isolated_network=True,
                isolated_runtime=True,
            )
        )

        if not sandbox_result.allowed:
            return ToolExecutionResult(
                success=False,
                tool=tool_name,
                result=None,
                error=(
                    "Execution blocked by Mother Sandbox: "
                    f"{sandbox_result.reason}"
                ),
            )

        if not tool.read_only:
            permission_granted = kwargs.get("_permission_granted", False)
            if not permission_granted:
                return ToolExecutionResult(
                    success=False,
                    tool=tool_name,
                    result=None,
                    error=(
                        "Execution blocked: protected tool requires "
                        "permission gateway authorization."
                    ),
                )

        if tool.read_only and tool.requires_confirmation:
            return ToolExecutionResult(
                success=False,
                tool=tool_name,
                result=None,
                error=(
                    "Execution blocked: "
                    "tool requires confirmation."
                ),
            )

        try:
            result = tool.handler(**kwargs)

            return ToolExecutionResult(
                success=True,
                tool=tool_name,
                result=result,
                error=None,
            )

        except Exception as exc:
            return ToolExecutionResult(
                success=False,
                tool=tool_name,
                result=None,
                error=f"{type(exc).__name__}: {exc}",
            )
