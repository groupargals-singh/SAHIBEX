from core.brain.child_lifecycle_boundary import (
    ChildLifecycleBoundary,
    ChildLifecycleState,
    LifecycleActor,
    LifecycleDecision,
    LifecycleOperation,
)


def main() -> None:
    boundary = ChildLifecycleBoundary

    # Valid birth authorization.
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

    # Missing Mother authorization.
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

    # Invalid transition.
    result = boundary.decide(
        LifecycleActor.SAHIBEX_MOTHER,
        LifecycleOperation.ACTIVATE,
        ChildLifecycleState.PROPOSED,
        ChildLifecycleState.ACTIVE,
        mother_approved=True,
    )

    assert not result.allowed
    assert result.decision == LifecycleDecision.DENY

    # Activation gate.
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

    # Recovery requires verification.
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

    # Retirement requires Human.
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

    # Retirement is terminal.
    result = boundary.decide(
        LifecycleActor.HUMAN,
        LifecycleOperation.REACTIVATE,
        ChildLifecycleState.RETIRED,
        ChildLifecycleState.READY,
        human_approved=True,
    )

    assert not result.allowed
    assert result.decision == LifecycleDecision.DENY

    # Constitutional guarantees.
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

    assert not boundary.creates_real_child()
    assert not boundary.activates_real_child()
    assert not boundary.executes_child_actions()
    assert not boundary.retires_real_child()

    print("SAHIBEX CHILD LIFECYCLE BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
