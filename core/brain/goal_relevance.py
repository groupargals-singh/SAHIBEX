from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class GoalRelevanceLevel(str, Enum):
    IRRELEVANT = "irrelevant"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class GoalRelevanceInput:
    content: str
    goal: str
    semantic_relevance: float
    goal_dependency: float
    expected_contribution: float
    goal_priority: float

    input_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        for name in ("content", "goal"):
            value = getattr(self, name)

            if not isinstance(value, str):
                raise TypeError(f"{name} must be str.")

            if not value.strip():
                raise ValueError(
                    f"{name} must not be empty."
                )

        for name in (
            "semantic_relevance",
            "goal_dependency",
            "expected_contribution",
            "goal_priority",
        ):
            value = getattr(self, name)

            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"{name} must be numeric."
                )

            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(
                    f"{name} must be between 0.0 and 1.0."
                )

        if not isinstance(self.input_id, str):
            raise TypeError("input_id must be str.")

        if not self.input_id.strip():
            raise ValueError(
                "input_id must not be empty."
            )


@dataclass(frozen=True)
class GoalRelevanceResult:
    level: GoalRelevanceLevel
    relevance_score: float
    relevant: bool
    input_id: str
    goal: str
    reason: str

    result_id: str = field(
        default_factory=lambda: str(uuid4())
    )


class GoalRelevanceEngine:
    """
    Canonical SAHIBEX Goal-Relevance Engine.

    Determines how strongly an input contributes to
    the active goal.

    This layer does NOT:
    - execute actions
    - grant permissions
    - approve protected actions
    - access credentials
    - modify the Constitution
    - override Human Authority
    """

    VERSION = "1.0"

    SEMANTIC_WEIGHT = 0.35
    DEPENDENCY_WEIGHT = 0.25
    CONTRIBUTION_WEIGHT = 0.25
    PRIORITY_WEIGHT = 0.15

    CRITICAL_THRESHOLD = 0.85
    HIGH_THRESHOLD = 0.65
    MEDIUM_THRESHOLD = 0.40
    LOW_THRESHOLD = 0.15

    def evaluate(
        self,
        relevance_input: GoalRelevanceInput,
    ) -> GoalRelevanceResult:
        if not isinstance(
            relevance_input,
            GoalRelevanceInput,
        ):
            raise TypeError(
                "relevance_input must be GoalRelevanceInput."
            )

        score = (
            relevance_input.semantic_relevance
            * self.SEMANTIC_WEIGHT
            + relevance_input.goal_dependency
            * self.DEPENDENCY_WEIGHT
            + relevance_input.expected_contribution
            * self.CONTRIBUTION_WEIGHT
            + relevance_input.goal_priority
            * self.PRIORITY_WEIGHT
        )

        score = round(score, 6)

        if score >= self.CRITICAL_THRESHOLD:
            level = GoalRelevanceLevel.CRITICAL
            relevant = True
            reason = (
                "Input is critically relevant to the "
                "active goal."
            )

        elif score >= self.HIGH_THRESHOLD:
            level = GoalRelevanceLevel.HIGH
            relevant = True
            reason = (
                "Input is highly relevant to the "
                "active goal."
            )

        elif score >= self.MEDIUM_THRESHOLD:
            level = GoalRelevanceLevel.MEDIUM
            relevant = True
            reason = (
                "Input has meaningful relevance to the "
                "active goal."
            )

        elif score >= self.LOW_THRESHOLD:
            level = GoalRelevanceLevel.LOW
            relevant = False
            reason = (
                "Input has weak relevance to the "
                "active goal."
            )

        else:
            level = GoalRelevanceLevel.IRRELEVANT
            relevant = False
            reason = (
                "Input is not relevant to the "
                "active goal."
            )

        return GoalRelevanceResult(
            level=level,
            relevance_score=score,
            relevant=relevant,
            input_id=relevance_input.input_id,
            goal=relevance_input.goal,
            reason=reason,
        )
