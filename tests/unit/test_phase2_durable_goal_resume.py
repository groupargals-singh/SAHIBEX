from __future__ import annotations

import json

import pytest

from core.agent.checkpoint_resume import CheckpointResumeStore
from core.agent.autonomous_work_brain import AutonomousWorkBrain
from core.agent_goal import AgentGoal


def test_checkpoint_store_survives_new_instance_and_rejects_tampering(tmp_path):
    path = tmp_path / "runtime" / "checkpoints.json"
    first = CheckpointResumeStore(path)
    record = first.save(
        "durable-job",
        "phone-runtime",
        3,
        {"completed_titles": ["Understand objective"], "nested": {"api_token": "do-not-store"}},
    )
    assert record.state == {"completed_titles": ["Understand objective"], "nested": {}}
    assert "do-not-store" not in path.read_text(encoding="utf-8")

    second = CheckpointResumeStore(path)
    assert second.resume_state("durable-job", runtime_id="phone-runtime") == record.state
    assert path.stat().st_mode & 0o777 == 0o600

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["records"][0]["state"]["completed_titles"] = ["tampered"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="corrupted or incompatible"):
        CheckpointResumeStore(path)


def test_snapshot_import_is_all_or_nothing():
    source = CheckpointResumeStore()
    source.save("valid", "runtime", 1, {"step": 1})
    snapshot = source.export_snapshot()
    invalid = dict(snapshot[0])
    invalid["job_id"] = "invalid"
    invalid["state"] = {"step": 99}

    target = CheckpointResumeStore()
    target.save("existing", "runtime", 1, {"keep": True})
    before = target.export_snapshot()
    with pytest.raises(ValueError, match="corrupted"):
        target.import_snapshot([snapshot[0], invalid])
    assert target.export_snapshot() == before


def test_autonomous_work_resumes_after_process_restart(tmp_path):
    path = tmp_path / "autonomous-checkpoints.json"
    goal = AgentGoal(
        "continue work after runtime restart",
        "execute",
        success_criteria=("all steps verified",),
    )
    first_calls = []
    first_brain = AutonomousWorkBrain(checkpoint_path=path)

    first = first_brain.run(
        goal,
        execute_step=lambda step: first_calls.append(step.title) or f"done:{step.title}",
        verify_step=lambda step, output: True,
        job_id="restartable-job",
        runtime_id="phone",
        max_steps=1,
    )
    assert not first.success
    assert first.checkpoint_sequence == 1
    assert first_calls == ["Understand objective"]
    saved_state = first_brain.checkpoints.resume_state("restartable-job", runtime_id="phone")
    original_plan_id = saved_state["plan"]["plan_id"]
    original_task_goal_id = saved_state["task_goal_id"]
    assert len(saved_state["plan"]["goals"]) == 3

    second_calls = []
    restarted_brain = AutonomousWorkBrain(checkpoint_path=path)
    second = restarted_brain.run(
        goal,
        execute_step=lambda step: second_calls.append(step.title) or f"done:{step.title}",
        verify_step=lambda step, output: True,
        job_id="restartable-job",
        runtime_id="phone",
    )
    assert second.success
    assert second.resumed is True
    assert restarted_brain.last_plan.plan_id == original_plan_id
    restored_goal = restarted_brain.task_manager.get_goal(original_task_goal_id)
    assert restored_goal is not None and len(restored_goal.tasks) == 3
    assert len([g for g in restarted_brain.task_manager.goals.values()
                if g.metadata.get("autonomous_job_id") == "restartable-job"]) == 1
    assert "Understand objective" not in second_calls
    assert second_calls == ["Perform required work", "Verify result"]
    assert second.verification_status == "VERIFIED"
    assert restarted_brain.checkpoints.grants_permission() is False
    assert restarted_brain.checkpoints.executes_protected_actions() is False
