from __future__ import annotations

import sqlite3

import pytest

from core.brain.continuous_learning_improvement import (
    ContinuousLearningImprovement,
    ImprovementKind,
    SkillStatus,
)
from core.brain.self_improvement_state_store import SelfImprovementStateStore
from security.audit.child_self_improvement_audit_store import ChildSelfImprovementAuditStore


def _proposal(runtime, skill_id=None, name="Persistent skill"):
    return runtime.propose_skill(
        skill_id=skill_id,
        name=name,
        description="Metadata-only; no executable code changes.",
        kind=ImprovementKind.SKILL_IMPROVEMENT if skill_id else ImprovementKind.NEW_SKILL,
        reason="P6 restart recovery acceptance",
        expected_benefit="Verify persistent version state",
        expected_risk="No code execution; rollback tested",
        protected_update=True,
    )


def _activate(runtime, proposal):
    runtime.test_skill(proposal.proposal_id, security_passed=True, regression_passed=True, verification_passed=True, confidence=0.95)
    runtime.approve_protected_update(proposal.proposal_id, mother_approved=True, human_approved=True)
    return runtime.activate_skill(proposal.proposal_id)


def test_active_version_and_proposals_survive_runtime_restart(tmp_path):
    state_path = tmp_path / "state.sqlite3"
    audit_path = tmp_path / "audit.sqlite3"
    state = SelfImprovementStateStore(state_path)
    audit = ChildSelfImprovementAuditStore(audit_path)
    runtime = ContinuousLearningImprovement(state_store=state, audit_store=audit)
    v1 = _proposal(runtime)
    active1 = _activate(runtime, v1)
    v2 = _proposal(runtime, skill_id=active1.skill_id, name="Persistent skill v2")
    runtime.test_skill(v2.proposal_id, security_passed=True, regression_passed=True, verification_passed=True)
    runtime.approve_protected_update(v2.proposal_id, mother_approved=True, human_approved=True)
    state.close()
    audit.close()

    # New stores and a new runtime simulate a real application-process restart.
    state2 = SelfImprovementStateStore(state_path)
    audit2 = ChildSelfImprovementAuditStore(audit_path)
    recovered = ContinuousLearningImprovement(state_store=state2, audit_store=audit2)
    assert recovered.active_skill(active1.skill_id).version == 1
    assert recovered.proposal(v2.proposal_id).status == SkillStatus.TESTED
    assert recovered.skill_versions(active1.skill_id)[1].status == SkillStatus.TESTED
    active2 = recovered.activate_skill(v2.proposal_id)
    assert active2.version == 2
    assert recovered.active_skill(active1.skill_id).version == 2
    restored = recovered.rollback_skill(active1.skill_id, target_version=1, mother_approved=True, human_approved=True, verification_passed=True)
    assert restored.version == 1
    state2.close()
    audit2.close()

    state3 = SelfImprovementStateStore(state_path)
    audit3 = ChildSelfImprovementAuditStore(audit_path)
    after_rollback_restart = ContinuousLearningImprovement(state_store=state3, audit_store=audit3)
    assert after_rollback_restart.active_skill(active1.skill_id).version == 1
    assert audit3.verify_chain()
    assert after_rollback_restart.capability_contract()["restart_recovery"] is True
    state3.close()
    audit3.close()


def test_state_integrity_failure_fails_closed(tmp_path):
    path = tmp_path / "state.sqlite3"
    state = SelfImprovementStateStore(path)
    runtime = ContinuousLearningImprovement(state_store=state)
    proposal = _proposal(runtime)
    _activate(runtime, proposal)
    state.close()

    db = sqlite3.connect(path)
    db.execute("UPDATE self_improvement_state SET payload='{}' WHERE singleton=1")
    db.commit()
    db.close()

    with pytest.raises(RuntimeError, match="integrity_check_failed"):
        ContinuousLearningImprovement(state_store=SelfImprovementStateStore(path))


def test_activation_store_failure_restores_previous_durable_active_version(tmp_path, monkeypatch):
    state = SelfImprovementStateStore(tmp_path / "state.sqlite3")
    runtime = ContinuousLearningImprovement(state_store=state)
    v1 = _proposal(runtime)
    active1 = _activate(runtime, v1)
    v2 = _proposal(runtime, skill_id=active1.skill_id, name="Persistent skill v2")
    runtime.test_skill(v2.proposal_id, security_passed=True, regression_passed=True, verification_passed=True)
    runtime.approve_protected_update(v2.proposal_id, mother_approved=True, human_approved=True)
    original_save = state.save
    calls = {"n": 0}
    def fail_once(payload):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("injected state commit failure")
        return original_save(payload)
    monkeypatch.setattr(state, "save", fail_once)
    with pytest.raises(OSError, match="injected state commit failure"):
        runtime.activate_skill(v2.proposal_id)
    assert runtime.active_skill(active1.skill_id).version == 1
    state.close()
    recovered = ContinuousLearningImprovement(state_store=SelfImprovementStateStore(tmp_path / "state.sqlite3"))
    assert recovered.active_skill(active1.skill_id).version == 1
    recovered.state_store.close()


def test_tampered_audit_blocks_runtime_recovery_on_startup(tmp_path):
    audit_path = tmp_path / "audit.sqlite3"
    audit = ChildSelfImprovementAuditStore(audit_path)
    runtime = ContinuousLearningImprovement(audit_store=audit)
    proposal = _proposal(runtime)
    audit._connection.execute("DROP TRIGGER child_improvement_audit_no_update")
    audit._connection.execute("UPDATE child_improvement_audit_events SET payload='{}' WHERE sequence=1")
    audit._connection.commit()
    audit.close()
    reopened = ChildSelfImprovementAuditStore(audit_path)
    with pytest.raises(RuntimeError, match="audit_chain_invalid_on_startup"):
        ContinuousLearningImprovement(audit_store=reopened)
    reopened.close()


def test_final_verified_answer_promotes_only_linked_multisource_knowledge():
    from types import SimpleNamespace
    from core.brain.mother_research_integration import MotherResearchIntegration
    from core.brain.knowledge_brain import KnowledgeBrain
    from core.research.models import KnowledgeCandidate
    from core.research.storage import ResearchStorage

    storage = ResearchStorage(":memory:")
    candidate = KnowledgeCandidate(
        knowledge_id="p6-promote-1",
        statement="A claim supported by independent publishers.",
        findings=["finding-1"],
        evidence=["evidence-1", "evidence-2"],
        confidence=0.92,
        verified=False,
        metadata={"source": "live-research-test"},
    )
    storage.save_knowledge(candidate)
    answer_evidence = SimpleNamespace(
        knowledge_id="p6-promote-1",
        verified=True,
        confidence=0.92,
        source_ids=["publisher-a", "publisher-b"],
        evidence_texts=["publisher A supports claim", "publisher B supports claim"],
    )
    synthesized = SimpleNamespace(
        verified=True,
        status="VERIFIED",
        knowledge_ids=["p6-promote-1"],
        evidence=[answer_evidence],
    )
    pipeline_result = SimpleNamespace(
        answer=synthesized,
        arbitration=SimpleNamespace(accepted=True),
        aggregation=SimpleNamespace(
            unresolved_conflict_count=0,
            answer_traceability=SimpleNamespace(traces=[
                SimpleNamespace(
                    knowledge_id="p6-promote-1",
                    trace_complete=True,
                    supported=True,
                    verified=True,
                    source_ids=["publisher-a", "publisher-b"],
                    evidence_ids=["evidence-1", "evidence-2"],
                )
            ]),
        ),
    )
    context = SimpleNamespace(answer=pipeline_result)
    integration = object.__new__(MotherResearchIntegration)
    integration.storage = storage

    outcome = integration._promote_verified_answer_knowledge(
        context, query="verified claim?", job_id="p6-job-1"
    )
    assert outcome["status"] == "PROMOTED"
    assert outcome["promoted_count"] == 1
    knowledge = KnowledgeBrain(storage=storage).retrieve(
        "independent publishers", verified_only=True
    )
    assert knowledge.knowledge_ids == ("p6-promote-1",)
    lifecycle = storage.knowledge_verification_lifecycle("p6-promote-1")
    assert lifecycle["verification_status"] == "VERIFIED"
    assert lifecycle["verification_event_count"] == 1
    assert storage.get_knowledge("p6-promote-1").metadata["verified_answer_promotion"]["research_job_id"] == "p6-job-1"
    storage.close()


def test_unresolved_conflict_blocks_verified_answer_promotion():
    from types import SimpleNamespace
    from core.brain.mother_research_integration import MotherResearchIntegration
    from core.research.storage import ResearchStorage

    storage = ResearchStorage(":memory:")
    synthesized = SimpleNamespace(
        verified=True, status="VERIFIED", knowledge_ids=["claim-x"], evidence=[]
    )
    pipeline_result = SimpleNamespace(
        answer=synthesized,
        arbitration=SimpleNamespace(accepted=True),
        aggregation=SimpleNamespace(unresolved_conflict_count=1),
    )
    integration = object.__new__(MotherResearchIntegration)
    integration.storage = storage
    outcome = integration._promote_verified_answer_knowledge(
        SimpleNamespace(answer=pipeline_result), query="conflicting claim", job_id="p6-job-conflict"
    )
    assert outcome["status"] == "BLOCKED"
    assert outcome["promoted_count"] == 0
    assert storage.knowledge_count() == 0
    storage.close()


def test_actual_subprocess_restart_restores_active_version_and_rollback(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    state_path = tmp_path / "process-state.sqlite3"
    audit_path = tmp_path / "process-audit.sqlite3"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root)

    setup = r"""
from core.brain.continuous_learning_improvement import ContinuousLearningImprovement, ImprovementKind
from core.brain.self_improvement_state_store import SelfImprovementStateStore
from security.audit.child_self_improvement_audit_store import ChildSelfImprovementAuditStore
state=SelfImprovementStateStore(r'REPLACE_STATE')
audit=ChildSelfImprovementAuditStore(r'REPLACE_AUDIT')
runtime=ContinuousLearningImprovement(state_store=state,audit_store=audit)
p=runtime.propose_skill(skill_id='process-restart-skill',name='restart v1',description='metadata only',kind=ImprovementKind.NEW_SKILL,protected_update=True)
runtime.test_skill(p.proposal_id,security_passed=True,regression_passed=True,verification_passed=True,confidence=.95)
runtime.approve_protected_update(p.proposal_id,mother_approved=True,human_approved=True)
runtime.activate_skill(p.proposal_id)
state.close(); audit.close()
""".replace("REPLACE_STATE", str(state_path)).replace("REPLACE_AUDIT", str(audit_path))
    first = subprocess.run([sys.executable, "-c", setup], cwd=root, env=env, text=True, capture_output=True, timeout=20)
    assert first.returncode == 0, first.stdout + first.stderr

    recovery = r"""
from core.brain.continuous_learning_improvement import ContinuousLearningImprovement, ImprovementKind
from core.brain.self_improvement_state_store import SelfImprovementStateStore
from security.audit.child_self_improvement_audit_store import ChildSelfImprovementAuditStore
state=SelfImprovementStateStore(r'REPLACE_STATE')
audit=ChildSelfImprovementAuditStore(r'REPLACE_AUDIT')
runtime=ContinuousLearningImprovement(state_store=state,audit_store=audit)
assert runtime.active_skill('process-restart-skill').version == 1
p=runtime.propose_skill(skill_id='process-restart-skill',name='restart v2',description='metadata only',kind=ImprovementKind.SKILL_IMPROVEMENT,protected_update=True)
runtime.test_skill(p.proposal_id,security_passed=True,regression_passed=True,verification_passed=True,confidence=.95)
runtime.approve_protected_update(p.proposal_id,mother_approved=True,human_approved=True)
runtime.activate_skill(p.proposal_id)
runtime.rollback_skill('process-restart-skill',target_version=1,mother_approved=True,human_approved=True,verification_passed=True)
state.close(); audit.close()
""".replace("REPLACE_STATE", str(state_path)).replace("REPLACE_AUDIT", str(audit_path))
    second = subprocess.run([sys.executable, "-c", recovery], cwd=root, env=env, text=True, capture_output=True, timeout=20)
    assert second.returncode == 0, second.stdout + second.stderr

    verify = r"""
from core.brain.continuous_learning_improvement import ContinuousLearningImprovement
from core.brain.self_improvement_state_store import SelfImprovementStateStore
from security.audit.child_self_improvement_audit_store import ChildSelfImprovementAuditStore
state=SelfImprovementStateStore(r'REPLACE_STATE')
audit=ChildSelfImprovementAuditStore(r'REPLACE_AUDIT')
runtime=ContinuousLearningImprovement(state_store=state,audit_store=audit)
assert runtime.active_skill('process-restart-skill').version == 1
assert audit.verify_chain()
print('ACTUAL_PROCESS_RESTART_RECOVERY=PASS')
state.close(); audit.close()
""".replace("REPLACE_STATE", str(state_path)).replace("REPLACE_AUDIT", str(audit_path))
    third = subprocess.run([sys.executable, "-c", verify], cwd=root, env=env, text=True, capture_output=True, timeout=20)
    assert third.returncode == 0, third.stdout + third.stderr
    assert "ACTUAL_PROCESS_RESTART_RECOVERY=PASS" in third.stdout
