from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class RetentionLevel(str, Enum):
    RELEASE = "release"
    TEMPORARY = "temporary"
    RETAIN = "retain"


@dataclass(frozen=True)
class RetentionInput:
    content: str
    importance: float
    urgency: float
    risk: float
    goal_relevance: float
    priority: float

    input_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise TypeError("content must be str.")

        if not self.content.strip():
            raise ValueError(
                "content must not be empty."
            )

        for name in (
            "importance",
            "urgency",
            "risk",
            "goal_relevance",
            "priority",
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
class RetentionResult:
    level: RetentionLevel
    retention_score: float
    input_id: str
    reason: str
    result_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    @property
    def retained(self) -> bool:
        return self.level != RetentionLevel.RELEASE


class RetentionControlEngine:
    """
    SAHIBEX Retention Control Engine.

    Determines how strongly information should remain
    cognitively available.

    This engine does not:
    - modify persistent memory
    - delete memory
    - execute actions
    - grant permissions
    - access credentials
    - modify the Constitution
    """

    VERSION = "1.0"

    IMPORTANCE_WEIGHT = 0.30
    URGENCY_WEIGHT = 0.20
    RISK_WEIGHT = 0.20
    GOAL_WEIGHT = 0.20
    PRIORITY_WEIGHT = 0.10

    RETAIN_THRESHOLD = 0.70
    TEMPORARY_THRESHOLD = 0.35

    def evaluate(
        self,
        retention_input: RetentionInput,
    ) -> RetentionResult:
        if not isinstance(
            retention_input,
            RetentionInput,
        ):
            raise TypeError(
                "retention_input must be RetentionInput."
            )

        score = (
            retention_input.importance
            * self.IMPORTANCE_WEIGHT
            + retention_input.urgency
            * self.URGENCY_WEIGHT
            + retention_input.risk
            * self.RISK_WEIGHT
            + retention_input.goal_relevance
            * self.GOAL_WEIGHT
            + retention_input.priority
            * self.PRIORITY_WEIGHT
        )

        score = round(score, 6)

        if score >= self.RETAIN_THRESHOLD:
            level = RetentionLevel.RETAIN
            reason = (
                "Input has sufficient importance for "
                "continued retention."
            )

        elif score >= self.TEMPORARY_THRESHOLD:
            level = RetentionLevel.TEMPORARY
            reason = (
                "Input has moderate value and should "
                "remain available temporarily."
            )

        else:
            level = RetentionLevel.RELEASE
            reason = (
                "Input has insufficient retention value "
                "and can be released."
            )

        return RetentionResult(
            level=level,
            retention_score=score,
            input_id=retention_input.input_id,
            reason=reason,
        )
