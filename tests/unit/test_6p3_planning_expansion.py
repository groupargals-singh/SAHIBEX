from core.agent_goal import AgentGoal
from core.agent_decomposition_expansion import GoalDecompositionExpansion
from core.agent_planning_expansion import AgentPlanningExpansion


def test_planning_expansion():
    goal = AgentGoal(
        objective="Research and verify AI security",
        intent="research",
        priority="high",
        constraints=("trusted sources",),
        success_criteria=("verified answer",),
    )
    decomposition = GoalDecompositionExpansion().decompose(goal)
    result = AgentPlanningExpansion().build_plan(decomposition.tasks)
    assert result.success
    assert len(result.tasks) == 3
    assert [task.sequence for task in result.tasks] == [1, 2, 3]
    assert result.tasks[1].dependencies == (result.tasks[0].task_id,)
    assert result.tasks[2].dependencies == (result.tasks[1].task_id,)
    assert all(task.constraints == goal.constraints for task in result.tasks)
    assert all(task.success_criteria == goal.success_criteria for task in result.tasks)
    assert all(task.verification_required for task in result.tasks)
    assert AgentPlanningExpansion.validate(result) == ()
    assert not result.grants_permission
    assert not result.executes_protected_actions
