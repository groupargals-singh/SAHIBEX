from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from core.agent_planning import AgentPlan
from tools.discovery import ToolCandidate, ToolDiscovery


@dataclass(frozen=True)
class AgentToolAssignment:
    goal_id: str
    discovery_query: str
    tool: str
    reason: str


@dataclass(frozen=True)
class AgentToolCoordinationResult:
    success: bool
    plan_id: str
    assignments: tuple[AgentToolAssignment, ...]
    coordination_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    error: str | None = None


class AgentToolCoordinator:
    """
    Coordinates AgentPlan goals with the existing 6K tool
    discovery layer.

    This layer:
    - converts agent goals into tool-discovery queries
    - selects the deterministic best registered tool
    - records the selected tool for downstream execution

    It does not:
    - execute tools directly
    - grant permissions
    - bypass SafeToolExecutor
    - bypass ToolPermissionGateway
    - modify the Constitution
    - modify registered tools
    """

    def __init__(
        self,
        discovery: ToolDiscovery,
    ) -> None:
        if not isinstance(discovery, ToolDiscovery):
            raise TypeError(
                "discovery must be ToolDiscovery."
            )

        self.discovery = discovery

    def coordinate(
        self,
        plan: AgentPlan,
    ) -> AgentToolCoordinationResult:
        if not isinstance(plan, AgentPlan):
            raise TypeError(
                "plan must be AgentPlan."
            )

        assignments: list[AgentToolAssignment] = []

        for goal in plan.goals:
            query = self._build_discovery_query(
                goal.title,
                goal.objective,
            )

            candidate: ToolCandidate | None = (
                self.discovery.select(query)
            )

            if candidate is None:
                return AgentToolCoordinationResult(
                    success=False,
                    plan_id=plan.plan_id,
                    assignments=tuple(assignments),
                    error=(
                        "No registered tool matches "
                        f"agent goal: {goal.title}"
                    ),
                )

            assignments.append(
                AgentToolAssignment(
                    goal_id=goal.goal_id,
                    discovery_query=query,
                    tool=candidate.name,
                    reason=(
                        "Selected by the existing deterministic "
                        "6K ToolDiscovery layer."
                    ),
                )
            )

        return AgentToolCoordinationResult(
            success=True,
            plan_id=plan.plan_id,
            assignments=tuple(assignments),
        )

    @staticmethod
    def _build_discovery_query(
        title: str,
        objective: str,
    ) -> str:
        title = title.strip()
        objective = objective.strip()

        if title and objective:
            return f"{title} {objective}"

        if title:
            return title

        return objective
