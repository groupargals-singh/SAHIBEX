from core.agent_decomposition import DecomposedGoal
from core.agent_planning import AgentPlan, DynamicPlanningEngine


def goal(name: str, dependencies: tuple[str, ...] = ()) -> DecomposedGoal:
    return DecomposedGoal(
        title=name,
        objective=f"Complete {name}",
        intent="test",
        success_criteria=(f"{name} is complete",),
        dependencies=dependencies,
        goal_id=name,
    )


def test_completed_dependency_is_removed_from_remaining_plan():
    first = goal("first")
    second = goal("second", ("first",))
    plan = AgentPlan(goals=(first, second))

    result = DynamicPlanningEngine().replan(
        plan,
        completed_goal_ids=("first",),
    )

    assert result.success is True
    assert result.plan is not None
    assert [item.goal_id for item in result.plan.goals] == ["second"]
    assert result.plan.goals[0].dependencies == ()


def test_replacement_can_depend_on_a_completed_goal():
    first = goal("first")
    second = goal("second", ("first",))
    replacement = goal("recovery", ("first",))
    plan = AgentPlan(goals=(first, second))

    result = DynamicPlanningEngine().replan(
        plan,
        completed_goal_ids=("first",),
        replacement_goals=(replacement,),
        trigger="task_failed",
    )

    assert result.success is True
    assert result.plan is not None
    assert result.plan.goals[-1].goal_id == "recovery"
    assert result.plan.goals[-1].dependencies == ()


def test_unknown_uncompleted_dependency_still_fails_closed():
    plan = AgentPlan(goals=(goal("first"),))
    replacement = goal("recovery", ("missing",))

    result = DynamicPlanningEngine().replan(
        plan,
        replacement_goals=(replacement,),
        trigger="dependency_changed",
    )

    assert result.success is False
    assert result.plan is None
    assert "Unknown dependency" in result.reason


def test_invalid_trigger_returns_a_failed_result_without_mutating_plan():
    plan = AgentPlan(goals=(goal("first"),))

    result = DynamicPlanningEngine().replan(
        plan,
        trigger="unsafe_trigger",
    )

    assert result.success is False
    assert result.plan is None
    assert result.changed is False
    assert plan.version == 1
