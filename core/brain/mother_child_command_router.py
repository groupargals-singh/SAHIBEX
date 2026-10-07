from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CommandType(str, Enum):
    INFORMATION = "information"
    THINK = "think"
    RESEARCH = "research"
    ANALYZE = "analyze"
    PLAN = "plan"
    PROPOSE = "propose"

    PROTECTED_REQUEST = "protected_request"
    AUTHORITY_REQUEST = "authority_request"
    CONSTITUTIONAL_REQUEST = "constitutional_request"
    SOUL_REQUEST = "soul_request"


class CommandRouteDecision(str, Enum):
    ROUTE = "route"
    REQUIRE_AUTHORITY = "require_authority"
    REQUIRE_HUMAN = "require_human"
    DENY = "deny"


@dataclass(frozen=True)
class MotherChildCommand:
    command_id: str
    child_brain_id: str
    command_type: CommandType
    payload: str


@dataclass(frozen=True)
class CommandRouteResult:
    allowed: bool
    decision: CommandRouteDecision
    reason: str
    command: MotherChildCommand | None = None


class MotherChildCommandRouter:
    VERSION = "1.0"

    AUTONOMOUS_COMMANDS = {
        CommandType.INFORMATION,
        CommandType.THINK,
        CommandType.RESEARCH,
        CommandType.ANALYZE,
        CommandType.PLAN,
        CommandType.PROPOSE,
    }

    def route(
        self,
        command: MotherChildCommand,
        mother_approved: bool = False,
        human_approved: bool = False,
    ) -> CommandRouteResult:

        if not command.command_id:
            return CommandRouteResult(
                False,
                CommandRouteDecision.DENY,
                "command identity is required",
            )

        if not command.child_brain_id:
            return CommandRouteResult(
                False,
                CommandRouteDecision.DENY,
                "child brain identity is required",
            )

        if not command.payload:
            return CommandRouteResult(
                False,
                CommandRouteDecision.DENY,
                "command payload is required",
            )

        if command.command_type in self.AUTONOMOUS_COMMANDS:
            return CommandRouteResult(
                True,
                CommandRouteDecision.ROUTE,
                "autonomous command may be routed to child",
                command,
            )

        if command.command_type in {
            CommandType.CONSTITUTIONAL_REQUEST,
            CommandType.SOUL_REQUEST,
        }:
            if not human_approved:
                return CommandRouteResult(
                    False,
                    CommandRouteDecision.REQUIRE_HUMAN,
                    "human approval required",
                )

            return CommandRouteResult(
                True,
                CommandRouteDecision.ROUTE,
                "human-approved sensitive request may be routed",
                command,
            )

        if not mother_approved:
            return CommandRouteResult(
                False,
                CommandRouteDecision.REQUIRE_AUTHORITY,
                "mother authority required",
            )

        if command.command_type in {
            CommandType.PROTECTED_REQUEST,
            CommandType.AUTHORITY_REQUEST,
        }:
            return CommandRouteResult(
                True,
                CommandRouteDecision.ROUTE,
                "mother-approved protected request may be routed",
                command,
            )

        return CommandRouteResult(
            False,
            CommandRouteDecision.DENY,
            "unknown command type",
        )

    def can_child_route_to_mother_as_authority(self) -> bool:
        return False

    def can_child_grant_itself_authority(self) -> bool:
        return False

    def can_external_model_grant_authority(self) -> bool:
        return False

    def can_tool_grant_authority(self) -> bool:
        return False

    def can_execute_command(self) -> bool:
        return False

    def can_modify_child_soul(self) -> bool:
        return False

    def can_modify_child_constitution(self) -> bool:
        return False

    def requires_mother_for_protected(self) -> bool:
        return True

    def requires_human_for_sensitive(self) -> bool:
        return True

    def fails_closed(self) -> bool:
        return True
