from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from core.agent_goal import AgentGoal


@dataclass(frozen=True)
class DecomposedGoal:
    title: str
    objective: str
    intent: str
    success_criteria: tuple[str, ...]
    dependencies: tuple[str, ...] = ()
    goal_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.title, str):
            raise TypeError("title must be str.")
        if not self.title.strip():
            raise ValueError("title must not be empty.")

        if not isinstance(self.objective, str):
            raise TypeError("objective must be str.")
        if not self.objective.strip():
            raise ValueError("objective must not be empty.")

        if not isinstance(self.intent, str):
            raise TypeError("intent must be str.")
        if not self.intent.strip():
            raise ValueError("intent must not be empty.")

        if not isinstance(
            self.success_criteria,
            tuple,
        ):
            raise TypeError(
                "success_criteria must be tuple."
            )

        for criterion in self.success_criteria:
            if not isinstance(criterion, str):
                raise TypeError(
                    "every success criterion must be str."
                )
            if not criterion.strip():
                raise ValueError(
                    "success criteria cannot contain "
                    "empty strings."
                )

        if not isinstance(
            self.dependencies,
            tuple,
        ):
            raise TypeError(
                "dependencies must be tuple."
            )

        for dependency in self.dependencies:
            if not isinstance(dependency, str):
                raise TypeError(
                    "every dependency must be str."
                )
            if not dependency.strip():
                raise ValueError(
                    "dependencies cannot contain "
                    "empty strings."
                )

        if not isinstance(self.goal_id, str):
            raise TypeError("goal_id must be str.")
        if not self.goal_id.strip():
            raise ValueError("goal_id must not be empty.")


@dataclass(frozen=True)
class GoalDecompositionResult:
    success: bool
    objective: str
    goals: tuple[DecomposedGoal, ...]
    decomposition_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    error: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool.")

        if not isinstance(self.objective, str):
            raise TypeError("objective must be str.")
        if not self.objective.strip():
            raise ValueError(
                "objective must not be empty."
            )

        if not isinstance(self.goals, tuple):
            raise TypeError("goals must be tuple.")

        for goal in self.goals:
            if not isinstance(
                goal,
                DecomposedGoal,
            ):
                raise TypeError(
                    "every goal must be DecomposedGoal."
                )

        if not isinstance(
            self.decomposition_id,
            str,
        ):
            raise TypeError(
                "decomposition_id must be str."
            )
        if not self.decomposition_id.strip():
            raise ValueError(
                "decomposition_id must not be empty."
            )

        if self.error is not None and not isinstance(
            self.error,
            str,
        ):
            raise TypeError(
                "error must be str or None."
            )


class GoalDecompositionEngine:
    """
    Deterministic goal decomposition contract.

    This layer decomposes an objective but does not:

    - execute tasks
    - execute tools
    - grant permissions
    - perform network access
    - modify the Constitution
    """

    def decompose(
        self,
        goal: AgentGoal,
    ) -> GoalDecompositionResult:
        if not isinstance(goal, AgentGoal):
            raise TypeError(
                "goal must be AgentGoal."
            )

        objective = goal.objective.strip()

        first = DecomposedGoal(
            title="Understand objective",
            objective=objective,
            intent=goal.intent.strip().lower(),
            success_criteria=(
                "Objective is clearly understood.",
            ),
        )

        second = DecomposedGoal(
            title="Perform required work",
            objective=objective,
            intent=goal.intent.strip().lower(),
            success_criteria=(
                "Required work is completed.",
            ),
            dependencies=(first.goal_id,),
        )

        third = DecomposedGoal(
            title="Verify result",
            objective=objective,
            intent="verify",
            success_criteria=(
                "Result satisfies the objective.",
            ),
            dependencies=(second.goal_id,),
        )

        return GoalDecompositionResult(
            success=True,
            objective=objective,
            goals=(
                first,
                second,
                third,
            ),
        )
