from core.agent_decomposition import (
    DecomposedGoal,
    GoalDecompositionEngine,
)
from core.agent_goal import AgentGoal
from core.agent_planning import (
    AgentPlan,
    DynamicPlanningEngine,
    ReplanningResult,
)


def main() -> None:
    source_goal = AgentGoal(
        objective="Research and verify a technical topic.",
        intent="research",
        priority="high",
    )

    decomposition = GoalDecompositionEngine()
    decomposition_result = decomposition.decompose(
        source_goal
    )

    assert decomposition_result.success is True
    assert len(decomposition_result.goals) == 3

    engine = DynamicPlanningEngine()

    plan = engine.create_plan(
        decomposition_result.goals
    )

    assert isinstance(plan, AgentPlan)
    assert plan.version == 1
    assert plan.reason == "initial_plan"
    assert len(plan.goals) == 3
    assert plan.plan_id

    first_goal = plan.goals[0]

    replanned = engine.replan(
        plan,
        completed_goal_ids=(first_goal.goal_id,),
        reason="First goal completed.",
    )

    assert isinstance(
        replanned,
        ReplanningResult,
    )
    assert replanned.success is True
    assert replanned.changed is True
    assert replanned.plan is not None
    assert replanned.plan.version == 2
    assert (
        replanned.previous_plan_id
        == plan.plan_id
    )
    assert len(replanned.plan.goals) == 2

    remaining_ids = {
        goal.goal_id
        for goal in replanned.plan.goals
    }

    assert first_goal.goal_id not in remaining_ids

    for goal in replanned.plan.goals:
        assert isinstance(
            goal,
            DecomposedGoal,
        )

    no_change = engine.replan(
        plan,
        reason="No completed goals reported.",
    )

    assert no_change.success is True
    assert no_change.changed is False
    assert no_change.plan is not None
    assert no_change.plan.version == 2
    assert len(no_change.plan.goals) == 3

    replacement = DecomposedGoal(
        title="Recover failed work",
        objective=source_goal.objective,
        intent="recover",
        success_criteria=("Recovery is completed.",),
        dependencies=(first_goal.goal_id,),
    )
    for trigger in (
        "task_failed",
        "new_evidence",
        "dependency_changed",
        "verification_failed",
        "objective_changed",
        "approval_unavailable",
    ):
        dynamic = engine.replan(
            plan,
            completed_goal_ids=(first_goal.goal_id,),
            replacement_goals=(replacement,),
            trigger=trigger,
            reason=trigger,
        )
        assert dynamic.success is True
        assert dynamic.changed is True
        assert dynamic.plan is not None
        assert dynamic.plan.version == 2
        assert dynamic.plan.reason == trigger
        assert replacement.goal_id in {
            goal.goal_id for goal in dynamic.plan.goals
        }

    invalid_trigger = engine.replan(
        plan,
        trigger="unsafe_trigger",
    )
    assert invalid_trigger.success is False
    assert invalid_trigger.plan is None

    bad_replacement = DecomposedGoal(
        title="Broken dependency",
        objective=source_goal.objective,
        intent="recover",
        success_criteria=("Recovery is completed.",),
        dependencies=("missing-goal",),
    )
    invalid_dependency = engine.replan(
        plan,
        replacement_goals=(bad_replacement,),
        trigger="dependency_changed",
    )
    assert invalid_dependency.success is False
    assert invalid_dependency.plan is None

    unknown = engine.replan(
        plan,
        completed_goal_ids=(
            "unknown-goal-id",
        ),
    )

    assert unknown.success is False
    assert unknown.plan is None
    assert unknown.changed is False

    completed = engine.replan(
        plan,
        completed_goal_ids=tuple(
            goal.goal_id
            for goal in plan.goals
        ),
    )

    assert completed.success is True
    assert completed.plan is None
    assert completed.changed is False

    try:
        engine.create_plan(())
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty goals must raise ValueError."
        )

    try:
        engine.create_plan(
            ("invalid-goal",)
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Invalid goal must raise TypeError."
        )

    try:
        engine.replan(
            "invalid-plan",
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Invalid plan must raise TypeError."
        )

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
            engine,
            method_name,
        )

    print(
        "SAHIBEX 6P-4 DYNAMIC PLANNING & "
        "REPLANNING TEST: PASS"
    )


if __name__ == "__main__":
    main()
