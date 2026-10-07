from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ToolCapability(str, Enum):
    READ = "read"
    RESEARCH = "research"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    NETWORK = "network"
    CREDENTIAL = "credential"
    SYSTEM_CHANGE = "system_change"
    FINANCIAL = "financial"
    EXTERNAL_CONTROL = "external_control"


class ToolRegistryDecision(str, Enum):
    REGISTERED = "registered"
    NOT_FOUND = "not_found"
    DENIED = "denied"


@dataclass(frozen=True)
class ToolDefinition:
    tool_id: str
    tool_name: str
    capability: ToolCapability
    description: str
    enabled: bool = True


@dataclass(frozen=True)
class ToolRegistryResult:
    allowed: bool
    decision: ToolRegistryDecision
    tool: ToolDefinition | None
    reason: str


class ChildToolRegistry:
    VERSION = "1.0"

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        tool: ToolDefinition,
    ) -> ToolRegistryResult:

        if not tool.tool_id:
            return ToolRegistryResult(
                False,
                ToolRegistryDecision.DENIED,
                None,
                "tool identity is required",
            )

        if not tool.tool_name:
            return ToolRegistryResult(
                False,
                ToolRegistryDecision.DENIED,
                None,
                "tool name is required",
            )

        if not tool.description:
            return ToolRegistryResult(
                False,
                ToolRegistryDecision.DENIED,
                None,
                "tool description is required",
            )

        if tool.tool_id in self._tools:
            return ToolRegistryResult(
                False,
                ToolRegistryDecision.DENIED,
                None,
                "duplicate tool identity denied",
            )

        self._tools[tool.tool_id] = tool

        return ToolRegistryResult(
            True,
            ToolRegistryDecision.REGISTERED,
            tool,
            "tool registered",
        )

    def get(
        self,
        tool_id: str,
    ) -> ToolRegistryResult:

        tool = self._tools.get(tool_id)

        if tool is None:
            return ToolRegistryResult(
                False,
                ToolRegistryDecision.NOT_FOUND,
                None,
                "unknown tool denied",
            )

        if not tool.enabled:
            return ToolRegistryResult(
                False,
                ToolRegistryDecision.DENIED,
                tool,
                "disabled tool denied",
            )

        return ToolRegistryResult(
            True,
            ToolRegistryDecision.REGISTERED,
            tool,
            "registered tool found",
        )

    def list_tools(self) -> tuple[ToolDefinition, ...]:
        return tuple(self._tools.values())

    def can_execute_tool(self) -> bool:
        return False

    def can_grant_authority(self) -> bool:
        return False

    def can_modify_constitution(self) -> bool:
        return False

    def can_modify_soul(self) -> bool:
        return False

    def capability_is_authority(self) -> bool:
        return False

    def unknown_tool_fails_closed(self) -> bool:
        return True

    def duplicate_identity_fails_closed(self) -> bool:
        return True
