import sqlite3

import pytest

from core.brain.child_instance_registry import ChildInstanceRegistry
from core.brain.root_identity import SahibexRootIdentity
from core.brain.specialist_brain import BrainCapability, BrainStatus, SpecialistBrain
from core.brain.verification import BrainTrustStatus
from core.policies.constitution import BrainRole


def make_child(*, brain_id: str = "child-brain-test-1") -> SpecialistBrain:
    return SpecialistBrain(
        name="Research Child",
        description="Narrow local research specialist",
        specialization="research-source-checking",
        capabilities={BrainCapability.THINK, BrainCapability.RESEARCH, BrainCapability.VERIFY},
        brain_id=brain_id,
        brain_role=BrainRole.CHILD_BRAIN,
        parent_brain_id=SahibexRootIdentity().BRAIN_ID,
    )


def test_registry_persists_child_identity_trust_and_lifecycle_across_restart(tmp_path):
    db_path = tmp_path / "children.db"
    registry = ChildInstanceRegistry(db_path)
    child = make_child()
    registry.register(
        child, mother_approved=True, human_approved=True, authorization_valid=True
    )
    registry.update_trust(
        child.brain_id,
        BrainTrustStatus.VERIFIED,
        evidence="offline regression suite passed; identity checked",
        mother_approved=True,
        human_approved=True,
        reason="trust evidence verified",
    )
    registry.transition(
        child.brain_id,
        BrainStatus.READY,
        mother_approved=True,
        verification_passed=True,
        reason="identity and configuration verified",
    )
    registry.transition(
        child.brain_id,
        BrainStatus.ACTIVE,
        mother_approved=True,
        human_approved=True,
        verification_passed=True,
        reason="explicit activation approval",
    )
    assert registry.verify_integrity() is True
    registry.close()

    restored_registry = ChildInstanceRegistry(db_path)
    restored = restored_registry.get("child-brain-test-1")
    assert restored is not None
    assert restored.name == "Research Child"
    assert restored.parent_brain_id == SahibexRootIdentity().BRAIN_ID
    assert restored.status == BrainStatus.ACTIVE
    assert restored.trust_status == BrainTrustStatus.VERIFIED
    assert restored.trust_evidence == "offline regression suite passed; identity checked"
    assert restored.has_capability(BrainCapability.RESEARCH)
    assert restored_registry.verify_integrity() is True
    assert len(restored_registry.list_events()) == 4
    restored_registry.close()


def test_registration_requires_mother_human_and_valid_authorization(tmp_path):
    registry = ChildInstanceRegistry(tmp_path / "children.db")
    with pytest.raises(PermissionError, match="mother_and_human_approval"):
        registry.register(
            make_child(), mother_approved=True, human_approved=False,
            authorization_valid=True,
        )
    assert registry.get("child-brain-test-1") is None
    registry.close()


def test_activation_requires_verified_trust_and_both_approvals(tmp_path):
    registry = ChildInstanceRegistry(tmp_path / "children.db")
    child = make_child()
    registry.register(
        child, mother_approved=True, human_approved=True, authorization_valid=True
    )
    registry.transition(
        child.brain_id, BrainStatus.READY, mother_approved=True,
        verification_passed=True, reason="verified configuration",
    )
    with pytest.raises(PermissionError, match="verified_trust_evidence"):
        registry.transition(
            child.brain_id, BrainStatus.ACTIVE, mother_approved=True,
            human_approved=True, verification_passed=True, reason="activation test",
        )
    registry.close()


def test_activation_without_human_approval_is_blocked(tmp_path):
    registry = ChildInstanceRegistry(tmp_path / "children.db")
    child = make_child()
    registry.register(
        child, mother_approved=True, human_approved=True, authorization_valid=True
    )
    registry.update_trust(
        child.brain_id, BrainTrustStatus.VERIFIED,
        evidence="verified test evidence", mother_approved=True,
        human_approved=True, reason="trust approval",
    )
    registry.transition(
        child.brain_id, BrainStatus.READY, mother_approved=True,
        verification_passed=True, reason="ready approval",
    )
    with pytest.raises(PermissionError, match="activation_requires_mother_human"):
        registry.transition(
            child.brain_id, BrainStatus.ACTIVE, mother_approved=True,
            human_approved=False, verification_passed=True, reason="missing human approval",
        )
    registry.close()


def test_safe_pause_and_failure_recording_do_not_require_passing_verification(tmp_path):
    registry = ChildInstanceRegistry(tmp_path / "children.db")
    child = make_child()
    registry.register(
        child, mother_approved=True, human_approved=True, authorization_valid=True
    )
    registry.update_trust(
        child.brain_id, BrainTrustStatus.VERIFIED,
        evidence="verified test evidence", mother_approved=True,
        human_approved=True, reason="trust approval",
    )
    registry.transition(
        child.brain_id, BrainStatus.READY, mother_approved=True,
        verification_passed=True, reason="ready approval",
    )
    registry.transition(
        child.brain_id, BrainStatus.ACTIVE, mother_approved=True,
        human_approved=True, verification_passed=True, reason="activation approval",
    )
    paused = registry.transition(
        child.brain_id, BrainStatus.PAUSED, human_approved=True,
        verification_passed=False, reason="emergency safe stop",
    )
    assert paused["to_status"] == "paused"
    failed = registry.transition(
        child.brain_id, BrainStatus.FAILED,
        verification_passed=False, reason="runtime failure recorded",
    )
    assert failed["to_status"] == "failed"
    assert registry.verify_integrity() is True
    registry.close()


def test_child_instance_state_and_event_log_tampering_is_detected(tmp_path):
    path = tmp_path / "children.db"
    registry = ChildInstanceRegistry(path)
    child = make_child()
    registry.register(
        child, mother_approved=True, human_approved=True, authorization_valid=True
    )
    registry._db.execute(
        "UPDATE child_instances SET data=? WHERE brain_id=?",
        ('{"brain_id":"child-brain-test-1","status":"active"}', child.brain_id),
    )
    registry._db.commit()
    assert registry.verify_integrity() is False
    with pytest.raises(ValueError, match="integrity_failure"):
        registry.get(child.brain_id)
    registry.close()


def test_duplicate_and_reserved_root_ids_are_rejected(tmp_path):
    registry = ChildInstanceRegistry(tmp_path / "children.db")
    root_id = SahibexRootIdentity().BRAIN_ID
    reserved = make_child(brain_id=root_id)
    with pytest.raises(ValueError, match="reserved"):
        registry.register(
            reserved, mother_approved=True, human_approved=True, authorization_valid=True
        )
    child = make_child()
    registry.register(
        child, mother_approved=True, human_approved=True, authorization_valid=True
    )
    with pytest.raises(ValueError, match="already_registered"):
        registry.register(
            child, mother_approved=True, human_approved=True, authorization_valid=True
        )
    registry.close()
