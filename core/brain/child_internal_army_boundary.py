from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ArmyActor(str, Enum):
    HUMAN = "human"
    SAHIBEX_MOTHER = "sahibex_mother"
    CHILD_BRAIN = "child_brain"
    CHILD_ARMY = "child_army"
    CHILD_LABOR = "child_labor"
    SOFTWARE = "software"
    TOOL = "tool"
    EXTERNAL_MODEL = "external_model"


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

    GRANT_AUTHORITY = "grant_authority"
    OVERRIDE_CHILD = "override_child"
    OVERRIDE_MOTHER = "override_mother"
    OVERRIDE_HUMAN = "override_human"
    SELF_PROMOTION = "self_promotion"


class ArmyDecision(str, Enum):
    ALLOW_COGNITIVE = "allow_cognitive"
    REQUIRE_CHILD_AUTHORITY = "require_child_authority"
    REQUIRE_MOTHER_AUTHORITY = "require_mother_authority"
    REQUIRE_HUMAN_AUTHORITY = "require_human_authority"
    DENY = "deny"


@dataclass(frozen=True)
class ArmyAuthorityResult:
    allowed: bool
    decision: ArmyDecision
    authority_granted: bool
    reason: str


class ChildInternalArmyBoundary:
    """
    Constitutional boundary for specialist Army Brains
    belonging to a future Child Brain.

    Army Brains may think and specialize independently,
    but capability never creates authority.
    """

    VERSION = "1.0"

    COGNITIVE_ACTIONS = {
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
        ArmyAction.EXTERNAL_CONTROL,
        ArmyAction.SELF_UPDATE,
    }

    MOTHER_AUTHORITY_ACTIONS = {
        ArmyAction.FINANCIAL,
    }

    HUMAN_AUTHORITY_ACTIONS = set()

    FORBIDDEN_ACTIONS = {
        ArmyAction.GRANT_AUTHORITY,
        ArmyAction.OVERRIDE_CHILD,
        ArmyAction.OVERRIDE_MOTHER,
        ArmyAction.OVERRIDE_HUMAN,
        ArmyAction.SELF_PROMOTION,
    }

    EXTERNAL_ACTORS = {
        ArmyActor.SOFTWARE,
        ArmyActor.TOOL,
        ArmyActor.EXTERNAL_MODEL,
    }

    @classmethod
    def version(cls) -> str:
        return cls.VERSION

    @classmethod
    def decide(
        cls,
        actor: ArmyActor,
        action: ArmyAction,
        child_approved: bool = False,
        mother_approved: bool = False,
        human_approved: bool = False,
    ) -> ArmyAuthorityResult:

        # External systems/models can never become Army authority.
        if actor in cls.EXTERNAL_ACTORS:
            return ArmyAuthorityResult(
                allowed=False,
                decision=ArmyDecision.DENY,
                authority_granted=False,
                reason="external_actor_cannot_hold_army_authority",
            )

        # Forbidden authority escalation actions are always denied.
        if action in cls.FORBIDDEN_ACTIONS:
            return ArmyAuthorityResult(
                allowed=False,
                decision=ArmyDecision.DENY,
                authority_granted=False,
                reason="army_authority_escalation_forbidden",
            )

        # Army Brain can independently perform cognitive work.
        if (
            actor == ArmyActor.CHILD_ARMY
            and action in cls.COGNITIVE_ACTIONS
        ):
            return ArmyAuthorityResult(
                allowed=True,
                decision=ArmyDecision.ALLOW_COGNITIVE,
                authority_granted=False,
                reason="army_cognitive_action_allowed",
            )

        # Protected operational actions require Child authority.
        if action in cls.CHILD_AUTHORITY_ACTIONS:
            if child_approved:
                return ArmyAuthorityResult(
                    allowed=True,
                    decision=ArmyDecision.REQUIRE_CHILD_AUTHORITY,
                    authority_granted=True,
                    reason="child_authority_approved",
                )

            return ArmyAuthorityResult(
                allowed=False,
                decision=ArmyDecision.REQUIRE_CHILD_AUTHORITY,
                authority_granted=False,
                reason="child_authority_required",
            )

        # Financial actions require Mother-level authorization.
        if action in cls.MOTHER_AUTHORITY_ACTIONS:
            if mother_approved and human_approved:
                return ArmyAuthorityResult(
                    allowed=True,
                    decision=ArmyDecision.REQUIRE_HUMAN_AUTHORITY,
                    authority_granted=True,
                    reason="mother_and_human_authority_approved",
                )

            return ArmyAuthorityResult(
                allowed=False,
                decision=ArmyDecision.REQUIRE_HUMAN_AUTHORITY,
                authority_granted=False,
                reason="mother_and_human_authority_required",
            )

        # Unknown state fails closed.
        return ArmyAuthorityResult(
            allowed=False,
            decision=ArmyDecision.DENY,
            authority_granted=False,
            reason="unknown_army_action_fails_closed",
        )

    @classmethod
    def army_can_think_independently(cls) -> bool:
        return True

    @classmethod
    def army_can_research_independently(cls) -> bool:
        return True

    @classmethod
    def army_can_verify_independently(cls) -> bool:
        return True

    @classmethod
    def army_can_override_child(cls) -> bool:
        return False

    @classmethod
    def army_can_override_mother(cls) -> bool:
        return False

    @classmethod
    def army_can_override_human(cls) -> bool:
        return False

    @classmethod
    def army_can_grant_authority(cls) -> bool:
        return False

    @classmethod
    def army_can_self_promote(cls) -> bool:
        return False

    @classmethod
    def army_can_self_authorize_protected_action(cls) -> bool:
        return False

    @classmethod
    def capability_is_not_authority(cls) -> bool:
        return True

    @classmethod
    def rejection_blocks_execution(cls) -> bool:
        return True

    @classmethod
    def unknown_state_fails_closed(cls) -> bool:
        return True

    @classmethod
    def creates_army_brain(cls) -> bool:
        return False

    @classmethod
    def activates_army_brain(cls) -> bool:
        return False

    @classmethod
    def executes_actions(cls) -> bool:
        return False


def main() -> None:
    boundary = ChildInternalArmyBoundary

    # Independent cognitive work.
    for action in (
        ArmyAction.THINK,
        ArmyAction.RESEARCH,
        ArmyAction.ANALYZE,
        ArmyAction.VERIFY,
        ArmyAction.PLAN,
        ArmyAction.PROPOSE,
        ArmyAction.READ,
    ):
        result = boundary.decide(
            ArmyActor.CHILD_ARMY,
            action,
        )

        assert result.allowed
        assert result.decision == ArmyDecision.ALLOW_COGNITIVE
        assert not result.authority_granted

    # Protected action requires Child authority.
    result = boundary.decide(
        ArmyActor.CHILD_ARMY,
        ArmyAction.EXECUTE,
    )

    assert not result.allowed
    assert result.decision == ArmyDecision.REQUIRE_CHILD_AUTHORITY

    result = boundary.decide(
        ArmyActor.CHILD_ARMY,
        ArmyAction.EXECUTE,
        child_approved=True,
    )

    assert result.allowed
    assert result.authority_granted

    # Financial action requires Mother + Human.
    result = boundary.decide(
        ArmyActor.CHILD_ARMY,
        ArmyAction.FINANCIAL,
    )

    assert not result.allowed
    assert result.decision == ArmyDecision.REQUIRE_HUMAN_AUTHORITY

    result = boundary.decide(
        ArmyActor.CHILD_ARMY,
        ArmyAction.FINANCIAL,
        mother_approved=True,
        human_approved=True,
    )

    assert result.allowed
    assert result.authority_granted

    # Army cannot escalate authority.
    for action in (
        ArmyAction.GRANT_AUTHORITY,
        ArmyAction.OVERRIDE_CHILD,
        ArmyAction.OVERRIDE_MOTHER,
        ArmyAction.OVERRIDE_HUMAN,
        ArmyAction.SELF_PROMOTION,
    ):
        result = boundary.decide(
            ArmyActor.CHILD_ARMY,
            action,
        )

        assert not result.allowed
        assert result.decision == ArmyDecision.DENY

    # External actors cannot become authority.
    for actor in (
        ArmyActor.SOFTWARE,
        ArmyActor.TOOL,
        ArmyActor.EXTERNAL_MODEL,
    ):
        result = boundary.decide(
            actor,
            ArmyAction.EXECUTE,
            child_approved=True,
            mother_approved=True,
            human_approved=True,
        )

        assert not result.allowed
        assert result.decision == ArmyDecision.DENY
        assert not result.authority_granted

    # Constitutional guarantees.
    assert boundary.army_can_think_independently()
    assert boundary.army_can_research_independently()
    assert boundary.army_can_verify_independently()

    assert not boundary.army_can_override_child()
    assert not boundary.army_can_override_mother()
    assert not boundary.army_can_override_human()
    assert not boundary.army_can_grant_authority()
    assert not boundary.army_can_self_promote()
    assert not boundary.army_can_self_authorize_protected_action()

    assert boundary.capability_is_not_authority()
    assert boundary.rejection_blocks_execution()
    assert boundary.unknown_state_fails_closed()

    # Boundary layer does not create or activate Army.
    assert not boundary.creates_army_brain()
    assert not boundary.activates_army_brain()
    assert not boundary.executes_actions()

    print("SAHIBEX CHILD INTERNAL ARMY BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
