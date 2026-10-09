"""Final commissioning evidence for the maintained SAHIBEX 6P overlay."""

from pathlib import Path

from core.agent.autonomous_work_brain import AutonomousWorkBrain
from core.agent_goal import AgentGoal
from core.agent_decomposition import GoalDecompositionEngine
from core.agent_planning import DynamicPlanningEngine
from core.agent_task_orchestration import AgentTaskOrchestrator
from core.brain.tool_brain import ToolBrain
from core.policies.approval import PermissionEngine
from core.orchestrator.task_state import TaskManager, TaskStatus


def _plan():
    goal = AgentGoal(
        "commission a dependency-aware verified task",
        "execute",
        success_criteria=("all work is completed and verified",),
    )
    decomposition = GoalDecompositionEngine().decompose(goal)
    assert decomposition.success
    plan = DynamicPlanningEngine().create_plan(decomposition.goals)
    return goal, plan


def test_6p5_dependency_orchestration_and_completion_propagation():
    _, plan = _plan()
    manager = TaskManager()
    result = AgentTaskOrchestrator(manager).create_tasks(plan)

    assert result.success
    assert len(result.task_ids) == 3
    assert len(result.ready_task_ids) == 1
    assert len(result.blocked_task_ids) == 2

    root = manager.get_goal(next(iter(manager.goals)))
    assert root is not None
    ready = manager.ready_tasks(root.goal_id)
    assert len(ready) == 1
    ready[0].mark_ready()
    ready[0].mark_running()
    ready[0].complete("ok")
    assert len(manager.ready_tasks(root.goal_id)) == 1
    assert manager.ready_tasks(root.goal_id)[0].status == TaskStatus.PENDING


def test_6p9_observation_feedback_recovery_is_bounded():
    brain = AutonomousWorkBrain()
    goal = AgentGoal("recover once", "execute", success_criteria=("verified",))
    calls = {"count": 0}

    def execute(step):
        calls["count"] += 1
        if step.title == "Perform required work" and calls["count"] == 2:
            raise RuntimeError("transient observation failure")
        return "verified-output"

    result = brain.run(
        goal,
        execute_step=execute,
        verify_step=lambda step, output: output == "verified-output",
        max_steps=10,
    )

    assert result.success
    assert result.verification_status == "VERIFIED"
    assert result.attempts == 4
    assert result.metadata["controlled_until_done"] is True


def test_6p10_completion_requires_final_verification():
    brain = AutonomousWorkBrain()
    goal = AgentGoal("must not falsely complete", "execute", success_criteria=("verified",))

    rejected = brain.run(
        goal,
        execute_step=lambda step: "bad-output",
        verify_step=lambda step, output: False,
        max_steps=1,
    )
    assert not rejected.success
    assert rejected.status == "FAILED"
    assert rejected.verification_status in {"FAILED", "NOT_VERIFIED"}

    accepted = brain.run(
        goal,
        execute_step=lambda step: "good-output",
        verify_step=lambda step, output: output == "good-output",
    )
    assert accepted.success
    assert accepted.status == "COMPLETED"
    assert accepted.verification_status == "VERIFIED"
    assert accepted.metadata["final_task_state_verified"] is True


def test_6p11_end_to_end_real_tool_boundary():
    brain = AutonomousWorkBrain()
    goal = AgentGoal(
        "read and verify a local project file",
        "execute",
        success_criteria=("tool result is allowed and verified",),
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
    assert result.status == "COMPLETED"
    assert result.verification_status == "VERIFIED"


def test_6p_security_boundary_is_non_escalating():
    brain = AutonomousWorkBrain()
    assert brain.grants_permission() is False
    assert brain.modifies_constitution() is False
    assert brain.jobs.grants_permission() is False
    assert brain.checkpoints.grants_permission() is False


def test_6p12_final_regression_contract():
    goal, plan = _plan()
    assert goal.authority_context == "user"
    assert len(plan.goals) == 3
    assert plan.goals[1].dependencies == (plan.goals[0].goal_id,)
    assert plan.goals[2].dependencies == (plan.goals[1].goal_id,)

    brain = AutonomousWorkBrain()
    result = brain.run(
        goal,
        execute_step=lambda step: {"step": step.title, "verified": True},
        verify_step=lambda step, output: output["verified"] is True,
    )
    assert result.success
    assert result.verification_status == "VERIFIED"
    assert result.metadata["controlled_until_done"] is True
    assert result.metadata["final_task_state_verified"] is True
