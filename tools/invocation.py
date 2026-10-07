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
        # Only protected tools receive the private marker after the
        # PermissionGateway returns allowed=True.
        if not candidate.read_only:
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
