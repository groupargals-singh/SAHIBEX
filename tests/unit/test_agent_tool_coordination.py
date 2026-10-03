from core.agent_decomposition import (
    GoalDecompositionEngine,
)
from core.agent_goal import AgentGoal
from core.agent_planning import DynamicPlanningEngine
from core.agent_tool_coordination import (
    AgentToolCoordinator,
    AgentToolCoordinationResult,
)
from tools.discovery import ToolDiscovery
from tools.registry import ToolRegistry


def list_directory_handler(**kwargs):
    return {"entries": []}


def main() -> None:
    agent_goal = AgentGoal(
        objective="List files in a directory.",
        intent="read",
        priority="normal",
    )

    decomposition = GoalDecompositionEngine()

    decomposition_result = (
        decomposition.decompose(agent_goal)
    )

    assert decomposition_result.success is True
    assert len(decomposition_result.goals) == 3

    planner = DynamicPlanningEngine()

    plan = planner.create_plan(
        decomposition_result.goals
    )

    registry = ToolRegistry()

    registry.register(
        name="list_directory",
        description=(
            "List files and directories in a path."
        ),
        handler=list_directory_handler,
        read_only=True,
        requires_confirmation=False,
    )

    discovery = ToolDiscovery(registry)

    coordinator = AgentToolCoordinator(
        discovery
    )

    result = coordinator.coordinate(
        plan,
    )

    assert isinstance(
        result,
        AgentToolCoordinationResult,
    )

    assert result.success is True
    assert result.plan_id == plan.plan_id
    assert len(result.assignments) == 3

    for assignment in result.assignments:
        assert (
            assignment.tool
            == "list_directory"
        )

        assert (
            assignment.discovery_query.strip()
        )

        assert (
            "6K ToolDiscovery"
            in assignment.reason
        )

    forbidden_methods = (
        "execute",
        "execute_tool",
        "run_command",
        "grant_permission",
        "modify_constitution",
        "network_access",
    )

    for method_name in forbidden_methods:
        assert not hasattr(
            coordinator,
            method_name,
        )

    assert (
        coordinator.discovery
        is discovery
    )

    print(
        "SAHIBEX 6P-7 TOOL SELECTION "
        "AND EXECUTION COORDINATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
