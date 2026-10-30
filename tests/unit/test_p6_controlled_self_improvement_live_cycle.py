from __future__ import annotations

from security.audit.child_self_improvement_audit_store import ChildSelfImprovementAuditStore
from core.brain.continuous_learning_improvement import (
    ContinuousLearningImprovement,
    ImprovementKind,
    SkillStatus,
)


def _proposal(runtime, *, skill_id=None, name="Reversible metadata skill"):
    return runtime.propose_skill(
        skill_id=skill_id,
        name=name,
        description="Metadata-only test improvement; executes no code.",
        kind=ImprovementKind.SKILL_IMPROVEMENT if skill_id else ImprovementKind.NEW_SKILL,
        reason="P6 isolated controlled self-improvement acceptance",
        expected_benefit="Validate safe lifecycle",
        expected_risk="Test failure; rollback must restore prior version",
        protected_update=True,
    )


def _pass_tests(runtime, proposal):
    return runtime.test_skill(
        proposal.proposal_id,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
        confidence=0.95,
    )


def _approve(runtime, proposal):
    return runtime.approve_protected_update(
        proposal.proposal_id,
        mother_approved=True,
        human_approved=True,
    )


def test_p6_full_lifecycle_persists_audit_and_verified_rollback(tmp_path):
    audit_path = tmp_path / "p6-self-improvement-audit.sqlite3"
    store = ChildSelfImprovementAuditStore(audit_path)
    runtime = ContinuousLearningImprovement(audit_store=store)

    v1 = _proposal(runtime)
    _pass_tests(runtime, v1)
    try:
        runtime.approve_protected_update(
            v1.proposal_id, mother_approved=True, human_approved=False
        )
    except PermissionError:
        pass
    else:
        raise AssertionError("missing human approval must block")
    _approve(runtime, v1)
    active_v1 = runtime.activate_skill(v1.proposal_id)
    assert active_v1.status == SkillStatus.ACTIVE
    assert runtime.active_skill(active_v1.skill_id).version == 1

    v2 = _proposal(runtime, skill_id=active_v1.skill_id, name="Reversible metadata skill v2")
    _pass_tests(runtime, v2)
    _approve(runtime, v2)
    active_v2 = runtime.activate_skill(v2.proposal_id)
    assert active_v2.status == SkillStatus.ACTIVE
    assert runtime.active_skill(active_v1.skill_id).version == 2

    restored = runtime.rollback_skill(
        active_v1.skill_id,
        target_version=1,
        mother_approved=True,
        human_approved=True,
        verification_passed=True,
    )
    assert restored.version == 1
    assert restored.status == SkillStatus.ACTIVE
    assert runtime.active_skill(active_v1.skill_id).version == 1
    assert runtime.can_modify_constitution() is False
    assert runtime.can_self_authorize_protected_update() is False
    assert store.verify_chain() is True
    store.close()

    # Persistence survives closing/reopening the audit database.
    reopened = ChildSelfImprovementAuditStore(audit_path)
    assert reopened.verify_chain() is True
    events = [item["payload"]["event"] for item in reversed(reopened.list_events(limit=100))]
    decisions = [item["payload"]["decision"] for item in reversed(reopened.list_events(limit=100))]
    assert "proposal_created" in events
    assert "proposal_tests_completed" in events
    assert "approval_blocked" in events
    assert "approval_granted" in events
    assert "activation_started" in events
    assert "activation_committed" in events
    assert "rollback_started" in events
    assert "rollback_completed" in events
    assert "block" in decisions and "accept" in decisions
    assert all(item["payload"]["authority_changed"] is False for item in reopened.list_events(limit=100))
    assert all(item["payload"]["constitution_changed"] is False for item in reopened.list_events(limit=100))
    reopened.close()


def test_p6_failed_regression_never_activates_and_is_audited(tmp_path):
    store = ChildSelfImprovementAuditStore(tmp_path / "failed-tests.sqlite3")
    runtime = ContinuousLearningImprovement(audit_store=store)
    proposal = _proposal(runtime)
    result = runtime.test_skill(
        proposal.proposal_id,
        security_passed=True,
        regression_passed=False,
        verification_passed=True,
    )
    assert result.status == SkillStatus.RETIRED
    try:
        runtime.activate_skill(proposal.proposal_id)
    except PermissionError:
        pass
    else:
        raise AssertionError("failed regression must prevent activation")
    assert runtime.active_skill(proposal.skill_id) is None
    assert store.verify_chain() is True
    events = [item["payload"] for item in store.list_events(limit=100)]
    assert any(item["event"] == "proposal_tests_completed" and item["decision"] == "block" for item in events)
    assert any(item["event"] == "activation_blocked" and item["decision"] == "block" for item in events)
    store.close()


def test_p6_activation_commit_failure_restores_prior_active_version(tmp_path):
    store = ChildSelfImprovementAuditStore(tmp_path / "activation-recovery.sqlite3")
    runtime = ContinuousLearningImprovement(audit_store=store)
    v1 = _proposal(runtime)
    _pass_tests(runtime, v1)
    _approve(runtime, v1)
    runtime.activate_skill(v1.proposal_id)

    v2 = _proposal(runtime, skill_id=v1.skill_id, name="Reversible metadata skill v2")
    _pass_tests(runtime, v2)
    _approve(runtime, v2)

    original_append = store.append

    def fail_activation_commit(*, audit_id, payload):
        if payload.get("event") == "activation_committed":
            raise OSError("injected audit write failure")
        return original_append(audit_id=audit_id, payload=payload)

    store.append = fail_activation_commit
    try:
        runtime.activate_skill(v2.proposal_id)
    except OSError as exc:
        assert "injected audit write failure" in str(exc)
    else:
        raise AssertionError("injected commit failure should propagate")
    finally:
        store.append = original_append

    assert runtime.active_skill(v1.skill_id).version == 1
    assert runtime.skill_versions(v1.skill_id)[1].status != SkillStatus.ACTIVE
    assert store.verify_chain() is True
    events = [item["payload"] for item in reversed(store.list_events(limit=100))]
    assert any(item["event"] == "activation_started" and item.get("proposal_id") == v2.proposal_id for item in events)
    assert any(item["event"] == "activation_recovery" and item.get("proposal_id") == v2.proposal_id for item in events)
    assert not any(item["event"] == "activation_committed" and item.get("proposal_id") == v2.proposal_id for item in events)
    store.close()


def test_p6_tampered_audit_chain_blocks_activation(tmp_path):
    store = ChildSelfImprovementAuditStore(tmp_path / "tampered-chain.sqlite3")
    runtime = ContinuousLearningImprovement(audit_store=store)
    proposal = _proposal(runtime)
    _pass_tests(runtime, proposal)
    _approve(runtime, proposal)
    store._connection.execute("DROP TRIGGER child_improvement_audit_no_update")
    store._connection.execute(
        "UPDATE child_improvement_audit_events SET payload=? WHERE sequence=1",
        ('{"event":"tampered","decision":"accept"}',),
    )
    store._connection.commit()
    assert store.verify_chain() is False
    try:
        runtime.activate_skill(proposal.proposal_id)
    except RuntimeError as exc:
        assert "audit_chain_invalid" in str(exc)
    else:
        raise AssertionError("tampered audit must block activation")
    assert runtime.active_skill(proposal.skill_id) is None
    store.close()



def test_main_brain_wires_configured_persistent_audit_store(tmp_path, monkeypatch):
    from core.brain.master_brain import MasterBrain

    audit_path = tmp_path / "runtime-audit.sqlite3"
    state_path = tmp_path / "runtime-state.sqlite3"
    monkeypatch.setenv("SAHIBEX_SELF_IMPROVEMENT_AUDIT_DB", str(audit_path))
    monkeypatch.setenv("SAHIBEX_SELF_IMPROVEMENT_STATE_DB", str(state_path))
    brain = MasterBrain()
    assert brain.self_improvement_audit_store is not None
    assert brain.self_improvement_state_store is not None
    assert brain.continuous_learning.audit_store is brain.self_improvement_audit_store
    assert brain.continuous_learning.state_store is brain.self_improvement_state_store
    contract = brain.continuous_learning.capability_contract()
    assert contract["persistent_audit"] is True
    assert contract["fail_closed_on_audit_tamper"] is True
    assert brain.self_improvement_audit_store.verify_chain() is True
    brain.self_improvement_audit_store.close()
