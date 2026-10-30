#!/usr/bin/env python3
"""Bounded live P4 acceptance using the real MasterBrain manager and temp DBs.

All durable child data is isolated under a TemporaryDirectory. No production
child registry/memory database is opened or modified.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.brain.master_brain import MasterBrain
from core.brain.research_learning_command import DepartmentOperation


def close_brain(brain: MasterBrain) -> None:
    manager = brain.specialist_child_brains
    for record in list(manager._records.values()):
        record.memory.close()
    if manager.instance_registry is not None:
        manager.instance_registry.close()


def main() -> int:
    report = {"production_data_touched": False, "checks": {}}
    with tempfile.TemporaryDirectory(prefix="sahibex-p4-live-") as tmp:
        root = Path(tmp)
        os.environ["SAHIBEX_CHILD_REGISTRY_DB"] = str(root / "child_registry.sqlite3")
        os.environ["SAHIBEX_CHILD_MEMORY_DB"] = str(root / "child_memory.sqlite3")
        os.environ["SAHIBEX_SELF_IMPROVEMENT_AUDIT_DB"] = str(root / "self_improvement_audit.sqlite3")
        os.environ["SAHIBEX_SELF_IMPROVEMENT_STATE_DB"] = str(root / "self_improvement_state.sqlite3")

        brain = MasterBrain()
        manager = brain.specialist_child_brains
        army = manager.create_child(
            name="P4 Acceptance Army",
            description="temporary independent analysis worker",
            specialization="research",
            mother_approved=True,
            human_approved=True,
        )
        labour = manager.create_child(
            name="P4 Acceptance Labour",
            description="temporary independent evidence worker",
            specialization="research",
            mother_approved=True,
            human_approved=True,
        )
        for record, evidence in (
            (army, "P4 disposable acceptance identity verification"),
            (labour, "P4 disposable acceptance identity verification"),
        ):
            manager.verify_trust(
                record.brain.brain_id,
                evidence=evidence,
                mother_approved=True,
                human_approved=True,
                verification_passed=True,
            )
            manager.activate(
                record.brain.brain_id,
                mother_approved=True,
                human_approved=True,
            )

        army_id, labour_id = army.brain.brain_id, labour.brain.brain_id
        army.memory.write("army-private", {"claim": "alpha"})
        labour.memory.write("labour-private", {"evidence": "alpha"})
        report["checks"]["child_memory_namespace_isolation"] = (
            army.memory.read("labour-private") is None
            and labour.memory.read("army-private") is None
        )
        if not report["checks"]["child_memory_namespace_isolation"]:
            raise AssertionError("child memory namespace isolation failed")

        seen: list[tuple[str, str]] = []
        manager.register_handler(
            army_id,
            lambda request, metadata: seen.append(("army", request)) or {"claim": "alpha"},
        )
        manager.register_handler(
            labour_id,
            lambda request, metadata: seen.append(("labour", request)) or {"evidence": "alpha"},
        )
        result = brain.dispatch_worker_team(
            DepartmentOperation.RESEARCH,
            "independently verify alpha claim",
            army_child_id=army_id,
            labour_child_id=labour_id,
            verify_results=lambda a, l: a.get("claim") == l.get("evidence"),
            mother_approved=True,
            human_approved=True,
        )
        report["checks"]["real_dual_worker_execution_and_joint_verification"] = (
            [r[0] for r in seen] == ["army", "labour"]
            and result.trace.status.value == "completed"
            and result.result["verification_status"] == "VERIFIED"
        )
        if not report["checks"]["real_dual_worker_execution_and_joint_verification"]:
            raise AssertionError(f"dual worker acceptance failed: {result!r}")

        report["checks"]["authority_boundary"] = (
            manager.can_child_grant_authority() is False
            and manager.can_child_modify_constitution() is False
            and manager.can_child_override_mother() is False
            and manager.protected_actions_stay_with_mother() is True
        )
        if not report["checks"]["authority_boundary"]:
            raise AssertionError("child authority boundary failed")

        try:
            brain.dispatch_worker_team(
                DepartmentOperation.RESEARCH,
                "must not run without approval",
                army_child_id=army_id,
                labour_child_id=labour_id,
                verify_results=lambda a, l: True,
            )
        except PermissionError:
            report["checks"]["approval_gate"] = True
        else:
            raise AssertionError("worker dispatch succeeded without approvals")

        report["checks"]["registry_hash_chain_before_restart"] = manager.instance_registry.verify_integrity()
        if not report["checks"]["registry_hash_chain_before_restart"]:
            raise AssertionError("registry integrity failed before restart")

        # Close every SQLite connection as if the process were shutting down.
        close_brain(brain)
        brain = MasterBrain()
        manager = brain.specialist_child_brains
        restored_army = manager.get(army_id)
        restored_labour = manager.get(labour_id)
        if restored_army is None or restored_labour is None:
            raise AssertionError("child identities were not restored")
        report["checks"]["identity_parent_and_memory_survive_restart"] = (
            restored_army.brain.parent_brain_id == "sahibex-master-brain"
            and restored_labour.brain.parent_brain_id == "sahibex-master-brain"
            and restored_army.runtime_state.value == "paused"
            and restored_labour.runtime_state.value == "paused"
            and restored_army.brain.trust_status.value == "unverified"
            and restored_labour.brain.trust_status.value == "unverified"
            and restored_army.memory.read("army-private") == {"claim": "alpha"}
            and restored_labour.memory.read("labour-private") == {"evidence": "alpha"}
            and restored_army.memory.read("labour-private") is None
            and restored_labour.memory.read("army-private") is None
        )
        if not report["checks"]["identity_parent_and_memory_survive_restart"]:
            raise AssertionError("restart identity/memory/isolation acceptance failed")

        # No callable handler is restored from disk: dispatch fails closed.
        blocked = manager.dispatch(army_id, "must not execute after restart")
        report["checks"]["restart_requires_fresh_approval_and_handler_rebind"] = not blocked.success
        if blocked.success:
            raise AssertionError("restored child executed before re-approval/rebind")

        for child_id in (army_id, labour_id):
            manager.resume(
                child_id,
                mother_approved=True,
                human_approved=True,
                verification_passed=True,
                verification_evidence="fresh P4 post-restart verification",
            )
            manager.activate(child_id, mother_approved=True, human_approved=True)
        manager.register_handler(
            army_id,
            lambda request, metadata: {"claim": "beta"},
        )
        manager.register_handler(
            labour_id,
            lambda request, metadata: {"evidence": "beta"},
        )
        post_restart = brain.dispatch_worker_team(
            DepartmentOperation.RESEARCH,
            "verify beta after restart",
            army_child_id=army_id,
            labour_child_id=labour_id,
            verify_results=lambda a, l: a.get("claim") == l.get("evidence"),
            mother_approved=True,
            human_approved=True,
        )
        report["checks"]["dispatch_after_fresh_approval_and_rebind"] = (
            post_restart.trace.status.value == "completed"
            and post_restart.result["verification_status"] == "VERIFIED"
        )
        if not report["checks"]["dispatch_after_fresh_approval_and_rebind"]:
            raise AssertionError("post-restart dispatch failed")

        manager.suspend(army_id, mother_approved=True, reason="P4 suspension check")
        paused_dispatch = manager.dispatch(army_id, "must be blocked while paused")
        report["checks"]["suspension_blocks_dispatch"] = not paused_dispatch.success
        if paused_dispatch.success:
            raise AssertionError("suspended child executed")
        manager.resume(
            army_id,
            mother_approved=True,
            human_approved=True,
            verification_passed=True,
            verification_evidence="fresh verification after suspension",
        )
        manager.suspend(labour_id, mother_approved=True, reason="P4 retirement check")
        manager.retire(labour_id, human_approved=True)
        report["checks"]["resume_and_retirement_lifecycle"] = (
            manager.get(army_id).runtime_state.value == "ready"
            and manager.get(labour_id).runtime_state.value == "retired"
        )
        if not report["checks"]["resume_and_retirement_lifecycle"]:
            raise AssertionError("resume/retirement lifecycle failed")

        report["checks"]["registry_hash_chain_after_lifecycle"] = manager.instance_registry.verify_integrity()
        if not report["checks"]["registry_hash_chain_after_lifecycle"]:
            raise AssertionError("registry hash chain failed after lifecycle transitions")
        close_brain(brain)

    report["overall_status"] = "PASS"
    report["check_count"] = len(report["checks"])
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
