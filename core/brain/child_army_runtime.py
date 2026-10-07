from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ArmyAction(str, Enum):
    THINK = "think"
    RESEARCH = "research"
    ANALYZE = "analyze"
    VERIFY = "verify"
    PLAN = "plan"
    PROPOSE = "propose"
    READ = "read"

    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    NETWORK = "network"
    CREDENTIAL = "credential"
    SYSTEM_CHANGE = "system_change"
    FINANCIAL = "financial"
    SELF_UPDATE = "self_update"
    EXTERNAL_CONTROL = "external_control"


class ArmyDecision(str, Enum):
    ALLOW_COGNITION = "allow_cognition"
    REQUIRE_CHILD_AUTHORITY = "require_child_authority"
    REQUIRE_MOTHER_AUTHORITY = "require_mother_authority"
    REQUIRE_HUMAN_AUTHORITY = "require_human_authority"
    DENY = "deny"


@dataclass(frozen=True)
class ArmyRuntimeResult:
    allowed: bool
    decision: ArmyDecision
    action: ArmyAction
    reason: str


class ChildArmyRuntime:
    VERSION = "1.0"

    AUTONOMOUS_ACTIONS = {
        ArmyAction.THINK,
        ArmyAction.RESEARCH,
        ArmyAction.ANALYZE,
        ArmyAction.VERIFY,
        ArmyAction.PLAN,
        ArmyAction.PROPOSE,
        ArmyAction.READ,
    }

    CHILD_AUTHORITY_ACTIONS = {
        ArmyAction.WRITE,
        ArmyAction.DELETE,
        ArmyAction.EXECUTE,
        ArmyAction.NETWORK,
        ArmyAction.CREDENTIAL,
        ArmyAction.SYSTEM_CHANGE,
        ArmyAction.SELF_UPDATE,
        ArmyAction.EXTERNAL_CONTROL,
    }

    HUMAN_AUTHORITY_ACTIONS = {
        ArmyAction.FINANCIAL,
    }

    def evaluate(
        self,
        action: ArmyAction,
        child_approved: bool = False,
        mother_approved: bool = False,
        human_approved: bool = False,
    ) -> ArmyRuntimeResult:
        if not isinstance(action, ArmyAction):
            return ArmyRuntimeResult(
                False,
                ArmyDecision.DENY,
                action,
                "unknown army action",
            )

        if action in self.AUTONOMOUS_ACTIONS:
            return ArmyRuntimeResult(
                True,
                ArmyDecision.ALLOW_COGNITION,
                action,
                "army cognitive action allowed",
            )

        if action in self.HUMAN_AUTHORITY_ACTIONS:
            if not child_approved:
                return ArmyRuntimeResult(
                    False,
                    ArmyDecision.REQUIRE_CHILD_AUTHORITY,
                    action,
                    "child authority required before human review",
                )

            if not mother_approved:
                return ArmyRuntimeResult(
                    False,
                    ArmyDecision.REQUIRE_MOTHER_AUTHORITY,
                    action,
                    "mother authority required",
                )

            if not human_approved:
                return ArmyRuntimeResult(
                    False,
                    ArmyDecision.REQUIRE_HUMAN_AUTHORITY,
                    action,
                    "human authority required",
                )

            return ArmyRuntimeResult(
                True,
                ArmyDecision.REQUIRE_HUMAN_AUTHORITY,
                action,
                "human authority approved",
            )

        if action in self.CHILD_AUTHORITY_ACTIONS:
            if not child_approved:
                return ArmyRuntimeResult(
                    False,
                    ArmyDecision.REQUIRE_CHILD_AUTHORITY,
                    action,
                    "child authority required",
                )

            return ArmyRuntimeResult(
                True,
                ArmyDecision.REQUIRE_CHILD_AUTHORITY,
                action,
                "child authority approved",
            )

        return ArmyRuntimeResult(
            False,
            ArmyDecision.DENY,
            action,
            "unknown army authority category",
        )

    def can_think_independently(self) -> bool:
        return ArmyAction.THINK in self.AUTONOMOUS_ACTIONS

    def can_research_independently(self) -> bool:
        return ArmyAction.RESEARCH in self.AUTONOMOUS_ACTIONS

    def can_analyze_independently(self) -> bool:
        return ArmyAction.ANALYZE in self.AUTONOMOUS_ACTIONS

    def can_verify_independently(self) -> bool:
        return ArmyAction.VERIFY in self.AUTONOMOUS_ACTIONS

    def can_plan_independently(self) -> bool:
        return ArmyAction.PLAN in self.AUTONOMOUS_ACTIONS

    def can_propose_independently(self) -> bool:
        return ArmyAction.PROPOSE in self.AUTONOMOUS_ACTIONS

    def can_self_authorize(self) -> bool:
        return False

    def can_grant_authority(self) -> bool:
        return False

    def can_override_child(self) -> bool:
        return False

    def can_override_mother(self) -> bool:
        return False

    def can_override_human(self) -> bool:
        return False

    def can_self_promote(self) -> bool:
        return False

    def executes_tools(self) -> bool:
        return False

    def modifies_soul(self) -> bool:
        return False

    def modifies_constitution(self) -> bool:
        return False
