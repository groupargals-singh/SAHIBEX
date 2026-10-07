from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


PRIORITY_VERSION = "P1-36-1"


class PriorityLevel(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class PriorityInput:
    urgency: float
    risk: float
    goal_relevance: float
    importance: float
    consequence: float
    user_priority: float
    input_id: str


@dataclass(frozen=True)
class PriorityResult:
    input_id: str
    priority_score: float
    level: PriorityLevel
    reason: str
    result_id: str = field(default_factory=lambda: str(uuid4()))
    version: str = PRIORITY_VERSION

    @property
    def is_high_priority(self) -> bool:
        return self.level in (
            PriorityLevel.HIGH,
            PriorityLevel.CRITICAL,
        )


class PriorityEngine:
    """
    Cognitive priority assessment.

    This engine:
    - calculates priority only
    - does not schedule tasks
    - does not execute actions
    - does not grant permission
    - does not modify tasks
    - does not override Human Authority
    """

    URGENCY_WEIGHT = 0.20
    RISK_WEIGHT = 0.20
    GOAL_WEIGHT = 0.20
    IMPORTANCE_WEIGHT = 0.15
    CONSEQUENCE_WEIGHT = 0.15
    USER_PRIORITY_WEIGHT = 0.10

    def assess(self, priority_input: PriorityInput) -> PriorityResult:
        self._validate(priority_input)

        score = (
            priority_input.urgency * self.URGENCY_WEIGHT
            + priority_input.risk * self.RISK_WEIGHT
            + priority_input.goal_relevance * self.GOAL_WEIGHT
            + priority_input.importance * self.IMPORTANCE_WEIGHT
            + priority_input.consequence * self.CONSEQUENCE_WEIGHT
            + priority_input.user_priority * self.USER_PRIORITY_WEIGHT
        )

        score = round(max(0.0, min(1.0, score)), 4)

        level = self._level(score)

        reason = (
            f"priority={level.value}; "
            f"score={score:.4f}"
        )

        return PriorityResult(
            input_id=priority_input.input_id.strip(),
            priority_score=score,
            level=level,
            reason=reason,
        )

    @staticmethod
    def _validate(priority_input: PriorityInput) -> None:
        if not isinstance(priority_input, PriorityInput):
            raise TypeError("priority_input must be PriorityInput")

        if not isinstance(priority_input.input_id, str):
            raise TypeError("input_id must be a string")

        if not priority_input.input_id.strip():
            raise ValueError("input_id cannot be empty")

        values = (
            priority_input.urgency,
            priority_input.risk,
            priority_input.goal_relevance,
            priority_input.importance,
            priority_input.consequence,
            priority_input.user_priority,
        )

        for value in values:
            if not isinstance(value, (int, float)):
                raise TypeError("priority signals must be numeric")

            if isinstance(value, bool):
                raise TypeError("priority signals cannot be bool")

            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(
                    "priority signals must be between 0 and 1"
                )

    @staticmethod
    def _level(score: float) -> PriorityLevel:
        if score >= 0.80:
            return PriorityLevel.CRITICAL

        if score >= 0.60:
            return PriorityLevel.HIGH

        if score >= 0.35:
            return PriorityLevel.NORMAL

        return PriorityLevel.LOW

    @staticmethod
    def schedules_tasks() -> bool:
        return False

    @staticmethod
    def executes_actions() -> bool:
        return False

    @staticmethod
    def grants_permission() -> bool:
        return False

    @staticmethod
    def modifies_tasks() -> bool:
        return False

    @staticmethod
    def overrides_human_authority() -> bool:
        return False
