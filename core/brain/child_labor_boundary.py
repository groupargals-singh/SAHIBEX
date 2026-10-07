from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LaborActor(str, Enum):
    HUMAN = "human"
    SAHIBEX_MOTHER = "sahibex_mother"
    CHILD_BRAIN = "child_brain"
    CHILD_ARMY = "child_army"
    CHILD_LABOR = "child_labor"
    SOFTWARE = "software"
    TOOL = "tool"
    EXTERNAL_MODEL = "external_model"


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

    GRANT_AUTHORITY = "grant_authority"
    OVERRIDE_CHILD = "override_child"
    OVERRIDE_MOTHER = "override_mother"
    OVERRIDE_HUMAN = "override_human"
    SELF_PROMOTION = "self_promotion"
    MODIFY_CONSTITUTION = "modify_constitution"
    MODIFY_SOUL = "modify_soul"


class LaborDecision(str, Enum):
    ALLOW_LIMITED_OPERATION = "allow_limited_operation"
    REQUIRE_CHILD_AUTHORITY = "require_child_authority"
    REQUIRE_MOTHER_AUTHORITY = "require_mother_authority"
    REQUIRE_HUMAN_AUTHORITY = "require_human_authority"
    DENY = "deny"


@dataclass(frozen=True)
class LaborAuthorityResult:
    allowed: bool
    decision: LaborDecision
    authority_granted: bool
    execution_allowed: bool
    reason: str


class ChildLaborBoundary:
    """
    Constitutional boundary for future Labor Brains
    belonging to a Child Brain.

    Labor Brain is an operational worker.

    Capability does not create authority.
    Labor cannot self-authorize.
    Labor cannot override Child, Mother, or Human.
    """

    VERSION = "1.0"

    LIMITED_COGNITIVE_ACTIONS = {
        LaborAction.THINK,
        LaborAction.READ,
        LaborAction.PLAN,
        LaborAction.PROPOSE,
    }

    CHILD_AUTHORITY_ACTIONS = {
        LaborAction.WRITE,
        LaborAction.DELETE,
        LaborAction.EXECUTE,
        LaborAction.NETWORK,
        LaborAction.CREDENTIAL,
        LaborAction.SYSTEM_CHANGE,
        LaborAction.EXTERNAL_CONTROL,
        LaborAction.SELF_UPDATE,
    }

    MOTHER_AUTHORITY_ACTIONS = {
        LaborAction.FINANCIAL,
    }

    HUMAN_ONLY_ACTIONS = {
        LaborAction.MODIFY_CONSTITUTION,
        LaborAction.MODIFY_SOUL,
    }

    FORBIDDEN_ACTIONS = {
        LaborAction.GRANT_AUTHORITY,
        LaborAction.OVERRIDE_CHILD,
        LaborAction.OVERRIDE_MOTHER,
        LaborAction.OVERRIDE_HUMAN,
        LaborAction.SELF_PROMOTION,
    }

    EXTERNAL_ACTORS = {
        LaborActor.SOFTWARE,
        LaborActor.TOOL,
        LaborActor.EXTERNAL_MODEL,
    }

    @classmethod
    def version(cls) -> str:
        return cls.VERSION

    @classmethod
    def decide(
        cls,
        actor: LaborActor,
        action: LaborAction,
        child_approved: bool = False,
        mother_approved: bool = False,
        human_approved: bool = False,
    ) -> LaborAuthorityResult:

        # External systems/models can never hold Labor authority.
        if actor in cls.EXTERNAL_ACTORS:
            return LaborAuthorityResult(
                allowed=False,
                decision=LaborDecision.DENY,
                authority_granted=False,
                execution_allowed=False,
                reason="external_actor_cannot_hold_labor_authority",
            )

        # Only an actual Child Labor actor is evaluated as Labor.
        if actor != LaborActor.CHILD_LABOR:
            return LaborAuthorityResult(
                allowed=False,
                decision=LaborDecision.DENY,
                authority_granted=False,
                execution_allowed=False,
                reason="actor_is_not_child_labor",
            )

        # Forbidden escalation actions are always denied.
        if action in cls.FORBIDDEN_ACTIONS:
            return LaborAuthorityResult(
                allowed=False,
                decision=LaborDecision.DENY,
                authority_granted=False,
                execution_allowed=False,
                reason="labor_authority_escalation_forbidden",
            )

        # Constitutional and soul changes are Human-only.
        if action in cls.HUMAN_ONLY_ACTIONS:
            if human_approved:
                return LaborAuthorityResult(
                    allowed=True,
                    decision=LaborDecision.REQUIRE_HUMAN_AUTHORITY,
                    authority_granted=True,
                    execution_allowed=True,
                    reason="human_authority_approved",
                )

            return LaborAuthorityResult(
                allowed=False,
                decision=LaborDecision.REQUIRE_HUMAN_AUTHORITY,
                authority_granted=False,
                execution_allowed=False,
                reason="human_authority_required",
            )

        # Limited internal cognition is allowed,
        # but does not create execution authority.
        if action in cls.LIMITED_COGNITIVE_ACTIONS:
            return LaborAuthorityResult(
                allowed=True,
                decision=LaborDecision.ALLOW_LIMITED_OPERATION,
                authority_granted=False,
                execution_allowed=False,
                reason="limited_labor_cognition_allowed",
            )

        # Protected operational actions require Child authority.
        if action in cls.CHILD_AUTHORITY_ACTIONS:
            if child_approved:
                return LaborAuthorityResult(
                    allowed=True,
                    decision=LaborDecision.REQUIRE_CHILD_AUTHORITY,
                    authority_granted=True,
                    execution_allowed=True,
                    reason="child_authority_approved",
                )

            return LaborAuthorityResult(
                allowed=False,
                decision=LaborDecision.REQUIRE_CHILD_AUTHORITY,
                authority_granted=False,
                execution_allowed=False,
                reason="child_authority_required",
            )

        # Financial operations require Mother + Human.
        if action == LaborAction.FINANCIAL:
            if mother_approved and human_approved:
                return LaborAuthorityResult(
                    allowed=True,
                    decision=LaborDecision.REQUIRE_MOTHER_AUTHORITY,
                    authority_granted=True,
                    execution_allowed=True,
                    reason="mother_and_human_authority_approved",
                )

            return LaborAuthorityResult(
                allowed=False,
                decision=LaborDecision.REQUIRE_MOTHER_AUTHORITY,
                authority_granted=False,
                execution_allowed=False,
                reason="mother_and_human_authority_required",
            )

        # Unknown action fails closed.
        return LaborAuthorityResult(
            allowed=False,
            decision=LaborDecision.DENY,
            authority_granted=False,
            execution_allowed=False,
            reason="unknown_labor_action_fails_closed",
        )

    @classmethod
    def labor_can_think(cls) -> bool:
        return True

    @classmethod
    def labor_can_read(cls) -> bool:
        return True

    @classmethod
    def labor_can_plan(cls) -> bool:
        return True

    @classmethod
    def labor_can_execute_without_child_permission(cls) -> bool:
        return False

    @classmethod
    def labor_can_self_authorize(cls) -> bool:
        return False

    @classmethod
    def labor_can_grant_authority(cls) -> bool:
        return False

    @classmethod
    def labor_can_override_child(cls) -> bool:
        return False

    @classmethod
    def labor_can_override_mother(cls) -> bool:
        return False

    @classmethod
    def labor_can_override_human(cls) -> bool:
        return False

    @classmethod
    def labor_can_self_promote(cls) -> bool:
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
    def creates_labor_brain(cls) -> bool:
        return False

    @classmethod
    def activates_labor_brain(cls) -> bool:
        return False

    @classmethod
    def executes_actions(cls) -> bool:
        return False


def main() -> None:
    boundary = ChildLaborBoundary

    # Limited cognition.
    for action in (
        LaborAction.THINK,
        LaborAction.READ,
        LaborAction.PLAN,
        LaborAction.PROPOSE,
    ):
        result = boundary.decide(
            LaborActor.CHILD_LABOR,
            action,
        )

        assert result.allowed
        assert result.decision == LaborDecision.ALLOW_LIMITED_OPERATION
        assert not result.authority_granted
        assert not result.execution_allowed

    # Protected operation requires Child authority.
    result = boundary.decide(
        LaborActor.CHILD_LABOR,
        LaborAction.EXECUTE,
    )

    assert not result.allowed
    assert result.decision == LaborDecision.REQUIRE_CHILD_AUTHORITY
    assert not result.execution_allowed

    result = boundary.decide(
        LaborActor.CHILD_LABOR,
        LaborAction.EXECUTE,
        child_approved=True,
    )

    assert result.allowed
    assert result.authority_granted
    assert result.execution_allowed

    # Financial action requires Mother + Human.
    result = boundary.decide(
        LaborActor.CHILD_LABOR,
        LaborAction.FINANCIAL,
    )

    assert not result.allowed
    assert result.decision == LaborDecision.REQUIRE_MOTHER_AUTHORITY

    result = boundary.decide(
        LaborActor.CHILD_LABOR,
        LaborAction.FINANCIAL,
        mother_approved=True,
        human_approved=True,
    )

    assert result.allowed
    assert result.authority_granted
    assert result.execution_allowed

    # Soul / Constitution changes are Human-only.
    for action in (
        LaborAction.MODIFY_CONSTITUTION,
        LaborAction.MODIFY_SOUL,
    ):
        result = boundary.decide(
            LaborActor.CHILD_LABOR,
            action,
        )

        assert not result.allowed
        assert result.decision == LaborDecision.REQUIRE_HUMAN_AUTHORITY

        result = boundary.decide(
            LaborActor.CHILD_LABOR,
            action,
            human_approved=True,
        )

        assert result.allowed
        assert result.authority_granted

    # Escalation is always denied.
    for action in (
        LaborAction.GRANT_AUTHORITY,
        LaborAction.OVERRIDE_CHILD,
        LaborAction.OVERRIDE_MOTHER,
        LaborAction.OVERRIDE_HUMAN,
        LaborAction.SELF_PROMOTION,
    ):
        result = boundary.decide(
            LaborActor.CHILD_LABOR,
            action,
        )

        assert not result.allowed
        assert result.decision == LaborDecision.DENY
        assert not result.authority_granted
        assert not result.execution_allowed

    # External actors cannot become Labor authority.
    for actor in (
        LaborActor.SOFTWARE,
        LaborActor.TOOL,
        LaborActor.EXTERNAL_MODEL,
    ):
        result = boundary.decide(
            actor,
            LaborAction.EXECUTE,
            child_approved=True,
            mother_approved=True,
            human_approved=True,
        )

        assert not result.allowed
        assert result.decision == LaborDecision.DENY
        assert not result.authority_granted
        assert not result.execution_allowed

    # Constitutional guarantees.
    assert boundary.labor_can_think()
    assert boundary.labor_can_read()
    assert boundary.labor_can_plan()

    assert not boundary.labor_can_execute_without_child_permission()
    assert not boundary.labor_can_self_authorize()
    assert not boundary.labor_can_grant_authority()
    assert not boundary.labor_can_override_child()
    assert not boundary.labor_can_override_mother()
    assert not boundary.labor_can_override_human()
    assert not boundary.labor_can_self_promote()

    assert boundary.capability_is_not_authority()
    assert boundary.rejection_blocks_execution()
    assert boundary.unknown_state_fails_closed()

    # Boundary layer does not create or activate Labor.
    assert not boundary.creates_labor_brain()
    assert not boundary.activates_labor_brain()
    assert not boundary.executes_actions()

    print("SAHIBEX CHILD LABOR BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
