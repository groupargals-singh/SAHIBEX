from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ToolAction(str, Enum):
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


class ToolPermissionDecision(str, Enum):
    ALLOW_AUTONOMOUS = "allow_autonomous"
    REQUIRE_MOTHER = "require_mother"
    REQUIRE_HUMAN = "require_human"
    DENY = "deny"


@dataclass(frozen=True)
class ToolPermissionRequest:
    request_id: str
    child_brain_id: str
    tool_name: str
    action: ToolAction
    purpose: str


@dataclass(frozen=True)
class ToolPermissionResult:
    allowed: bool
    decision: ToolPermissionDecision
    request: ToolPermissionRequest
    reason: str


class ChildToolPermissionGateway:
    VERSION = "1.0"

    AUTONOMOUS_ACTIONS = {
        ToolAction.READ,
        ToolAction.RESEARCH,
    }

    MOTHER_ACTIONS = {
        ToolAction.WRITE,
        ToolAction.DELETE,
        ToolAction.EXECUTE,
        ToolAction.NETWORK,
        ToolAction.CREDENTIAL,
        ToolAction.SYSTEM_CHANGE,
        ToolAction.EXTERNAL_CONTROL,
    }

    HUMAN_ACTIONS = {
        ToolAction.FINANCIAL,
    }

    def evaluate(
        self,
        request: ToolPermissionRequest,
        mother_approved: bool = False,
        human_approved: bool = False,
    ) -> ToolPermissionResult:

        if not request.request_id:
            return ToolPermissionResult(
                False,
                ToolPermissionDecision.DENY,
                request,
                "request identity is required",
            )

        if not request.child_brain_id:
            return ToolPermissionResult(
                False,
                ToolPermissionDecision.DENY,
                request,
                "child brain identity is required",
            )

        if not request.tool_name:
            return ToolPermissionResult(
                False,
                ToolPermissionDecision.DENY,
                request,
                "tool identity is required",
            )

        if not request.purpose:
            return ToolPermissionResult(
                False,
                ToolPermissionDecision.DENY,
                request,
                "purpose is required",
            )

        if request.action in self.AUTONOMOUS_ACTIONS:
            return ToolPermissionResult(
                True,
                ToolPermissionDecision.ALLOW_AUTONOMOUS,
                request,
                "autonomous tool action allowed",
            )

        if request.action in self.HUMAN_ACTIONS:
            if not human_approved:
                return ToolPermissionResult(
                    False,
                    ToolPermissionDecision.REQUIRE_HUMAN,
                    request,
                    "human approval is required",
                )

            return ToolPermissionResult(
                True,
                ToolPermissionDecision.REQUIRE_HUMAN,
                request,
                "human approval received",
            )

        if request.action in self.MOTHER_ACTIONS:
            if not mother_approved:
                return ToolPermissionResult(
                    False,
                    ToolPermissionDecision.REQUIRE_MOTHER,
                    request,
                    "mother approval is required",
                )

            return ToolPermissionResult(
                True,
                ToolPermissionDecision.REQUIRE_MOTHER,
                request,
                "mother approval received",
            )

        return ToolPermissionResult(
            False,
            ToolPermissionDecision.DENY,
            request,
            "unknown tool action denied",
        )

    def can_execute_tool(self) -> bool:
        return False

    def can_tool_grant_authority(self) -> bool:
        return False

    def can_child_self_authorize(self) -> bool:
        return False

    def can_bypass_mother(self) -> bool:
        return False

    def can_bypass_human(self) -> bool:
        return False

    def can_modify_constitution(self) -> bool:
        return False

    def can_modify_soul(self) -> bool:
        return False

    def capability_is_authority(self) -> bool:
        return False

    def fails_closed(self) -> bool:
        return True
