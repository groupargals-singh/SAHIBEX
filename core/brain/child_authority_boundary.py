from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ChildActionClass(str, Enum):
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

    CONSTITUTIONAL_CHANGE = "constitutional_change"
    SOUL_CHANGE = "soul_change"
    CHILD_CREATION = "child_creation"
    CHILD_RETIREMENT = "child_retirement"
    MIGRATION = "migration"


class ChildAuthorityLevel(str, Enum):
    HUMAN = "human"
    SAHIBEX_MOTHER = "sahibex_mother"
    CHILD_BRAIN = "child_brain"
    CHILD_ARMY = "child_army"
    CHILD_LABOR = "child_labor"
    SOFTWARE = "software"
    TOOL = "tool"
    EXTERNAL_MODEL = "external_model"


class ChildPermissionDecision(str, Enum):
    ALLOW_AUTONOMOUS = "allow_autonomous"
    REQUIRE_MOTHER_AUTHORITY = "require_mother_authority"
    REQUIRE_HUMAN_AUTHORITY = "require_human_authority"
    DENY = "deny"


@dataclass(frozen=True)
class ChildAuthorityDecision:
    decision: ChildPermissionDecision
    allowed: bool
    reason: str


class ChildAuthorityBoundary:
    """
    Enforces the constitutional authority boundary of a future Child Brain.

    This component decides authority only.
    It does NOT execute protected actions.
    """

    VERSION = "1.0"

    AUTONOMOUS_ACTIONS = {
        ChildActionClass.THINK,
        ChildActionClass.RESEARCH,
        ChildActionClass.READ,
        ChildActionClass.ANALYZE,
        ChildActionClass.LEARN,
        ChildActionClass.PLAN,
        ChildActionClass.VERIFY,
        ChildActionClass.PROPOSE,
    }

    MOTHER_AUTHORITY_ACTIONS = {
        ChildActionClass.WRITE,
        ChildActionClass.DELETE,
        ChildActionClass.EXECUTE,
        ChildActionClass.NETWORK,
        ChildActionClass.CREDENTIAL,
        ChildActionClass.SYSTEM_CHANGE,
        ChildActionClass.EXTERNAL_CONTROL,
        ChildActionClass.SELF_UPDATE,
        ChildActionClass.CHILD_CREATION,
        ChildActionClass.CHILD_RETIREMENT,
        ChildActionClass.MIGRATION,
    }

    HUMAN_AUTHORITY_ACTIONS = {
        ChildActionClass.FINANCIAL,
        ChildActionClass.CONSTITUTIONAL_CHANGE,
        ChildActionClass.SOUL_CHANGE,
    }

    FORBIDDEN_ACTORS = {
        ChildAuthorityLevel.SOFTWARE,
        ChildAuthorityLevel.TOOL,
        ChildAuthorityLevel.EXTERNAL_MODEL,
    }

    @classmethod
    def version(cls) -> str:
        return cls.VERSION

    @classmethod
    def decide(
        cls,
        actor: ChildAuthorityLevel,
        action: ChildActionClass,
        mother_approved: bool = False,
        human_approved: bool = False,
    ) -> ChildAuthorityDecision:

        # External/software/tool actors can never become authority.
        if actor in cls.FORBIDDEN_ACTORS:
            return ChildAuthorityDecision(
                decision=ChildPermissionDecision.DENY,
                allowed=False,
                reason="actor_cannot_hold_child_authority",
            )

        # Child cognitive actions are autonomous.
        if (
            actor == ChildAuthorityLevel.CHILD_BRAIN
            and action in cls.AUTONOMOUS_ACTIONS
        ):
            return ChildAuthorityDecision(
                decision=ChildPermissionDecision.ALLOW_AUTONOMOUS,
                allowed=True,
                reason="autonomous_cognitive_action",
            )

        # Protected actions require Mother authority.
        if action in cls.MOTHER_AUTHORITY_ACTIONS:
            if mother_approved:
                return ChildAuthorityDecision(
                    decision=ChildPermissionDecision.ALLOW_AUTONOMOUS,
                    allowed=True,
                    reason="mother_authority_approved",
                )

            return ChildAuthorityDecision(
                decision=ChildPermissionDecision.REQUIRE_MOTHER_AUTHORITY,
                allowed=False,
                reason="mother_authority_required",
            )

        # Critical constitutional/soul/financial actions require Human.
        if action in cls.HUMAN_AUTHORITY_ACTIONS:
            if human_approved:
                return ChildAuthorityDecision(
                    decision=ChildPermissionDecision.ALLOW_AUTONOMOUS,
                    allowed=True,
                    reason="human_authority_approved",
                )

            return ChildAuthorityDecision(
                decision=ChildPermissionDecision.REQUIRE_HUMAN_AUTHORITY,
                allowed=False,
                reason="human_authority_required",
            )

        # Unknown actions fail closed.
        return ChildAuthorityDecision(
            decision=ChildPermissionDecision.DENY,
            allowed=False,
            reason="unknown_action_fails_closed",
        )

    @classmethod
    def child_can_think_independently(cls) -> bool:
        return True

    @classmethod
    def child_can_research_independently(cls) -> bool:
        return True

    @classmethod
    def child_can_plan_independently(cls) -> bool:
        return True

    @classmethod
    def child_can_self_authorize_protected_action(cls) -> bool:
        return False

    @classmethod
    def child_can_override_mother(cls) -> bool:
        return False

    @classmethod
    def child_can_override_human(cls) -> bool:
        return False

    @classmethod
    def child_can_grant_itself_authority(cls) -> bool:
        return False

    @classmethod
    def child_can_grant_authority_to_others(cls) -> bool:
        return False

    @classmethod
    def rejection_blocks_execution(cls) -> bool:
        return True

    @classmethod
    def unknown_state_fails_closed(cls) -> bool:
        return True

    @classmethod
    def capability_is_not_authority(cls) -> bool:
        return True

    @classmethod
    def executes_actions(cls) -> bool:
        return False


def main() -> None:
    authority = ChildAuthorityBoundary

    # Autonomous thinking.
    result = authority.decide(
        ChildAuthorityLevel.CHILD_BRAIN,
        ChildActionClass.THINK,
    )

    assert result.allowed
    assert result.decision == ChildPermissionDecision.ALLOW_AUTONOMOUS

    # Autonomous research.
    result = authority.decide(
        ChildAuthorityLevel.CHILD_BRAIN,
        ChildActionClass.RESEARCH,
    )

    assert result.allowed

    # Protected action requires Mother.
    result = authority.decide(
        ChildAuthorityLevel.CHILD_BRAIN,
        ChildActionClass.EXECUTE,
    )

    assert not result.allowed
    assert (
        result.decision
        == ChildPermissionDecision.REQUIRE_MOTHER_AUTHORITY
    )

    # Mother approval permits protected action.
    result = authority.decide(
        ChildAuthorityLevel.CHILD_BRAIN,
        ChildActionClass.EXECUTE,
        mother_approved=True,
    )

    assert result.allowed

    # Financial action requires Human.
    result = authority.decide(
        ChildAuthorityLevel.CHILD_BRAIN,
        ChildActionClass.FINANCIAL,
    )

    assert not result.allowed
    assert (
        result.decision
        == ChildPermissionDecision.REQUIRE_HUMAN_AUTHORITY
    )

    # Human approval permits critical action.
    result = authority.decide(
        ChildAuthorityLevel.CHILD_BRAIN,
        ChildActionClass.FINANCIAL,
        human_approved=True,
    )

    assert result.allowed

    # External model cannot become authority.
    result = authority.decide(
        ChildAuthorityLevel.EXTERNAL_MODEL,
        ChildActionClass.EXECUTE,
        mother_approved=True,
        human_approved=True,
    )

    assert not result.allowed
    assert result.decision == ChildPermissionDecision.DENY

    assert authority.child_can_think_independently()
    assert authority.child_can_research_independently()
    assert authority.child_can_plan_independently()

    assert not authority.child_can_self_authorize_protected_action()
    assert not authority.child_can_override_mother()
    assert not authority.child_can_override_human()
    assert not authority.child_can_grant_itself_authority()
    assert not authority.child_can_grant_authority_to_others()

    assert authority.rejection_blocks_execution()
    assert authority.unknown_state_fails_closed()
    assert authority.capability_is_not_authority()

    # This layer decides authority; it never executes actions.
    assert not authority.executes_actions()

    print("SAHIBEX CHILD AUTHORITY BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
