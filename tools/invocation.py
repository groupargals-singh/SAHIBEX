from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tools.discovery import ToolDiscovery
from tools.executor import (
    SafeToolExecutor,
    ToolExecutionResult,
)
from tools.permission_gateway import (
    ToolPermissionGateway,
)


@dataclass(frozen=True)
class ToolInvocationResult:
    tool: str
    allowed: bool
    requires_confirmation: bool
    success: bool
    result: Any
    error: str | None
    risk: str
    reason: str


class ToolInvoker:
    """
    Controlled tool invocation boundary.

    Execution flow:
        Discovery
            ↓
        Permission Gateway
            ↓
        Safe Tool Executor
            ↓
        Tool Result

    This layer never bypasses permission.

    Explicit user confirmation is forwarded to the
    existing permission gateway. Confirmation itself
    never grants permission independently.
    """

    def __init__(
        self,
        discovery: ToolDiscovery,
        permission_gateway: ToolPermissionGateway,
        executor: SafeToolExecutor,
    ) -> None:
        if not isinstance(discovery, ToolDiscovery):
            raise TypeError(
                "discovery must be ToolDiscovery"
            )

        if not isinstance(
            permission_gateway,
            ToolPermissionGateway,
        ):
            raise TypeError(
                "permission_gateway must be ToolPermissionGateway"
            )

        if not isinstance(
            executor,
            SafeToolExecutor,
        ):
            raise TypeError(
                "executor must be SafeToolExecutor"
            )

        self.discovery = discovery
        self.permission_gateway = permission_gateway
        self.executor = executor
        self.executor.bind_permission_gateway(permission_gateway)

    def invoke(
        self,
        discovery_query: str,
        *,
        user_confirmation: bool = False,
        **kwargs: Any,
    ) -> ToolInvocationResult:
        """
        Discover and invoke a tool through the controlled
        permission and execution boundaries.

        user_confirmation is only forwarded to the existing
        permission gateway. It does not bypass permission,
        constitution, or safe execution controls.
        """
        if not isinstance(user_confirmation, bool):
            raise TypeError(
                "user_confirmation must be a boolean."
            )

        candidate = self.discovery.select(
            discovery_query
        )

        if candidate is None:
            return ToolInvocationResult(
                tool="",
                allowed=False,
                requires_confirmation=False,
                success=False,
                result=None,
                error=(
                    f"No registered tool matches: "
                    f"{discovery_query}"
                ),
                risk="unknown",
                reason=(
                    "No suitable tool was discovered."
                ),
            )

        permission = self.permission_gateway.check(
            candidate.name,
            confirmation=user_confirmation,
        )

        if not permission.allowed:
            return ToolInvocationResult(
                tool=candidate.name,
                allowed=False,
                requires_confirmation=(
                    permission.requires_confirmation
                ),
                success=False,
                result=None,
                error=None,
                risk=permission.risk,
                reason=permission.reason,
            )

        execution_kwargs = dict(kwargs)

        # Natural-language tool requests still need deterministic
        # argument binding before reaching the handler.  Keep this
        # parser deliberately narrow and limited to the registered
        # read-only filesystem tools; protected tools never receive
        # inferred authority or execution parameters here.
        if candidate.read_only:
            normalized_query = discovery_query.strip()
            query_parts = normalized_query.split(maxsplit=1)
            argument_text = query_parts[1].strip() if len(query_parts) == 2 else ""
            if candidate.name == "read_file" and "path" not in execution_kwargs:
                for prefix in ("file ", "file:"):
                    if argument_text.lower().startswith(prefix):
                        argument_text = argument_text[len(prefix):].strip()
                        break
                if argument_text:
                    execution_kwargs["path"] = argument_text
            elif candidate.name == "file_info" and "path" not in execution_kwargs:
                for prefix in ("information ", "info ", "for "):
                    if argument_text.lower().startswith(prefix):
                        argument_text = argument_text[len(prefix):].strip()
                        break
                if argument_text:
                    execution_kwargs["path"] = argument_text
            elif candidate.name == "list_directory" and "path" not in execution_kwargs:
                for prefix in ("directory ", "directory:", "files "):
                    if argument_text.lower().startswith(prefix):
                        argument_text = argument_text[len(prefix):].strip()
                        break
                if argument_text:
                    execution_kwargs["path"] = argument_text
            elif candidate.name == "search_local_files" and "query" not in execution_kwargs:
                for prefix in ("text ", "files ", "for "):
                    if argument_text.lower().startswith(prefix):
                        argument_text = argument_text[len(prefix):].strip()
                        break
                if argument_text:
                    execution_kwargs["query"] = argument_text

        # Deterministic argument binding for protected project tools.
        # The parser only extracts explicit natural-language arguments; it
        # never creates or upgrades permission.
        if not candidate.read_only:
            normalized = discovery_query.strip()
            parts = normalized.split(maxsplit=2)
            remainder = parts[2].strip() if len(parts) == 3 else ""

            if candidate.name == "delete_file" and "path" not in execution_kwargs:
                execution_kwargs["path"] = remainder

            elif candidate.name == "write_file":
                if "path" not in execution_kwargs or "content" not in execution_kwargs:
                    if " with " in remainder.lower():
                        path_text, content_text = remainder.split(
                            " with ", 1
                        )
                    elif " content " in remainder.lower():
                        path_text, content_text = remainder.split(
                            " content ", 1
                        )
                    else:
                        path_text, content_text = remainder, ""
                    if "path" not in execution_kwargs:
                        execution_kwargs["path"] = path_text.strip()
                    if "content" not in execution_kwargs:
                        execution_kwargs["content"] = content_text

            elif candidate.name == "run_command" and "command" not in execution_kwargs:
                execution_kwargs["command"] = remainder

            execution_kwargs["_permission_granted"] = True
            execution_kwargs["_confirmation_provided"] = user_confirmation

        execution: ToolExecutionResult = (
            self.executor.execute(
                candidate.name,
                **execution_kwargs,
            )
        )

        return ToolInvocationResult(
            tool=candidate.name,
            allowed=True,
            requires_confirmation=False,
            success=execution.success,
            result=execution.result,
            error=execution.error,
            risk=permission.risk,
            reason=(
                permission.reason
                if execution.success
                else (
                    execution.error
                    or permission.reason
                )
            ),
        )
