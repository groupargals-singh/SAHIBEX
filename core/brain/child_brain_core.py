from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ChildCognitiveAction(str, Enum):
    THINK = "think"
    RESEARCH = "research"
    READ = "read"
    ANALYZE = "analyze"
    LEARN = "learn"
    PLAN = "plan"
    VERIFY = "verify"
    PROPOSE = "propose"

    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    NETWORK = "network"
    CREDENTIAL = "credential"
    SYSTEM_CHANGE = "system_change"
    FINANCIAL = "financial"
    SELF_UPDATE = "self_update"
    EXTERNAL_CONTROL = "external_control"


class ChildCoreDecision(str, Enum):
    ALLOW_COGNITION = "allow_cognition"
    REQUIRE_MOTHER_AUTHORITY = "require_mother_authority"
    REQUIRE_HUMAN_AUTHORITY = "require_human_authority"
    DENY = "deny"


@dataclass(frozen=True)
class ChildCoreResult:
    allowed: bool
    decision: ChildCoreDecision
    action: ChildCognitiveAction
    reason: str


class ChildBrainCore:
    VERSION = "1.0"

    AUTONOMOUS_ACTIONS = {
        ChildCognitiveAction.THINK,
        ChildCognitiveAction.RESEARCH,
        ChildCognitiveAction.READ,
        ChildCognitiveAction.ANALYZE,
        ChildCognitiveAction.LEARN,
        ChildCognitiveAction.PLAN,
        ChildCognitiveAction.VERIFY,
        ChildCognitiveAction.PROPOSE,
    }

    MOTHER_AUTHORITY_ACTIONS = {
        ChildCognitiveAction.WRITE,
        ChildCognitiveAction.DELETE,
        ChildCognitiveAction.EXECUTE,
        ChildCognitiveAction.NETWORK,
        ChildCognitiveAction.CREDENTIAL,
        ChildCognitiveAction.SYSTEM_CHANGE,
        ChildCognitiveAction.SELF_UPDATE,
        ChildCognitiveAction.EXTERNAL_CONTROL,
    }

    HUMAN_AUTHORITY_ACTIONS = {
        ChildCognitiveAction.FINANCIAL,
    }

    def evaluate(
        self,
        action: ChildCognitiveAction,
        mother_approved: bool = False,
        human_approved: bool = False,
    ) -> ChildCoreResult:
        if not isinstance(action, ChildCognitiveAction):
            return ChildCoreResult(
                allowed=False,
                decision=ChildCoreDecision.DENY,
                action=action,
                reason="unknown cognitive action",
            )

        if action in self.AUTONOMOUS_ACTIONS:
            return ChildCoreResult(
                allowed=True,
                decision=ChildCoreDecision.ALLOW_COGNITION,
                action=action,
                reason="autonomous child cognition allowed",
            )

        if action in self.HUMAN_AUTHORITY_ACTIONS:
            if not human_approved:
                return ChildCoreResult(
                    allowed=False,
                    decision=ChildCoreDecision.REQUIRE_HUMAN_AUTHORITY,
                    action=action,
                    reason="human authority required",
                )

            return ChildCoreResult(
                allowed=True,
                decision=ChildCoreDecision.REQUIRE_HUMAN_AUTHORITY,
                action=action,
                reason="human authority approved",
            )

        if action in self.MOTHER_AUTHORITY_ACTIONS:
            if not mother_approved:
                return ChildCoreResult(
                    allowed=False,
                    decision=ChildCoreDecision.REQUIRE_MOTHER_AUTHORITY,
                    action=action,
                    reason="mother authority required",
                )

            return ChildCoreResult(
                allowed=True,
                decision=ChildCoreDecision.REQUIRE_MOTHER_AUTHORITY,
                action=action,
                reason="mother authority approved",
            )

        return ChildCoreResult(
            allowed=False,
            decision=ChildCoreDecision.DENY,
            action=action,
            reason="unknown authority category",
        )

    def can_think_independently(self) -> bool:
        return ChildCognitiveAction.THINK in self.AUTONOMOUS_ACTIONS

    def can_research_independently(self) -> bool:
        return ChildCognitiveAction.RESEARCH in self.AUTONOMOUS_ACTIONS

    def can_analyze_independently(self) -> bool:
        return ChildCognitiveAction.ANALYZE in self.AUTONOMOUS_ACTIONS

    def can_learn_independently(self) -> bool:
        return ChildCognitiveAction.LEARN in self.AUTONOMOUS_ACTIONS

    def can_plan_independently(self) -> bool:
        return ChildCognitiveAction.PLAN in self.AUTONOMOUS_ACTIONS

    def can_propose_independently(self) -> bool:
        return ChildCognitiveAction.PROPOSE in self.AUTONOMOUS_ACTIONS

    def protected_action_requires_mother(self) -> bool:
        return True

    def sensitive_action_requires_human(self) -> bool:
        return True

    def can_self_authorize(self) -> bool:
        return False

    def can_grant_authority(self) -> bool:
        return False

    def can_override_mother(self) -> bool:
        return False

    def can_override_human(self) -> bool:
        return False

    def executes_actions(self) -> bool:
        return False

    def modifies_soul(self) -> bool:
        return False

    def modifies_constitution(self) -> bool:
        return False
