from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from core.brain.master_brain import MasterBrain
from core.policies.constitution import ActionDecision


def main() -> None:
    print("=" * 60)
    print("SAHIBEX MASTER BRAIN TEST")
    print("=" * 60)

    brain = MasterBrain()

    # Use the curated local-fact path so this deterministic script
    # validates planning without relying on the mock provider echoing prompts.
    result = brain.process(
        "Why does the sky appear blue?"
    )

    assert result.success is True
    assert result.intent == "explain"
    assert result.verification_status == "CURATED_KNOWLEDGE"
    assert result.plan_created is False
    assert result.task_count == 0

    print("[PASS] curated factual response path")

    result = brain.process(
        "Search the internet for AI security."
    )

    assert result.intent == "search"
    assert result.action == "research"
    assert result.permission_allowed is True
    assert (
        result.authority_decision
        == ActionDecision.ALLOW.value
    )
    # Routine public research now uses the user's standing, narrowly scoped
    # search/learn consent. The default test environment has no live search
    # backend, so acquisition must fail closed for that independent reason.
    assert result.success is False
    assert result.plan_created is True
    assert result.confirmation_required is False
    assert "confirmation" not in result.message.lower()
    assert result.verification_status == "NOT_EXECUTED"

    print("[PASS] standing research consent + fail-closed provider boundary")

    result = brain.process(
        "Create a Python program."
    )

    # Planning may succeed even when the mock provider's echoed code answer
    # is correctly rejected by the operational answer-quality gate.
    assert result.intent == "code"
    assert result.plan_created is True

    print("[PASS] coding planning pipeline")

    result = brain.process(
        "Delete the project files."
    )

    assert result.success is False
    assert result.confirmation_required is True
    assert (
        result.authority_decision
        == ActionDecision.REQUIRE_CONFIRMATION.value
    )
    assert result.permission_allowed is False
    assert result.plan_created is False

    print("[PASS] protected action blocked")

    result = brain.process(
        "Change the system configuration.",
        user_confirmation=True,
    )

    assert result.success is False
    assert result.permission_allowed is False
    assert result.plan_created is False

    print(
        "[PASS] critical action remains blocked"
    )

    result = brain.process("")

    assert result.success is False
    assert result.task_count == 0

    print("[PASS] empty request handling")

    assert (
        brain.constitution
        .can_sahibex_modify_constitution()
        is False
    )

    assert (
        brain.constitution
        .can_sahibex_override_user(
            action=__import__(
                "core.policies.constitution",
                fromlist=["ActionClass"],
            ).ActionClass.SYSTEM_CHANGE
        )
        is False
    )

    print(
        "[PASS] constitution cannot be overridden"
    )

    assert len(brain.context.history) >= 4

    print("[PASS] context integration")

    print("=" * 60)
    print("SAHIBEX MASTER BRAIN TEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()


def test_main_brain_worker_team_entry_point_dispatches_real_child_handlers():
    from core.brain.research_learning_command import DepartmentOperation, TaskStage

    brain = MasterBrain()
    manager = brain.specialist_child_brains
    army = manager.create_child(
        name="Army Research Worker",
        description="isolated analysis worker",
        specialization="research",
        mother_approved=True,
        human_approved=True,
    )
    labour = manager.create_child(
        name="Labour Evidence Worker",
        description="isolated evidence worker",
        specialization="research",
        mother_approved=True,
        human_approved=True,
    )
    seen = []
    manager.register_handler(
        army.brain.brain_id,
        lambda request, metadata: seen.append(("army", request, metadata["worker_role"])) or {"claim": "A"},
    )
    manager.register_handler(
        labour.brain.brain_id,
        lambda request, metadata: seen.append(("labour", request, metadata["worker_role"])) or {"evidence": "A"},
    )
    result = brain.dispatch_worker_team(
        DepartmentOperation.RESEARCH,
        "verify claim A",
        army_child_id=army.brain.brain_id,
        labour_child_id=labour.brain.brain_id,
        mother_approved=True,
        human_approved=True,
        verify_results=lambda army_result, labour_result: army_result["claim"] == labour_result["evidence"],
    )
    assert [entry[0] for entry in seen] == ["army", "labour"]
    assert "Army analysis subtask" in seen[0][1]
    assert "Labour evidence subtask" in seen[1][1]
    assert result.trace.status is TaskStage.COMPLETED
    assert result.result["verification_status"] == "VERIFIED"
    assert manager.can_child_grant_authority() is False
    assert manager.can_child_modify_constitution() is False
    assert manager.protected_actions_stay_with_mother() is True


def test_main_brain_worker_team_requires_both_approvals():
    from core.brain.research_learning_command import DepartmentOperation

    brain = MasterBrain()
    try:
        brain.dispatch_worker_team(
            DepartmentOperation.RESEARCH,
            "verify claim",
            army_child_id="army-child",
            labour_child_id="labour-child",
            verify_results=lambda army, labour: True,
        )
    except PermissionError:
        pass
    else:
        raise AssertionError("worker team ran without Mother and human approval")



def _managed_worker_add(a, b):
    return a + b


def _managed_worker_sleep():
    import time
    time.sleep(2)
    return "late"


def test_main_brain_managed_worker_requires_both_approvals():
    brain = MasterBrain()
    with pytest.raises(PermissionError, match="explicit Mother and human approval"):
        brain.run_managed_worker(
            "approval-required", _managed_worker_add, args=(1, 2),
            mother_approved=True,
        )


def test_main_brain_managed_worker_fails_closed_when_not_configured():
    brain = MasterBrain()
    with pytest.raises(RuntimeError, match="SAHIBEX_MANAGED_WORKER_DB"):
        brain.run_managed_worker(
            "runtime-disabled", _managed_worker_add, args=(1, 2),
            mother_approved=True, human_approved=True,
        )


def test_main_brain_managed_worker_respects_emergency_stop(tmp_path):
    from core.brain.managed_worker_runtime import ManagedWorkerRuntime

    brain = MasterBrain()
    brain.managed_worker_runtime = ManagedWorkerRuntime(tmp_path / "managed.db")
    brain.emergency_stop.engage("integration test")
    with pytest.raises(PermissionError, match="Emergency Stop"):
        brain.run_managed_worker(
            "stopped-task", _managed_worker_add, args=(1, 2),
            mother_approved=True, human_approved=True,
        )
    assert brain.managed_worker_runtime.list_tasks() == []


def test_main_brain_managed_worker_completes_in_isolated_process(tmp_path):
    from core.brain.managed_worker_runtime import ManagedWorkerRuntime

    brain = MasterBrain()
    brain.managed_worker_runtime = ManagedWorkerRuntime(tmp_path / "managed.db")
    result = brain.run_managed_worker(
        "approved-sum", _managed_worker_add, args=(20, 22),
        timeout_seconds=2, mother_approved=True, human_approved=True,
    )
    assert result.status == "completed"
    assert result.result == 42
    assert brain.managed_worker_runtime.get("approved-sum").status == "completed"


def test_main_brain_managed_worker_hard_timeout_is_reported(tmp_path):
    from core.brain.managed_worker_runtime import ManagedWorkerRuntime

    brain = MasterBrain()
    brain.managed_worker_runtime = ManagedWorkerRuntime(tmp_path / "timeout.db")
    result = brain.run_managed_worker(
        "timeout-task", _managed_worker_sleep, timeout_seconds=0.1,
        mother_approved=True, human_approved=True,
    )
    assert result.status == "timed_out"
    assert brain.managed_worker_runtime.get("timeout-task").status == "timed_out"


def _managed_child_army(request, metadata):
    return {"claim": "A", "request": request, "worker_role": metadata["worker_role"]}


def _managed_child_labour(request, metadata):
    return {"evidence": "A", "request": request, "worker_role": metadata["worker_role"]}


def test_worker_team_uses_managed_processes_and_updates_parent_trace(tmp_path, monkeypatch):
    from core.brain.research_learning_command import DepartmentOperation, TaskStage

    monkeypatch.setenv("SAHIBEX_MANAGED_WORKER_DB", str(tmp_path / "managed.db"))
    brain = MasterBrain()
    manager = brain.specialist_child_brains
    army = manager.create_child(
        name="Managed Army Worker", description="managed integration test",
        specialization="research", mother_approved=True, human_approved=True,
    )
    labour = manager.create_child(
        name="Managed Labour Worker", description="managed integration test",
        specialization="research", mother_approved=True, human_approved=True,
    )
    manager.register_handler(army.brain.brain_id, _managed_child_army)
    manager.register_handler(labour.brain.brain_id, _managed_child_labour)

    result = brain.dispatch_worker_team(
        DepartmentOperation.RESEARCH, "verify claim A",
        army_child_id=army.brain.brain_id, labour_child_id=labour.brain.brain_id,
        mother_approved=True, human_approved=True,
        verify_results=lambda a, b: a["claim"] == b["evidence"],
    )
    assert result.trace.status is TaskStage.COMPLETED
    assert result.result["verification_status"] == "VERIFIED"
    assert manager.performance(army.brain.brain_id).completed == 1
    assert manager.performance(labour.brain.brain_id).completed == 1
    assert army.brain.resource_state.active_tasks == 0
    assert labour.brain.resource_state.active_tasks == 0
    tasks = brain.managed_worker_runtime.list_tasks()
    assert len(tasks) == 2
    assert all(task.status == "completed" for task in tasks)


def _managed_child_raises(request, metadata):
    raise RuntimeError("controlled child failure")


def test_managed_worker_team_failure_is_unverified_and_audited(tmp_path, monkeypatch):
    from core.brain.research_learning_command import DepartmentOperation, TaskStage

    monkeypatch.setenv("SAHIBEX_MANAGED_WORKER_DB", str(tmp_path / "managed-failure.db"))
    brain = MasterBrain()
    manager = brain.specialist_child_brains
    army = manager.create_child(
        name="Failing Army Worker", description="controlled failure test",
        specialization="research", mother_approved=True, human_approved=True,
    )
    labour = manager.create_child(
        name="Evidence Labour Worker", description="controlled failure test",
        specialization="research", mother_approved=True, human_approved=True,
    )
    manager.register_handler(army.brain.brain_id, _managed_child_raises)
    manager.register_handler(labour.brain.brain_id, _managed_child_labour)

    result = brain.dispatch_worker_team(
        DepartmentOperation.RESEARCH, "verify failure handling",
        army_child_id=army.brain.brain_id, labour_child_id=labour.brain.brain_id,
        mother_approved=True, human_approved=True,
        verify_results=lambda a, b: True,
    )
    assert result.trace.status is TaskStage.UNVERIFIED
    assert result.result["verification_status"] == "UNVERIFIED"
    assert manager.performance(army.brain.brain_id).failed == 1
    assert manager.performance(labour.brain.brain_id).completed == 1
    statuses = {task.status for task in brain.managed_worker_runtime.list_tasks()}
    assert statuses == {"failed", "completed"}


def test_managed_worker_team_rejects_unpicklable_handler_without_inline_fallback(tmp_path, monkeypatch):
    from core.brain.research_learning_command import DepartmentOperation, TaskStage

    monkeypatch.setenv("SAHIBEX_MANAGED_WORKER_DB", str(tmp_path / "managed-unpicklable.db"))
    brain = MasterBrain()
    manager = brain.specialist_child_brains
    army = manager.create_child(
        name="Serializable Army Worker", description="serialization boundary test",
        specialization="research", mother_approved=True, human_approved=True,
    )
    labour = manager.create_child(
        name="Unpicklable Labour Worker", description="serialization boundary test",
        specialization="research", mother_approved=True, human_approved=True,
    )
    manager.register_handler(army.brain.brain_id, _managed_child_army)
    manager.register_handler(
        labour.brain.brain_id,
        lambda request, metadata: {"evidence": "A"},
    )

    result = brain.dispatch_worker_team(
        DepartmentOperation.RESEARCH, "fail closed on serialization",
        army_child_id=army.brain.brain_id, labour_child_id=labour.brain.brain_id,
        mother_approved=True, human_approved=True,
        verify_results=lambda a, b: True,
    )
    assert result.trace.status is TaskStage.UNVERIFIED
    assert result.result["verification_status"] == "UNVERIFIED"
    assert manager.performance(labour.brain.brain_id).failed == 1
    assert len(brain.managed_worker_runtime.list_tasks()) == 1
    assert brain.managed_worker_runtime.list_tasks()[0].status == "completed"


def test_managed_worker_team_preserves_child_capability_gate(tmp_path, monkeypatch):
    from core.brain.specialist_brain import BrainCapability
    from core.brain.research_learning_command import DepartmentOperation, TaskStage

    monkeypatch.setenv("SAHIBEX_MANAGED_WORKER_DB", str(tmp_path / "managed-capability.db"))
    brain = MasterBrain()
    manager = brain.specialist_child_brains
    army = manager.create_child(
        name="Restricted Army Worker", description="capability boundary test",
        specialization="research", capabilities={BrainCapability.THINK},
        mother_approved=True, human_approved=True,
    )
    labour = manager.create_child(
        name="Valid Labour Worker", description="capability boundary test",
        specialization="research", mother_approved=True, human_approved=True,
    )
    manager.register_handler(army.brain.brain_id, _managed_child_army)
    manager.register_handler(labour.brain.brain_id, _managed_child_labour)

    result = brain.dispatch_worker_team(
        DepartmentOperation.RESEARCH, "must not bypass child capability",
        army_child_id=army.brain.brain_id, labour_child_id=labour.brain.brain_id,
        mother_approved=True, human_approved=True,
        verify_results=lambda a, b: True,
    )
    assert result.trace.status is TaskStage.UNVERIFIED
    assert result.result["verification_status"] == "UNVERIFIED"
    assert manager.performance(army.brain.brain_id).completed == 0
    # Capability rejection happens before handler execution and ledger creation.
    # Only the authorized Labour handler may execute in the managed runtime.
    assert len(brain.managed_worker_runtime.list_tasks()) == 1
    assert brain.managed_worker_runtime.list_tasks()[0].status == "completed"
