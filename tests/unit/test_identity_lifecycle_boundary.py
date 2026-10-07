from __future__ import annotations

from core.brain.root_identity import SahibexRootIdentity
from core.brain.root_instance import SahibexRootInstanceIdentity
from core.brain.specialist_brain import BrainCapability, BrainStatus, SpecialistBrain
from core.brain.child_lifecycle_boundary import (
    ChildLifecycleBoundary,
    ChildLifecycleState,
    LifecycleActor,
    LifecycleOperation,
    LifecycleDecision,
)
from security.audit.brain_trust_lifecycle import (
    BrainTrustEvidenceLifecycle,
)


def test_root_identity_is_not_lifecycle_identity() -> None:
    identity = SahibexRootIdentity()

    assert identity.validate() is True
    assert identity.grants_authority() is False

    public_methods = set(dir(identity))

    forbidden = {
        "transition_to",
        "activate",
        "pause",
        "resume",
        "retire",
        "execute",
    }

    assert not (forbidden & public_methods)


def test_root_instance_is_not_lifecycle_controller() -> None:
    instance = SahibexRootInstanceIdentity()

    assert instance.validate() is True
    assert instance.is_mother_instance() is True
    assert instance.is_execution_identity() is False
    assert instance.grants_authority() is False

    public_methods = set(dir(instance))

    forbidden = {
        "transition_to",
        "activate",
        "pause",
        "resume",
        "retire",
        "execute",
        "grant_permission",
        "modify_constitution",
    }

    assert not (forbidden & public_methods)


def test_specialist_lifecycle_is_separate_from_root_identity() -> None:
    brain = SpecialistBrain(
        name="Lifecycle Boundary Brain",
        description="Boundary test specialist brain.",
        specialization="testing",
        capabilities={BrainCapability.THINK},
    )

    original_root = SahibexRootIdentity()
    original_instance = SahibexRootInstanceIdentity()

    assert brain.status == BrainStatus.REGISTERED

    brain.transition_to(BrainStatus.READY)
    brain.transition_to(BrainStatus.ACTIVE)

    assert brain.status == BrainStatus.ACTIVE
    assert original_root.validate() is True
    assert original_instance.validate() is True


def test_trust_lifecycle_is_not_child_lifecycle() -> None:
    assert BrainTrustEvidenceLifecycle.ACTIVE.value == "active"
    assert BrainTrustEvidenceLifecycle.INVALIDATED.value == "invalidated"

    assert ChildLifecycleState.ACTIVE.value == "active"
    assert ChildLifecycleState.RETIRED.value == "retired"

    assert BrainTrustEvidenceLifecycle.ACTIVE.value != (
        ChildLifecycleState.ACTIVE.value
    ) or (
        BrainTrustEvidenceLifecycle.ACTIVE is not ChildLifecycleState.ACTIVE
    )


def test_child_lifecycle_requires_mother_authority_for_activation() -> None:
    result = ChildLifecycleBoundary.decide(
        actor=LifecycleActor.CHILD_BRAIN,
        operation=LifecycleOperation.ACTIVATE,
        from_state=ChildLifecycleState.READY,
        to_state=ChildLifecycleState.ACTIVE,
        mother_approved=False,
    )

    assert result.allowed is False
    assert result.decision == LifecycleDecision.REQUIRE_MOTHER_AUTHORITY
    assert result.authority_granted is False


def test_child_lifecycle_does_not_grant_execution_permission() -> None:
    result = ChildLifecycleBoundary.decide(
        actor=LifecycleActor.SAHIBEX_MOTHER,
        operation=LifecycleOperation.ACTIVATE,
        from_state=ChildLifecycleState.READY,
        to_state=ChildLifecycleState.ACTIVE,
        mother_approved=True,
    )

    assert result.allowed is True
    assert result.authority_granted is True
    assert ChildLifecycleBoundary.lifecycle_grants_execution_permission() is False


def test_external_actor_cannot_control_child_lifecycle() -> None:
    external_actors = (
        LifecycleActor.SOFTWARE,
        LifecycleActor.TOOL,
        LifecycleActor.EXTERNAL_MODEL,
    )

    for actor in external_actors:
        result = ChildLifecycleBoundary.decide(
            actor=actor,
            operation=LifecycleOperation.ACTIVATE,
            from_state=ChildLifecycleState.READY,
            to_state=ChildLifecycleState.ACTIVE,
            mother_approved=True,
        )

        assert result.allowed is False
        assert result.decision == LifecycleDecision.DENY
        assert result.authority_granted is False


def test_child_workers_cannot_control_child_lifecycle() -> None:
    for actor in (
        LifecycleActor.CHILD_ARMY,
        LifecycleActor.CHILD_LABOR,
    ):
        result = ChildLifecycleBoundary.decide(
            actor=actor,
            operation=LifecycleOperation.ACTIVATE,
            from_state=ChildLifecycleState.READY,
            to_state=ChildLifecycleState.ACTIVE,
            mother_approved=True,
        )

        assert result.allowed is False
        assert result.authority_granted is False

    assert ChildLifecycleBoundary.army_can_control_lifecycle() is False
    assert ChildLifecycleBoundary.labor_can_control_lifecycle() is False


def test_retired_child_cannot_be_reactivated() -> None:
    result = ChildLifecycleBoundary.decide(
        actor=LifecycleActor.HUMAN,
        operation=LifecycleOperation.REACTIVATE,
        from_state=ChildLifecycleState.RETIRED,
        to_state=ChildLifecycleState.READY,
        human_approved=True,
    )

    assert result.allowed is False
    assert result.decision == LifecycleDecision.DENY
    assert result.authority_granted is False
    assert ChildLifecycleBoundary.retired_state_is_terminal() is True


def test_invalid_child_lifecycle_fails_closed() -> None:
    result = ChildLifecycleBoundary.decide(
        actor=LifecycleActor.SAHIBEX_MOTHER,
        operation=LifecycleOperation.ACTIVATE,
        from_state=ChildLifecycleState.PROPOSED,
        to_state=ChildLifecycleState.ACTIVE,
        mother_approved=True,
    )

    assert result.allowed is False
    assert result.decision == LifecycleDecision.DENY
    assert result.authority_granted is False
    assert ChildLifecycleBoundary.invalid_state_fails_closed() is True


def test_lifecycle_does_not_modify_constitution() -> None:
    public_methods = set(dir(ChildLifecycleBoundary))

    forbidden = {
        "modify_constitution",
        "update_constitution",
        "change_constitution",
        "override_constitution",
        "grant_permission",
    }

    assert not (forbidden & public_methods)


def test_lifecycle_does_not_create_real_child() -> None:
    assert ChildLifecycleBoundary.creates_real_child() is False


def run_all_tests() -> None:
    test_root_identity_is_not_lifecycle_identity()
    test_root_instance_is_not_lifecycle_controller()
    test_specialist_lifecycle_is_separate_from_root_identity()
    test_trust_lifecycle_is_not_child_lifecycle()
    test_child_lifecycle_requires_mother_authority_for_activation()
    test_child_lifecycle_does_not_grant_execution_permission()
    test_external_actor_cannot_control_child_lifecycle()
    test_child_workers_cannot_control_child_lifecycle()
    test_retired_child_cannot_be_reactivated()
    test_invalid_child_lifecycle_fails_closed()
    test_lifecycle_does_not_modify_constitution()
    test_lifecycle_does_not_create_real_child()


if __name__ == "__main__":
    run_all_tests()
    print(
        "SAHIBEX PHASE 0 #11 IDENTITY-LIFECYCLE "
        "BOUNDARY TEST: PASS"
    )
