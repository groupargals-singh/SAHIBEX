from datetime import datetime, timezone

from core.agent_goal import AgentGoal


def main() -> None:
    goal = AgentGoal(
        objective="Research and explain a technical topic.",
        intent="research",
        priority="high",
        constraints=(
            "Do not modify system files.",
            "Use verified information.",
        ),
        success_criteria=(
            "Produce a verified explanation.",
            "Preserve source traceability.",
        ),
        authority_context="user",
        metadata={
            "test": True,
            "phase": "6P-1",
        },
    )

    assert goal.objective == (
        "Research and explain a technical topic."
    )
    assert goal.intent == "research"
    assert goal.priority == "high"

    assert len(goal.constraints) == 2
    assert len(goal.success_criteria) == 2

    assert goal.authority_context == "user"
    assert goal.goal_id
    assert isinstance(goal.created_at, datetime)
    assert goal.created_at.tzinfo == timezone.utc
    assert goal.metadata["phase"] == "6P-1"

    try:
        AgentGoal(
            objective="",
            intent="research",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty objective must raise ValueError."
        )

    try:
        AgentGoal(
            objective="Valid objective",
            intent="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty intent must raise ValueError."
        )

    try:
        AgentGoal(
            objective="Valid objective",
            intent="research",
            constraints=("valid", ""),
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty constraint must raise ValueError."
        )

    try:
        AgentGoal(
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

    print(
        "SAHIBEX 6P-1 AGENT GOAL CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
