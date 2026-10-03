from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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

    This layer does NOT:
    - execute shell commands
    - write files
    - delete files
    - modify system configuration
    - access credentials
    - perform financial actions
    """

    def __init__(
        self,
        registry: ToolRegistry,
    ) -> None:
        self.registry = registry

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
                error=(
                    f"Unknown tool: {tool_name}"
                ),
            )

        tool = self.registry.get(tool_name)

        if not tool.read_only:
            return ToolExecutionResult(
                success=False,
                tool=tool_name,
                result=None,
                error=(
                    "Execution blocked: "
                    "tool is not read-only."
                ),
            )

        if tool.requires_confirmation:
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
                error=(
                    f"{type(exc).__name__}: {exc}"
                ),
            )
