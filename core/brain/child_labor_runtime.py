from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LaborAction(str, Enum):
    THINK = "think"
    READ = "read"
    PLAN = "plan"
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

    CONSTITUTIONAL_CHANGE = "constitutional_change"
    SOUL_CHANGE = "soul_change"


class LaborDecision(str, Enum):
    ALLOW_COGNITION = "allow_cognition"
    REQUIRE_CHILD_AUTHORITY = "require_child_authority"
    REQUIRE_MOTHER_AUTHORITY = "require_mother_authority"
    REQUIRE_HUMAN_AUTHORITY = "require_human_authority"
    DENY = "deny"


@dataclass(frozen=True)
class LaborRuntimeResult:
    allowed: bool
    decision: LaborDecision
    reason: str


class ChildLaborRuntime:
    VERSION = "1.0"

    AUTONOMOUS_ACTIONS = {
        LaborAction.THINK,
        LaborAction.READ,
        LaborAction.PLAN,
        LaborAction.PROPOSE,
    }

    PROTECTED_ACTIONS = {
        LaborAction.WRITE,
        LaborAction.DELETE,
        LaborAction.EXECUTE,
        LaborAction.NETWORK,
        LaborAction.CREDENTIAL,
        LaborAction.SYSTEM_CHANGE,
        LaborAction.FINANCIAL,
        LaborAction.SELF_UPDATE,
        LaborAction.EXTERNAL_CONTROL,
    }

    HUMAN_ONLY_ACTIONS = {
        LaborAction.FINANCIAL,
        LaborAction.CONSTITUTIONAL_CHANGE,
        LaborAction.SOUL_CHANGE,
    }

    def evaluate(
        self,
        action: LaborAction,
        child_authority_approved: bool = False,
        mother_authority_approved: bool = False,
        human_authority_approved: bool = False,
    ) -> LaborRuntimeResult:

        if action in self.AUTONOMOUS_ACTIONS:
            return LaborRuntimeResult(
                True,
                LaborDecision.ALLOW_COGNITION,
                "labor cognition is allowed independently",
            )

        if action in self.HUMAN_ONLY_ACTIONS:
            if not human_authority_approved:
                return LaborRuntimeResult(
                    False,
                    LaborDecision.REQUIRE_HUMAN_AUTHORITY,
                    "human authority required",
                )

            return LaborRuntimeResult(
                True,
                LaborDecision.REQUIRE_HUMAN_AUTHORITY,
                "human authority approved",
            )

        if action in self.PROTECTED_ACTIONS:
            if action == LaborAction.FINANCIAL:
                if not child_authority_approved:
                    return LaborRuntimeResult(
                        False,
                        LaborDecision.REQUIRE_CHILD_AUTHORITY,
                        "child authority required before financial action",
                    )

                if not mother_authority_approved:
                    return LaborRuntimeResult(
                        False,
                        LaborDecision.REQUIRE_MOTHER_AUTHORITY,
                        "mother authority required before financial action",
                    )

                if not human_authority_approved:
                    return LaborRuntimeResult(
                        False,
                        LaborDecision.REQUIRE_HUMAN_AUTHORITY,
                        "human authority required before financial action",
                    )

                return LaborRuntimeResult(
                    True,
                    LaborDecision.REQUIRE_HUMAN_AUTHORITY,
                    "financial action fully authorized",
                )

            if not child_authority_approved:
                return LaborRuntimeResult(
                    False,
                    LaborDecision.REQUIRE_CHILD_AUTHORITY,
                    "child authority required",
                )

            return LaborRuntimeResult(
                True,
                LaborDecision.REQUIRE_CHILD_AUTHORITY,
                "child authority approved",
            )

        return LaborRuntimeResult(
            False,
            LaborDecision.DENY,
            "unknown labor action denied",
        )

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

    def can_modify_own_soul(self) -> bool:
        return False

    def can_modify_own_constitution(self) -> bool:
        return False

    def can_execute_without_authority(self) -> bool:
        return False

    def can_execute_tools(self) -> bool:
        return False
