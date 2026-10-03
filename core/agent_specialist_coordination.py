from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from core.agent_planning import AgentPlan
from core.brain.brain_registry import BrainRegistry
from core.brain.intelligence import BrainIntelligence
from core.brain.specialist_brain import BrainCapability


@dataclass(frozen=True)
class SpecialistAssignment:
    goal_id: str
    brain_id: str
    capability: BrainCapability
    reason: str


@dataclass(frozen=True)
class AgentSpecialistCoordinationResult:
    success: bool
    plan_id: str
    assignments: tuple[SpecialistAssignment, ...]
    coordination_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    error: str | None = None


class AgentSpecialistCoordinator:
    """
    Coordinates AgentPlan goals with available specialist brains.

    This layer:
    - maps goal intent to specialist capability
    - asks BrainIntelligence to select a specialist
    - records deterministic specialist assignments

    It does not:
    - execute specialist work
    - execute tools
    - grant permissions
    - modify the Constitution
    - modify specialist identity or capabilities
    - directly change specialist workload
    """

    _INTENT_CAPABILITY_MAP: dict[str, BrainCapability] = {
        "think": BrainCapability.THINK,
        "research": BrainCapability.RESEARCH,
        "analyze": BrainCapability.ANALYZE,
        "code": BrainCapability.CODE,
        "create": BrainCapability.CREATE,
        "verify": BrainCapability.VERIFY,
        "plan": BrainCapability.PLAN,
        "read": BrainCapability.READ,
    }

    def __init__(
        self,
        registry: BrainRegistry,
    ) -> None:
        if not isinstance(registry, BrainRegistry):
            raise TypeError(
                "registry must be BrainRegistry."
            )

        self.registry = registry
        self.intelligence = BrainIntelligence(registry)

    def coordinate(
        self,
        plan: AgentPlan,
        *,
        specialization: str | None = None,
    ) -> AgentSpecialistCoordinationResult:
        if not isinstance(plan, AgentPlan):
            raise TypeError(
                "plan must be AgentPlan."
            )

        if specialization is not None:
            if (
                not isinstance(specialization, str)
                or not specialization.strip()
            ):
                raise ValueError(
                    "specialization must be a non-empty string "
                    "when provided."
                )

        assignments: list[SpecialistAssignment] = []

        for goal in plan.goals:
            capability = self._capability_for_intent(
                goal.intent
            )

            if capability is None:
                return AgentSpecialistCoordinationResult(
                    success=False,
                    plan_id=plan.plan_id,
                    assignments=tuple(assignments),
                    error=(
                        "No specialist capability mapping "
                        f"exists for intent: {goal.intent}"
                    ),
                )

            selection = self.intelligence.select_brain(
                specialization=specialization,
                capability=capability,
            )

            if selection.selected_brain_id is None:
                return AgentSpecialistCoordinationResult(
                    success=False,
                    plan_id=plan.plan_id,
                    assignments=tuple(assignments),
                    error=selection.reason,
                )

            assignments.append(
                SpecialistAssignment(
                    goal_id=goal.goal_id,
                    brain_id=selection.selected_brain_id,
                    capability=capability,
                    reason=selection.reason,
                )
            )

        return AgentSpecialistCoordinationResult(
            success=True,
            plan_id=plan.plan_id,
            assignments=tuple(assignments),
        )

    @classmethod
    def _capability_for_intent(
        cls,
        intent: str,
    ) -> BrainCapability | None:
        normalized = intent.strip().lower()

        return cls._INTENT_CAPABILITY_MAP.get(
            normalized
        )
