from core.brain.brain_registry import BrainRegistry
from core.brain.specialist_brain import (
    BrainCapability,
    BrainStatus,
    SpecialistBrain,
)
from core.brain.specialist_child_manager import SpecialistChildBrainManager
from core.policies.constitution import BrainRole


def mother(registry: BrainRegistry) -> SpecialistBrain:
    m = SpecialistBrain(
        name="SAHIBEX Mother",
        description="root authority",
        specialization="mother",
        capabilities={
            BrainCapability.THINK,
            BrainCapability.PLAN,
            BrainCapability.VERIFY,
        },
        brain_role=BrainRole.MOTHER_BRAIN,
    )
    registry.register(m)
    m.transition_to(BrainStatus.READY)
    return m


def main() -> None:
    registry = BrainRegistry()
    root = mother(registry)
    manager = SpecialistChildBrainManager(registry=registry)

    # 1. Creation requires both Mother + human approval.
    try:
        manager.create_child(
            name="Research Child",
            description="specialist research brain",
            specialization="research",
        )
    except PermissionError:
        pass
    else:
        raise AssertionError("unauthorized child creation was allowed")

    child = manager.create_child(
        name="Research Child",
        description="specialist research brain",
        specialization="research",
        mother_approved=True,
        human_approved=True,
    )
    assert child.brain.brain_role == BrainRole.CHILD_BRAIN
    assert child.brain.parent_brain_id == root.brain_id
    assert child.runtime_state.value == "ready"
    assert child.brain.trust_status.value == "unverified"
    manager.verify_trust(
        child.brain.brain_id,
        evidence="independent phase-9 boundary test passed",
        mother_approved=True,
        human_approved=True,
        verification_passed=True,
    )
    assert child.brain.trust_status.value == "verified"
    assert child.memory.memory_is_child_isolated()
    assert child.memory.can_access_mother_private_memory() is False

    # 2. Specialist role/capabilities are assigned.
    assert child.brain.has_capability(BrainCapability.RESEARCH)
    assert child.brain.has_capability(BrainCapability.VERIFY)

    # 3. Child cognition is independent; protected actions stay with Mother.
    assert child.core.can_think_independently()
    assert child.core.can_research_independently()
    assert child.core.can_self_authorize() is False
    assert manager.can_child_grant_authority() is False
    assert manager.can_child_modify_constitution() is False
    assert manager.can_child_override_mother() is False
    assert manager.protected_actions_stay_with_mother() is True

    # 4. Parent-child dispatch and performance tracking.
    manager.register_handler(
        child.brain.brain_id,
        lambda request, metadata: {
            "ok": True,
            "request": request,
            "brain_id": metadata["brain_id"],
        },
    )
    result = manager.dispatch(
        child.brain.brain_id,
        "research AI security",
    )
    assert result.success is True
    assert manager.performance(child.brain.brain_id).completed == 1
    assert manager.performance(child.brain.brain_id).verified == 0

    # A successful handler run is not itself independent verification.
    manager.record_performance(
        child.brain.brain_id,
        success=True,
        verified=True,
    )
    assert manager.performance(child.brain.brain_id).verified == 1

    # 5. Activation is a real lifecycle state and active children can work.
    manager.activate(child.brain.brain_id, mother_approved=True, human_approved=True)
    assert child.runtime_state.value == "active"
    assert child.brain.status == BrainStatus.ACTIVE
    result = manager.dispatch(
        child.brain.brain_id,
        "continue research",
    )
    assert result.success is True
    assert child.runtime_state.value == "active"

    # 6. Suspension blocks work and requires Mother approval.
    manager.suspend(
        child.brain.brain_id,
        mother_approved=True,
        reason="temporary safety suspension",
    )
    assert child.runtime_state.value == "paused"
    assert child.brain.status == BrainStatus.PAUSED
    assert child.brain.trust_status.value == "suspended"
    blocked = manager.dispatch(child.brain.brain_id, "blocked")
    assert blocked.success is False

    # 7. Resume requires fresh verification.
    try:
        manager.resume(
            child.brain.brain_id,
            mother_approved=True,
            human_approved=True,
        )
    except PermissionError:
        pass
    else:
        raise AssertionError("resume without verification was allowed")

    manager.resume(
        child.brain.brain_id,
        mother_approved=True,
        human_approved=True,
        verification_passed=True,
        verification_evidence="fresh post-pause verification passed in unit test",
    )
    assert child.runtime_state.value == "ready"
    assert child.brain.status == BrainStatus.READY
    assert child.brain.trust_status.value == "verified"

    # 8. Replacement preserves lineage but creates a new identity.
    replacement = manager.replace(
        child.brain.brain_id,
        name="Research Child v2",
        description="replacement research brain",
        specialization="research",
        mother_approved=True,
        human_approved=True,
    )
    assert replacement.brain.brain_id != child.brain.brain_id
    assert child.runtime_state.value == "retired"
    assert replacement.runtime_state.value == "ready"
    assert replacement.predecessor_brain_id == child.brain.brain_id
    assert replacement.trust_lineage_id == child.trust_lineage_id
    assert registry.get(child.brain.brain_id) is child.brain

    # 9. Retirement is terminal and requires human authority.
    try:
        manager.retire(replacement.brain.brain_id)
    except PermissionError:
        pass
    else:
        raise AssertionError("retirement without human approval was allowed")

    manager.retire(
        replacement.brain.brain_id,
        human_approved=True,
    )
    assert replacement.runtime_state.value == "retired"
    try:
        manager.activate(
            replacement.brain.brain_id,
            mother_approved=True,
            human_approved=True,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("retired child was reactivated")

    # 10. Specialist templates cover the requested specialist families.
    profiles = manager.specialist_profiles()
    for name in (
        "research",
        "coding",
        "trading",
        "business",
        "computer-control",
    ):
        assert name in profiles
        assert profiles[name]

    print("SAHIBEX PHASE 9 SPECIALIST CHILD BRAIN: PASS")


def test_dispatch_enforces_required_specialist_capability():
    manager = SpecialistChildBrainManager()
    child = manager.create_child(
        name="Restricted Coding Child",
        description="coding role with intentionally restricted capabilities",
        specialization="coding",
        capabilities={BrainCapability.THINK, BrainCapability.READ},
        mother_approved=True,
        human_approved=True,
    )
    called = {"value": False}

    def handler(request, metadata):
        called["value"] = True
        return "should not execute"

    manager.register_handler(child.brain.brain_id, handler)
    result = manager.dispatch(child.brain.brain_id, "write a program")

    assert result.success is False
    assert "required capability" in result.error
    assert called["value"] is False
    assert manager.performance(child.brain.brain_id).failed == 0


def test_failed_replacement_keeps_predecessor_ready():
    manager = SpecialistChildBrainManager()
    child = manager.create_child(
        name="Original Child",
        description="working predecessor",
        specialization="research",
        mother_approved=True,
        human_approved=True,
    )

    try:
        manager.replace(
            child.brain.brain_id,
            name="",
            description="invalid replacement",
            specialization="research",
            mother_approved=True,
            human_approved=True,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("invalid replacement unexpectedly succeeded")

    assert child.runtime_state.value == "ready"
    assert child.brain.status == BrainStatus.READY
    assert manager.get(child.brain.brain_id) is child
    assert len(manager.list_children()) == 1


def test_activation_requires_explicit_human_approval():
    manager = SpecialistChildBrainManager()
    child = manager.create_child(
        name="Activation Gate Child",
        description="tests explicit human approval for activation",
        specialization="research",
        mother_approved=True,
        human_approved=True,
    )
    try:
        manager.activate(child.brain.brain_id, mother_approved=True)
    except PermissionError:
        pass
    else:
        raise AssertionError("activation without human approval was allowed")


def test_human_can_pause_child_when_verification_is_failing():
    manager = SpecialistChildBrainManager()
    child = manager.create_child(
        name="Emergency Pause Child",
        description="tests fail-safe pause",
        specialization="research",
        mother_approved=True,
        human_approved=True,
    )
    paused = manager.suspend(
        child.brain.brain_id,
        human_approved=True,
        reason="emergency stop during verification failure",
    )
    assert paused.runtime_state.value == "paused"
    assert paused.brain.status == BrainStatus.READY


def test_ready_child_can_suspend_and_resume_without_becoming_terminal():
    manager = SpecialistChildBrainManager()
    child = manager.create_child(
        name="Ready Child",
        description="tests safe pause/resume from READY",
        specialization="research",
        mother_approved=True,
        human_approved=True,
    )

    manager.suspend(
        child.brain.brain_id,
        mother_approved=True,
        reason="pause before first activation",
    )
    assert child.runtime_state.value == "paused"
    assert child.brain.status == BrainStatus.READY
    assert child.brain.trust_status.value == "suspended"

    manager.resume(
        child.brain.brain_id,
        mother_approved=True,
        human_approved=True,
        verification_passed=True,
        verification_evidence="fresh post-pause verification passed in unit test",
    )
    assert child.runtime_state.value == "ready"
    assert child.brain.status == BrainStatus.READY
    assert child.brain.trust_status.value == "verified"


def test_phase9_specialist_child_brain():
    main()


if __name__ == "__main__":
    main()
