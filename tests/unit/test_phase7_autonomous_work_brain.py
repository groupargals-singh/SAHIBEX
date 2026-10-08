from pathlib import Path

from core.agent.autonomous_work_brain import AutonomousWorkBrain
from core.agent_goal import AgentGoal
from core.brain.tool_brain import ToolBrain
from core.policies.approval import PermissionEngine


def test_phase7_full_autonomous_lifecycle():
    brain = AutonomousWorkBrain()
    goal = AgentGoal("complete a multi-step verified task", "execute", success_criteria=("all work complete",))
    seen = []

    def execute(step):
        seen.append(step.title)
        return f"done:{step.title}"

    result = brain.run(
        goal,
        execute_step=execute,
        verify_step=lambda step, output: output == f"done:{step.title}",
    )
    assert result.success
    assert result.status == "COMPLETED"
    assert result.verification_status == "VERIFIED"
    assert result.metadata["controlled_until_done"] is True
    assert len(result.completed_steps) == 3
    assert seen == ["Understand objective", "Perform required work", "Verify result"]


def test_phase7_failure_recovery_then_success():
    brain = AutonomousWorkBrain()
    goal = AgentGoal("recover a failed step", "execute", success_criteria=("verified",))
    calls = {"n": 0}

    def execute(step):
        calls["n"] += 1
        if step.title == "Perform required work" and calls["n"] == 2:
            raise RuntimeError("transient")
        return "ok"

    result = brain.run(goal, execute_step=execute, verify_step=lambda s, o: o == "ok")
    assert result.success
    assert calls["n"] == 4


def test_phase7_checkpoint_resume():
    brain = AutonomousWorkBrain()
    goal = AgentGoal("resume interrupted work", "execute", success_criteria=("verified",))

    def execute_first(step):
        if step.title == "Perform required work":
            raise RuntimeError("interrupt")
        return "ok"

    first = brain.run(
        goal,
        execute_step=execute_first,
        verify_step=lambda s, o: True,
        job_id="resume-job",
        runtime_id="rt",
        max_steps=1,
    )
    assert not first.success
    assert first.checkpoint_sequence == 1

    second = brain.run(
        goal,
        execute_step=lambda step: "ok",
        verify_step=lambda s, o: True,
        job_id="resume-job",
        runtime_id="rt",
    )
    assert second.success
    assert second.resumed
    assert second.verification_status == "VERIFIED"


def test_phase7_security_boundary():
    brain = AutonomousWorkBrain()
    intake = brain.intake.intake("x", intent="execute", success_criteria=("ok",))
    assert intake.accepted
    assert intake.grants_permission is False
    assert brain.jobs.grants_permission() is False
    assert brain.checkpoints.grants_permission() is False
    assert brain.grants_permission() is False
    assert brain.modifies_constitution() is False


def test_phase7_real_tool_brain_execution_boundary():
    brain = AutonomousWorkBrain()
    goal = AgentGoal(
        "use a permitted local tool and verify it",
        "execute",
        success_criteria=("tool result verified",),
    )
    tool_brain = ToolBrain(PermissionEngine(), project_root=Path.cwd())

    queries = {
        "Understand objective": ("list directory", {"path": "."}),
        "Perform required work": ("read file", {"path": "core/agent_goal.py"}),
        "Verify result": ("file info", {"path": "core/agent_goal.py"}),
    }

    def execute(step):
        query, kwargs = queries[step.title]
        return tool_brain.execute(query, **kwargs)

    def verify(step, output):
        return bool(output.success and output.allowed and output.error is None)

    result = brain.run(goal, execute_step=execute, verify_step=verify)
    assert result.success
    assert result.verification_status == "VERIFIED"

from core.brain.master_brain import MasterBrain


def test_phase7_master_brain_integration():
    master = MasterBrain()
    goal = AgentGoal("master brain autonomous work", "execute", success_criteria=("verified",))
    result = master.run_autonomous_work(
        goal,
        execute_step=lambda step: "ok",
        verify_step=lambda step, output: output == "ok",
    )
    assert result.success
    assert result.verification_status == "VERIFIED"
