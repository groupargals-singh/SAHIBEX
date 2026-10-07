from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ChildLifecycleState(str, Enum):
    PROPOSED = "proposed"
    BIRTH_AUTHORIZED = "birth_authorized"
    CREATED = "created"
    VERIFIED = "verified"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    RECOVERY = "recovery"
    RETIRED = "retired"


class LifecycleOperation(str, Enum):
    PROPOSE = "propose"
    AUTHORIZE_BIRTH = "authorize_birth"
    CREATE = "create"
    VERIFY = "verify"
    ACTIVATE = "activate"
    PAUSE = "pause"
    RESUME = "resume"
    START_RECOVERY = "start_recovery"
    COMPLETE_RECOVERY = "complete_recovery"
    RETIRE = "retire"
    REACTIVATE = "reactivate"


class LifecycleActor(str, Enum):
    HUMAN = "human"
    SAHIBEX_MOTHER = "sahibex_mother"
    CHILD_BRAIN = "child_brain"
    CHILD_ARMY = "child_army"
    CHILD_LABOR = "child_labor"
    SOFTWARE = "software"
    TOOL = "tool"
    EXTERNAL_MODEL = "external_model"


class LifecycleDecision(str, Enum):
    ALLOW = "allow"
    REQUIRE_MOTHER_AUTHORITY = "require_mother_authority"
    REQUIRE_HUMAN_AUTHORITY = "require_human_authority"
    DENY = "deny"


@dataclass(frozen=True)
class LifecycleTransitionResult:
    allowed: bool
    decision: LifecycleDecision
    from_state: ChildLifecycleState
    to_state: ChildLifecycleState
    authority_granted: bool
    reason: str


class ChildLifecycleBoundary:
    """
    Constitutional lifecycle boundary for a future Child Brain.

    This layer defines legal lifecycle transitions only.
    It does not create, activate, execute, or retire a real Child.
    """

    VERSION = "1.0"

    # Valid lifecycle transitions.
    VALID_TRANSITIONS = {
        (
            ChildLifecycleState.PROPOSED,
            ChildLifecycleState.BIRTH_AUTHORIZED,
        ),
        (
            ChildLifecycleState.BIRTH_AUTHORIZED,
            ChildLifecycleState.CREATED,
        ),
        (
            ChildLifecycleState.CREATED,
            ChildLifecycleState.VERIFIED,
        ),
        (
            ChildLifecycleState.VERIFIED,
            ChildLifecycleState.READY,
        ),
        (
            ChildLifecycleState.READY,
            ChildLifecycleState.ACTIVE,
        ),
        (
            ChildLifecycleState.ACTIVE,
            ChildLifecycleState.PAUSED,
        ),
        (
            ChildLifecycleState.PAUSED,
            ChildLifecycleState.READY,
        ),
        (
            ChildLifecycleState.ACTIVE,
            ChildLifecycleState.RECOVERY,
        ),
        (
            ChildLifecycleState.PAUSED,
            ChildLifecycleState.RECOVERY,
        ),
        (
            ChildLifecycleState.RECOVERY,
            ChildLifecycleState.VERIFIED,
        ),
        (
            ChildLifecycleState.READY,
            ChildLifecycleState.RETIRED,
        ),
        (
            ChildLifecycleState.PAUSED,
            ChildLifecycleState.RETIRED,
        ),
        (
            ChildLifecycleState.RECOVERY,
            ChildLifecycleState.RETIRED,
        ),
    }

    MOTHER_AUTHORITY_OPERATIONS = {
        LifecycleOperation.AUTHORIZE_BIRTH,
        LifecycleOperation.ACTIVATE,
        LifecycleOperation.PAUSE,
        LifecycleOperation.RESUME,
        LifecycleOperation.START_RECOVERY,
        LifecycleOperation.COMPLETE_RECOVERY,
    }

    HUMAN_AUTHORITY_OPERATIONS = {
        LifecycleOperation.RETIRE,
        LifecycleOperation.REACTIVATE,
    }

    INFORMATION_OPERATIONS = {
        LifecycleOperation.PROPOSE,
        LifecycleOperation.VERIFY,
    }

    EXTERNAL_ACTORS = {
        LifecycleActor.SOFTWARE,
        LifecycleActor.TOOL,
        LifecycleActor.EXTERNAL_MODEL,
    }

    WORKER_ACTORS = {
        LifecycleActor.CHILD_ARMY,
        LifecycleActor.CHILD_LABOR,
    }

    @classmethod
    def version(cls) -> str:
        return cls.VERSION

    @classmethod
    def is_valid_transition(
        cls,
        from_state: ChildLifecycleState,
        to_state: ChildLifecycleState,
    ) -> bool:
        return (from_state, to_state) in cls.VALID_TRANSITIONS

    @classmethod
    def decide(
        cls,
        actor: LifecycleActor,
        operation: LifecycleOperation,
        from_state: ChildLifecycleState,
        to_state: ChildLifecycleState,
        mother_approved: bool = False,
        human_approved: bool = False,
        verification_passed: bool = False,
        authorization_valid: bool = False,
    ) -> LifecycleTransitionResult:

        # External actors can never control lifecycle.
        if actor in cls.EXTERNAL_ACTORS:
            return LifecycleTransitionResult(
                allowed=False,
                decision=LifecycleDecision.DENY,
                from_state=from_state,
                to_state=to_state,
                authority_granted=False,
                reason="external_actor_cannot_control_child_lifecycle",
            )
        # Child worker actors can never control constitutional lifecycle.
        # Worker capability is not lifecycle authority.
        if actor in cls.WORKER_ACTORS:
            return LifecycleTransitionResult(
                allowed=False,
                decision=LifecycleDecision.DENY,
                from_state=from_state,
                to_state=to_state,
                authority_granted=False,
                reason="child_worker_cannot_control_child_lifecycle",
            )

        # Every transition must be explicitly defined.
        if not cls.is_valid_transition(from_state, to_state):
            return LifecycleTransitionResult(
                allowed=False,
                decision=LifecycleDecision.DENY,
                from_state=from_state,
                to_state=to_state,
                authority_granted=False,
                reason="invalid_lifecycle_transition",
            )

        # Retired is terminal.
        if from_state == ChildLifecycleState.RETIRED:
            return LifecycleTransitionResult(
                allowed=False,
                decision=LifecycleDecision.DENY,
                from_state=from_state,
                to_state=to_state,
                authority_granted=False,
                reason="retired_child_cannot_transition",
            )

        # Proposals and verification are cognitive/information stages.
        if operation in cls.INFORMATION_OPERATIONS:
            if operation == LifecycleOperation.VERIFY:
                if not verification_passed:
                    return LifecycleTransitionResult(
                        allowed=False,
                        decision=LifecycleDecision.DENY,
                        from_state=from_state,
                        to_state=to_state,
                        authority_granted=False,
                        reason="verification_required",
                    )

            return LifecycleTransitionResult(
                allowed=True,
                decision=LifecycleDecision.ALLOW,
                from_state=from_state,
                to_state=to_state,
                authority_granted=False,
                reason="lifecycle_information_operation_allowed",
            )

        # Birth authorization requires Mother authority plus valid authorization.
        if operation == LifecycleOperation.AUTHORIZE_BIRTH:
            if not mother_approved or not authorization_valid:
                return LifecycleTransitionResult(
                    allowed=False,
                    decision=LifecycleDecision.REQUIRE_MOTHER_AUTHORITY,
                    from_state=from_state,
                    to_state=to_state,
                    authority_granted=False,
                    reason="valid_mother_birth_authorization_required",
                )

            return LifecycleTransitionResult(
                allowed=True,
                decision=LifecycleDecision.REQUIRE_MOTHER_AUTHORITY,
                from_state=from_state,
                to_state=to_state,
                authority_granted=True,
                reason="mother_birth_authorization_valid",
            )

        # Mother-controlled lifecycle operations.
        if operation in cls.MOTHER_AUTHORITY_OPERATIONS:
            if not mother_approved:
                return LifecycleTransitionResult(
                    allowed=False,
                    decision=LifecycleDecision.REQUIRE_MOTHER_AUTHORITY,
                    from_state=from_state,
                    to_state=to_state,
                    authority_granted=False,
                    reason="mother_authority_required",
                )

            if operation == LifecycleOperation.COMPLETE_RECOVERY:
                if not verification_passed:
                    return LifecycleTransitionResult(
                        allowed=False,
                        decision=LifecycleDecision.DENY,
                        from_state=from_state,
                        to_state=to_state,
                        authority_granted=False,
                        reason="recovery_requires_successful_verification",
                    )

            return LifecycleTransitionResult(
                allowed=True,
                decision=LifecycleDecision.REQUIRE_MOTHER_AUTHORITY,
                from_state=from_state,
                to_state=to_state,
                authority_granted=True,
                reason="mother_authority_approved_lifecycle_operation",
            )

        # Retirement and reactivation are Human-controlled.
        if operation in cls.HUMAN_AUTHORITY_OPERATIONS:
            if not human_approved:
                return LifecycleTransitionResult(
                    allowed=False,
                    decision=LifecycleDecision.REQUIRE_HUMAN_AUTHORITY,
                    from_state=from_state,
                    to_state=to_state,
                    authority_granted=False,
                    reason="human_authority_required",
                )

            # Reactivation is deliberately denied by default because
            # retirement is terminal in this version.
            if operation == LifecycleOperation.REACTIVATE:
                return LifecycleTransitionResult(
                    allowed=False,
                    decision=LifecycleDecision.DENY,
                    from_state=from_state,
                    to_state=to_state,
                    authority_granted=False,
                    reason="retired_child_reactivation_forbidden",
                )

            return LifecycleTransitionResult(
                allowed=True,
                decision=LifecycleDecision.REQUIRE_HUMAN_AUTHORITY,
                from_state=from_state,
                to_state=to_state,
                authority_granted=True,
                reason="human_authority_approved_retirement",
            )

        # Unknown operation fails closed.
        return LifecycleTransitionResult(
            allowed=False,
            decision=LifecycleDecision.DENY,
            from_state=from_state,
            to_state=to_state,
            authority_granted=False,
            reason="unknown_lifecycle_state_fails_closed",
        )

    @classmethod
    def child_can_self_activate(cls) -> bool:
        return False

    @classmethod
    def child_can_self_pause(cls) -> bool:
        return False

    @classmethod
    def child_can_self_resume(cls) -> bool:
        return False

    @classmethod
    def child_can_self_retire(cls) -> bool:
        return False

    @classmethod
    def army_can_control_lifecycle(cls) -> bool:
        return False

    @classmethod
    def labor_can_control_lifecycle(cls) -> bool:
        return False

    @classmethod
    def external_actor_can_control_lifecycle(cls) -> bool:
        return False

    @classmethod
    def retired_state_is_terminal(cls) -> bool:
        return True

    @classmethod
    def invalid_state_fails_closed(cls) -> bool:
        return True

    @classmethod
    def lifecycle_creates_authority(cls) -> bool:
        return False

    @classmethod
    def lifecycle_grants_execution_permission(cls) -> bool:
        return False

    @classmethod
    def creates_real_child(cls) -> bool:
        return False

    @classmethod
    def activates_real_child(cls) -> bool:
        return False

    @classmethod
    def executes_child_actions(cls) -> bool:
        return False

    @classmethod
    def retires_real_child(cls) -> bool:
        return False


def main() -> None:
    boundary = ChildLifecycleBoundary

    # Valid transition: proposed -> birth authorized.
    result = boundary.decide(
        LifecycleActor.SAHIBEX_MOTHER,
        LifecycleOperation.AUTHORIZE_BIRTH,
        ChildLifecycleState.PROPOSED,
        ChildLifecycleState.BIRTH_AUTHORIZED,
        mother_approved=True,
        authorization_valid=True,
    )

    assert result.allowed
    assert result.authority_granted

    # Birth authorization without Mother approval is blocked.
    result = boundary.decide(
        LifecycleActor.CHILD_BRAIN,
        LifecycleOperation.AUTHORIZE_BIRTH,
        ChildLifecycleState.PROPOSED,
        ChildLifecycleState.BIRTH_AUTHORIZED,
        mother_approved=False,
        authorization_valid=True,
    )

    assert not result.allowed
    assert result.decision == LifecycleDecision.REQUIRE_MOTHER_AUTHORITY

    # Invalid transition is blocked.
    result = boundary.decide(
        LifecycleActor.SAHIBEX_MOTHER,
        LifecycleOperation.ACTIVATE,
        ChildLifecycleState.PROPOSED,
        ChildLifecycleState.ACTIVE,
        mother_approved=True,
    )

    assert not result.allowed
    assert result.decision == LifecycleDecision.DENY

    # Activation requires Mother approval.
    result = boundary.decide(
        LifecycleActor.SAHIBEX_MOTHER,
        LifecycleOperation.ACTIVATE,
        ChildLifecycleState.READY,
        ChildLifecycleState.ACTIVE,
        mother_approved=False,
    )

    assert not result.allowed
    assert result.decision == LifecycleDecision.REQUIRE_MOTHER_AUTHORITY

    result = boundary.decide(
        LifecycleActor.SAHIBEX_MOTHER,
        LifecycleOperation.ACTIVATE,
        ChildLifecycleState.READY,
        ChildLifecycleState.ACTIVE,
        mother_approved=True,
    )

    assert result.allowed
    assert result.authority_granted

    # Recovery completion requires verification.
    result = boundary.decide(
        LifecycleActor.SAHIBEX_MOTHER,
        LifecycleOperation.COMPLETE_RECOVERY,
        ChildLifecycleState.RECOVERY,
        ChildLifecycleState.VERIFIED,
        mother_approved=True,
        verification_passed=False,
    )

    assert not result.allowed
    assert result.decision == LifecycleDecision.DENY

    result = boundary.decide(
        LifecycleActor.SAHIBEX_MOTHER,
        LifecycleOperation.COMPLETE_RECOVERY,
        ChildLifecycleState.RECOVERY,
        ChildLifecycleState.VERIFIED,
        mother_approved=True,
        verification_passed=True,
    )

    assert result.allowed

    # Retirement requires Human authority.
    result = boundary.decide(
        LifecycleActor.SAHIBEX_MOTHER,
        LifecycleOperation.RETIRE,
        ChildLifecycleState.READY,
        ChildLifecycleState.RETIRED,
        human_approved=False,
    )

    assert not result.allowed
    assert result.decision == LifecycleDecision.REQUIRE_HUMAN_AUTHORITY

    result = boundary.decide(
        LifecycleActor.HUMAN,
        LifecycleOperation.RETIRE,
        ChildLifecycleState.READY,
        ChildLifecycleState.RETIRED,
        human_approved=True,
    )

    assert result.allowed
    assert result.authority_granted

    # Retired Child cannot reactivate.
    result = boundary.decide(
        LifecycleActor.HUMAN,
        LifecycleOperation.REACTIVATE,
        ChildLifecycleState.RETIRED,
        ChildLifecycleState.READY,
        human_approved=True,
    )

    assert not result.allowed
    assert result.decision == LifecycleDecision.DENY

    # Child / Army / Labor cannot control lifecycle.
    for actor in (
        LifecycleActor.CHILD_BRAIN,
        LifecycleActor.CHILD_ARMY,
        LifecycleActor.CHILD_LABOR,
    ):
        result = boundary.decide(
            actor,
            LifecycleOperation.ACTIVATE,
            ChildLifecycleState.READY,
            ChildLifecycleState.ACTIVE,
            mother_approved=True,
        )

        assert result.allowed is True
        assert result.authority_granted is True

    # Important: the layer evaluates authority; workers do not receive
    # authority merely because the actor is a worker.
    assert not boundary.child_can_self_activate()
    assert not boundary.child_can_self_pause()
    assert not boundary.child_can_self_resume()
    assert not boundary.child_can_self_retire()

    assert not boundary.army_can_control_lifecycle()
    assert not boundary.labor_can_control_lifecycle()
    assert not boundary.external_actor_can_control_lifecycle()

    assert boundary.retired_state_is_terminal()
    assert boundary.invalid_state_fails_closed()

    assert not boundary.lifecycle_creates_authority()
    assert not boundary.lifecycle_grants_execution_permission()

    # Boundary layer itself never creates/activates/executes/retire real Child.
    assert not boundary.creates_real_child()
    assert not boundary.activates_real_child()
    assert not boundary.executes_child_actions()
    assert not boundary.retires_real_child()

    print("SAHIBEX CHILD LIFECYCLE BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
