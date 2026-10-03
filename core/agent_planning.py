from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from core.agent_decomposition import DecomposedGoal


@dataclass(frozen=True)
class AgentPlan:
    goals: tuple[DecomposedGoal, ...]
    version: int = 1
    reason: str = "initial_plan"
    plan_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.goals, tuple):
            raise TypeError("goals must be tuple.")

        for goal in self.goals:
            if not isinstance(goal, DecomposedGoal):
                raise TypeError(
                    "every plan goal must be DecomposedGoal."
                )

        if not isinstance(self.version, int):
            raise TypeError("version must be int.")
        if self.version < 1:
            raise ValueError("version must be >= 1.")

        if not isinstance(self.reason, str):
            raise TypeError("reason must be str.")
        if not self.reason.strip():
            raise ValueError("reason must not be empty.")

        if not isinstance(self.plan_id, str):
            raise TypeError("plan_id must be str.")
        if not self.plan_id.strip():
            raise ValueError("plan_id must not be empty.")


@dataclass(frozen=True)
class ReplanningResult:
    success: bool
    previous_plan_id: str
    plan: AgentPlan | None
    changed: bool
    reason: str
    replanning_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool.")

        if not isinstance(self.previous_plan_id, str):
            raise TypeError(
                "previous_plan_id must be str."
            )
        if not self.previous_plan_id.strip():
            raise ValueError(
                "previous_plan_id must not be empty."
            )

        if self.plan is not None and not isinstance(
            self.plan,
            AgentPlan,
        ):
            raise TypeError(
                "plan must be AgentPlan or None."
            )

        if not isinstance(self.changed, bool):
            raise TypeError("changed must be bool.")

        if not isinstance(self.reason, str):
            raise TypeError("reason must be str.")
        if not self.reason.strip():
            raise ValueError("reason must not be empty.")

        if not isinstance(
            self.replanning_id,
            str,
        ):
            raise TypeError(
                "replanning_id must be str."
            )


class DynamicPlanningEngine:
    """
    Contract-level dynamic planning and replanning.

    This layer creates versioned plans and can replan around
    completed goals.

    It does not:

    - execute goals
    - execute tools
    - grant permissions
    - perform network access
    - modify the Constitution
    """

    def create_plan(
        self,
        goals: tuple[DecomposedGoal, ...],
    ) -> AgentPlan:
        if not isinstance(goals, tuple):
            raise TypeError("goals must be tuple.")

        if not goals:
            raise ValueError(
                "goals must not be empty."
            )

        for goal in goals:
            if not isinstance(goal, DecomposedGoal):
                raise TypeError(
                    "every goal must be DecomposedGoal."
                )

        return AgentPlan(
            goals=goals,
            version=1,
            reason="initial_plan",
        )

    def replan(
        self,
        plan: AgentPlan,
        *,
        completed_goal_ids: tuple[str, ...] = (),
        reason: str = "replan_requested",
    ) -> ReplanningResult:
        if not isinstance(plan, AgentPlan):
            raise TypeError(
                "plan must be AgentPlan."
            )

        if not isinstance(
            completed_goal_ids,
            tuple,
        ):
            raise TypeError(
                "completed_goal_ids must be tuple."
            )

        for goal_id in completed_goal_ids:
            if not isinstance(goal_id, str):
                raise TypeError(
                    "every completed goal ID must be str."
                )
            if not goal_id.strip():
                raise ValueError(
                    "completed goal IDs must not be empty."
                )

        if not isinstance(reason, str):
            raise TypeError("reason must be str.")
        if not reason.strip():
            raise ValueError(
                "reason must not be empty."
            )

        completed = set(completed_goal_ids)

        known_ids = {
            goal.goal_id
            for goal in plan.goals
        }

        unknown_ids = completed - known_ids

        if unknown_ids:
            return ReplanningResult(
                success=False,
                previous_plan_id=plan.plan_id,
                plan=None,
                changed=False,
                reason=(
                    "Unknown completed goal ID: "
                    + sorted(unknown_ids)[0]
                ),
            )

        remaining_goals = tuple(
            goal
            for goal in plan.goals
            if goal.goal_id not in completed
        )

        if not remaining_goals:
            return ReplanningResult(
                success=True,
                previous_plan_id=plan.plan_id,
                plan=None,
                changed=False,
                reason="All plan goals are completed.",
            )

        changed = bool(completed)

        new_plan = AgentPlan(
            goals=remaining_goals,
            version=plan.version + 1,
            reason=reason,
        )

        return ReplanningResult(
            success=True,
            previous_plan_id=plan.plan_id,
            plan=new_plan,
            changed=changed,
            reason=reason,
        )
