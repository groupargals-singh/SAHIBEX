from core.agent_decomposition import (
    GoalDecompositionEngine,
)
from core.agent_goal import AgentGoal
from core.agent_planning import DynamicPlanningEngine
from core.agent_specialist_coordination import (
    AgentSpecialistCoordinator,
    AgentSpecialistCoordinationResult,
)
from core.brain.brain_registry import BrainRegistry
from core.brain.specialist_brain import (
    BrainCapability,
    BrainStatus,
    SpecialistBrain,
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
    assert len(decomposition_result.goals) == 3

    planner = DynamicPlanningEngine()

    plan = planner.create_plan(
        decomposition_result.goals
    )

    registry = BrainRegistry()

    research_brain = SpecialistBrain(
        name="Research Brain",
        description="Research specialist.",
        specialization="research",
        capabilities={
            BrainCapability.RESEARCH,
        },
        status=BrainStatus.READY,
    )

    verify_brain = SpecialistBrain(
        name="Verification Brain",
        description="Verification specialist.",
        specialization="verification",
        capabilities={
            BrainCapability.VERIFY,
        },
        status=BrainStatus.READY,
    )

    registry.register(research_brain)
    registry.register(verify_brain)

    coordinator = AgentSpecialistCoordinator(
        registry
    )

    research_plan = planner.create_plan(
        (
            decomposition_result.goals[0],
        )
    )

    result = coordinator.coordinate(
        research_plan,
        specialization="research",
    )

    assert isinstance(
        result,
        AgentSpecialistCoordinationResult,
    )

    assert result.success is True
    assert result.plan_id == research_plan.plan_id
    assert len(result.assignments) == 1

    assignment = result.assignments[0]

    assert (
        assignment.brain_id
        == research_brain.brain_id
    )

    assert (
        assignment.capability
        == BrainCapability.RESEARCH
    )

    full_result = coordinator.coordinate(
        plan,
    )

    assert full_result.success is True
    assert full_result.plan_id == plan.plan_id
    assert len(full_result.assignments) == 3

    assert (
        full_result.assignments[0].capability
        == BrainCapability.RESEARCH
    )

    assert (
        full_result.assignments[0].brain_id
        == research_brain.brain_id
    )

    assert (
        full_result.assignments[1].capability
        == BrainCapability.RESEARCH
    )

    assert (
        full_result.assignments[1].brain_id
        == research_brain.brain_id
    )

    assert (
        full_result.assignments[2].capability
        == BrainCapability.VERIFY
    )

    assert (
        full_result.assignments[2].brain_id
        == verify_brain.brain_id
    )

    assert (
        registry.get(
            research_brain.brain_id
        )
        is research_brain
    )

    assert (
        registry.get(
            verify_brain.brain_id
        )
        is verify_brain
    )

    assert (
        research_brain.status
        == BrainStatus.READY
    )

    assert (
        verify_brain.status
        == BrainStatus.READY
    )

    assert (
        research_brain.resource_state.active_tasks
        == 0
    )

    assert (
        verify_brain.resource_state.active_tasks
        == 0
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
            coordinator,
            method_name,
        )

    print(
        "SAHIBEX 6P-6 SPECIALIST BRAIN "
        "COORDINATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
