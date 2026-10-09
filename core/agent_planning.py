from __future__ import annotations

from dataclasses import dataclass, field, replace
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


REPLAN_TRIGGERS = frozenset(
    {
        "task_failed",
        "new_evidence",
        "dependency_changed",
        "verification_failed",
        "objective_changed",
        "approval_unavailable",
        "replan_requested",
    }
)


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
        replacement_goals: tuple[DecomposedGoal, ...] = (),
        trigger: str = "replan_requested",
        reason: str = "replan_requested",
    ) -> ReplanningResult:
        """Create a new plan version without gaining execution authority.

        A replan may be triggered by task failure, new evidence, dependency
        changes, verification failure, objective changes, or unavailable
        approval. Replacement goals are supplied by an upstream planner;
        this engine only validates and composes them.
        """
        if not isinstance(plan, AgentPlan):
            raise TypeError("plan must be AgentPlan.")

        if not isinstance(completed_goal_ids, tuple):
            raise TypeError("completed_goal_ids must be tuple.")
        for goal_id in completed_goal_ids:
            if not isinstance(goal_id, str):
                raise TypeError("every completed goal ID must be str.")
            if not goal_id.strip():
                raise ValueError("completed goal IDs must not be empty.")

        if not isinstance(replacement_goals, tuple):
            raise TypeError("replacement_goals must be tuple.")
        for goal in replacement_goals:
            if not isinstance(goal, DecomposedGoal):
                raise TypeError(
                    "every replacement goal must be DecomposedGoal."
                )

        if not isinstance(trigger, str):
            raise TypeError("trigger must be str.")
        if trigger not in REPLAN_TRIGGERS:
            return ReplanningResult(
                success=False,
                previous_plan_id=plan.plan_id,
                plan=None,
                changed=False,
                reason="Unsupported replan trigger: " + trigger,
            )

        if not isinstance(reason, str):
            raise TypeError("reason must be str.")
        if not reason.strip():
            raise ValueError("reason must not be empty.")

        completed = set(completed_goal_ids)
        known_ids = {goal.goal_id for goal in plan.goals}
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

        # Completed dependencies are satisfied. Remove them from the
        # remaining plan instead of treating them as missing dependencies.
        remaining_goals = tuple(
            replace(
                goal,
                dependencies=tuple(
                    dependency
                    for dependency in goal.dependencies
                    if dependency not in completed
                ),
            )
            for goal in plan.goals
            if goal.goal_id not in completed
        )
        normalized_replacements = tuple(
            replace(
                goal,
                dependencies=tuple(
                    dependency
                    for dependency in goal.dependencies
                    if dependency not in completed
                ),
            )
            for goal in replacement_goals
        )
        replacement_ids = {
            goal.goal_id for goal in normalized_replacements
        }
        if len(replacement_ids) != len(replacement_goals):
            return ReplanningResult(
                success=False,
                previous_plan_id=plan.plan_id,
                plan=None,
                changed=False,
                reason="Replacement goals contain duplicate IDs.",
            )

        combined_goals = remaining_goals + normalized_replacements
        combined_ids = {goal.goal_id for goal in combined_goals}
        unknown_dependencies = sorted(
            {
                dependency
                for goal in combined_goals
                for dependency in goal.dependencies
                if dependency not in combined_ids
            }
        )
        if unknown_dependencies:
            return ReplanningResult(
                success=False,
                previous_plan_id=plan.plan_id,
                plan=None,
                changed=False,
                reason=(
                    "Unknown dependency after replan: "
                    + unknown_dependencies[0]
                ),
            )

        if not combined_goals:
            return ReplanningResult(
                success=True,
                previous_plan_id=plan.plan_id,
                plan=None,
                changed=False,
                reason="All plan goals are completed.",
            )

        changed = bool(completed or replacement_goals)

        new_plan = AgentPlan(
            goals=combined_goals,
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
