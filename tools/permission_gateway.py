from __future__ import annotations

from dataclasses import dataclass

from core.policies.approval import (
    ActionType,
    PermissionDecision,
    PermissionEngine,
)
from tools.registry import ToolRegistry


@dataclass(frozen=True)
class ToolPermissionDecision:
    """
    Permission result for a tool request.

    This object does not execute the tool.
    It only records whether execution is
    currently permitted.
    """

    tool: str
    action: ActionType
    allowed: bool
    requires_confirmation: bool
    risk: str
    reason: str


class ToolPermissionGateway:
    """
    Permission boundary between SAHIBEX tools
    and the central PermissionEngine.

    The gateway:
    - verifies that the tool is registered
    - classifies the tool request
    - asks the existing PermissionEngine
    - returns the permission decision
    - never executes the tool
    - never grants permission by itself
    """

    DEFAULT_READ_ACTION = ActionType.READ_FILE

    def __init__(
        self,
        permission_engine: PermissionEngine,
        registry: ToolRegistry,
    ) -> None:
        if not isinstance(
            permission_engine,
            PermissionEngine,
        ):
            raise TypeError(
                "permission_engine must be PermissionEngine"
            )

        if not isinstance(
            registry,
            ToolRegistry,
        ):
            raise TypeError(
                "registry must be ToolRegistry"
            )

        self.permission_engine = permission_engine
        self.registry = registry

    def action_for_tool(
        self,
        tool_name: str,
    ) -> ActionType:
        """
        Map a registered read-only tool
        to the existing READ_FILE permission class.
        """

        if not tool_name.strip():
            raise ValueError(
                "tool_name cannot be empty."
            )

        if not self.registry.has(tool_name):
            raise KeyError(
                f"Unknown SAHIBEX tool: {tool_name}"
            )

        tool = self.registry.get(tool_name)

        if tool.read_only:
            return self.DEFAULT_READ_ACTION

        if tool.protected_action is not None:
            return tool.protected_action

        raise PermissionError(
            f"Tool has no protected action classification: {tool_name}"
        )

    def check(
        self,
        tool_name: str,
        *,
        confirmation: bool = False,
    ) -> ToolPermissionDecision:
        """
        Check whether a registered tool request
        is permitted.

        No tool execution happens here.
        """

        action = self.action_for_tool(tool_name)

        decision: PermissionDecision = (
            self.permission_engine.check(
                action,
                confirmation=confirmation,
            )
        )

        return ToolPermissionDecision(
            tool=tool_name,
            action=action,
            allowed=decision.allowed,
            requires_confirmation=(
                decision.requires_confirmation
            ),
            risk=decision.risk.value,
            reason=decision.reason,
        )

    def require(
        self,
        tool_name: str,
        *,
        confirmation: bool = False,
    ) -> ToolPermissionDecision:
        """
        Require permission for a registered tool.

        Raises PermissionError when the existing
        PermissionEngine does not allow the action.
        """

        result = self.check(
            tool_name,
            confirmation=confirmation,
        )

        if not result.allowed:
            raise PermissionError(
                f"Tool permission blocked for "
                f"{tool_name}: {result.reason}"
            )

        return result
