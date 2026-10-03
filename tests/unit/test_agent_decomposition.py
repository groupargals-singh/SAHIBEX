from core.agent_decomposition import (
    DecomposedGoal,
    GoalDecompositionEngine,
    GoalDecompositionResult,
)
from core.agent_goal import AgentGoal


def main() -> None:
    goal = AgentGoal(
        objective="Research a technical topic and explain it.",
        intent="research",
        priority="high",
        constraints=(
            "Use verified information.",
        ),
        success_criteria=(
            "Produce a correct explanation.",
        ),
    )

    engine = GoalDecompositionEngine()

    result = engine.decompose(goal)

    assert isinstance(
        result,
        GoalDecompositionResult,
    )

    assert result.success is True
    assert result.objective == goal.objective
    assert result.error is None

    assert len(result.goals) == 3

    for item in result.goals:
        assert isinstance(
            item,
            DecomposedGoal,
        )
        assert item.title
        assert item.objective == goal.objective
        assert item.intent
        assert item.success_criteria
        assert item.goal_id

    understand = result.goals[0]
    work = result.goals[1]
    verify = result.goals[2]

    assert understand.title == "Understand objective"
    assert work.title == "Perform required work"
    assert verify.title == "Verify result"

    assert understand.dependencies == ()
    assert work.dependencies == (
        understand.goal_id,
    )
    assert verify.dependencies == (
        work.goal_id,
    )

    assert verify.intent == "verify"

    try:
        engine.decompose("invalid-goal")
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Invalid goal type must raise TypeError."
        )

    try:
        DecomposedGoal(
            title="",
            objective="Valid objective",
            intent="research",
            success_criteria=("valid",),
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty title must raise ValueError."
        )

    try:
        DecomposedGoal(
            title="Valid",
            objective="Valid objective",
            intent="research",
            success_criteria=("valid", ""),
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty success criterion must raise ValueError."
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
        "SAHIBEX 6P-3 GOAL DECOMPOSITION TEST: PASS"
    )


if __name__ == "__main__":
    main()
