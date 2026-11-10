from core.orchestrator.task_state import TaskManager, TaskStatus
from core.research.storage import ResearchStorage
from core.agent.long_running_jobs import LongRunningJobManager

def test_task_graph_survives_manager_recreation(tmp_path):
    db = tmp_path / "graph.sqlite3"
    first = TaskManager(storage=ResearchStorage(db))
    goal = first.create_goal("persist complete graph")
    parent = first.create_task(goal.goal_id, "parent")
    child = first.create_task(goal.goal_id, "child", dependencies=[parent.task_id], parent_task_id=parent.task_id)
    parent.mark_ready(); parent.mark_running(); parent.complete({"ok": True})
    first.persist_goal(goal.goal_id)
    second = TaskManager(storage=ResearchStorage(db))
    restored = second.get_goal(goal.goal_id)
    assert restored is not None and len(restored.tasks) == 2
    assert second.get_task(parent.task_id).status == TaskStatus.COMPLETED
    assert second.get_task(child.task_id).dependencies == [parent.task_id]
    assert [t.task_id for t in second.ready_tasks(goal.goal_id)] == [child.task_id]

def test_job_lifecycle_restart_pauses_running_and_keeps_terminal(tmp_path):
    path = tmp_path / "jobs.json"
    first = LongRunningJobManager(path)
    first.create("active", "resume only on explicit request", "phone")
    first.start("active")
    first.checkpoint("active", {"step": 2, "api_token": "never-persist"})
    first.create("done", "completed objective")
    first.start("done"); first.complete("done")
    second = LongRunningJobManager(path)
    assert second.get("active").status == "paused"
    assert second.get("active").sequence == 2
    assert second.checkpoint_for("active").state == {"step": 2}
    assert second.get("done").status == "completed"
    assert any((item.get("reason") or "").startswith("Interrupted") for item in second.history("active"))
    assert "never-persist" not in path.read_text(encoding="utf-8")
    assert path.stat().st_mode & 0o777 == 0o600

def test_running_task_is_recovered_as_ready_without_execution(tmp_path):
    db = tmp_path / "interrupted.sqlite3"
    first = TaskManager(storage=ResearchStorage(db))
    goal = first.create_goal("interrupted task")
    task = first.create_task(goal.goal_id, "was running")
    task.mark_ready(); task.mark_running()
    first.persist_goal(goal.goal_id)
    second = TaskManager(storage=ResearchStorage(db))
    recovered = second.get_task(task.task_id)
    assert recovered.status == TaskStatus.READY
    assert recovered.metadata["recovered_after_restart"] is True


def test_plan_manifest_recovers_even_if_latest_checkpoint_is_missing(tmp_path):
    from core.agent.autonomous_work_brain import AutonomousWorkBrain
    from core.agent_goal import AgentGoal

    checkpoint = tmp_path / "plan-checkpoints.json"
    goal = AgentGoal("recover from graph manifest", "execute", success_criteria=("verified",))
    first = AutonomousWorkBrain(checkpoint_path=checkpoint)
    first_result = first.run(goal, execute_step=lambda step: "ok",
                             verify_step=lambda step, output: True,
                             job_id="manifest-job", runtime_id="phone", max_steps=1)
    assert not first_result.success
    old_plan_id = first.last_plan.plan_id
    old_goal_ids = [g.goal_id for g in first.task_manager.goals.values()]
    checkpoint.unlink()

    calls = []
    second = AutonomousWorkBrain(checkpoint_path=checkpoint)
    result = second.run(goal, execute_step=lambda step: calls.append(step.title) or "ok",
                        verify_step=lambda step, output: True,
                        job_id="manifest-job", runtime_id="phone")
    assert result.success and result.resumed
    assert second.last_plan.plan_id == old_plan_id
    assert calls == ["Perform required work", "Verify result"]
    assert [g.goal_id for g in second.task_manager.goals.values()] == old_goal_ids

def test_task_graph_persistence_sanitizes_nested_sensitive_result_fields(tmp_path):
    db = tmp_path / "sanitized.sqlite3"
    first = TaskManager(storage=ResearchStorage(db))
    goal = first.create_goal("sanitized result")
    task = first.create_task(goal.goal_id, "save output")
    task.mark_ready(); task.mark_running()
    task.complete({"answer": "ok", "nested": {"api_token": "sensitive", "value": 1}})
    first.persist_goal(goal.goal_id)
    restored = TaskManager(storage=ResearchStorage(db)).get_task(task.task_id)
    assert restored.result == {"answer": "ok", "nested": {"value": 1}}
