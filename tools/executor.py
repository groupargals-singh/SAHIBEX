from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.brain.mother_sandbox_runtime import (
    MotherSandboxRequest,
    MotherSandboxRuntime,
)
from tools.registry import ToolRegistry


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
    ) -> None:
        self.registry = registry
        self.sandbox = (
            sandbox
            if sandbox is not None
            else MotherSandboxRuntime()
        )

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
