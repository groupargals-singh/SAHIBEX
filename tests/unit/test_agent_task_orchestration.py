from core.agent_decomposition import (
    GoalDecompositionEngine,
)
from core.agent_goal import AgentGoal
from core.agent_planning import DynamicPlanningEngine
from core.agent_task_orchestration import (
    AgentTaskOrchestrator,
    AgentTaskOrchestrationResult,
)
from core.orchestrator.task_state import (
    TaskManager,
    TaskPriority,
)


def main() -> None:
    agent_goal = AgentGoal(
        objective="Research and verify a technical topic.",
        intent="research",
        priority="normal",
    )

    decomposition = GoalDecompositionEngine()

    decomposition_result = (
        decomposition.decompose(agent_goal)
    )

    assert decomposition_result.success is True

    planner = DynamicPlanningEngine()

    plan = planner.create_plan(
        decomposition_result.goals
    )

    manager = TaskManager()

    orchestrator = AgentTaskOrchestrator(
        manager
    )

    result = orchestrator.create_tasks(plan)

    assert isinstance(
        result,
        AgentTaskOrchestrationResult,
    )

    assert result.success is True
    assert result.plan_id == plan.plan_id

    assert len(result.task_ids) == 3
    assert len(result.ready_task_ids) == 1
    assert len(result.blocked_task_ids) == 2

    assert len(manager.goals) == 1
    assert len(manager.tasks) == 3

    goal_id = next(iter(manager.goals))

    goal = manager.get_goal(goal_id)

    assert goal is not None
    assert len(goal.tasks) == 3

    tasks = list(goal.tasks)

    for task in tasks:
        assert task.task_id in result.task_ids
        assert task.priority == TaskPriority.NORMAL

    ready_ids = {
        task.task_id
        for task in tasks
        if not task.dependencies
    }

    blocked_ids = {
        task.task_id
        for task in tasks
        if task.dependencies
    }

    assert ready_ids == set(
        result.ready_task_ids
    )

    assert blocked_ids == set(
        result.blocked_task_ids
    )

    assert len(blocked_ids) == 2

    first_task = tasks[0]
    second_task = tasks[1]
    third_task = tasks[2]

    assert first_task.dependencies == []

    assert second_task.dependencies == [
        first_task.task_id
    ]

    assert third_task.dependencies == [
        second_task.task_id
    ]

    forbidden_methods = (
        "execute",
        "execute_tool",
        "grant_permission",
        "modify_constitution",
        "run_command",
        "network_access",
    )

    for method_name in forbidden_methods:
        assert not hasattr(
            orchestrator,
            method_name,
        )

    print(
        "SAHIBEX 6P-5 TASK DEPENDENCY "
        "ORCHESTRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
