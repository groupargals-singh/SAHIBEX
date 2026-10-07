from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


MEMORY_IMPORTANCE_VERSION = "P2-MI-1"


class MemoryImportanceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class MemoryImportanceInput:
    content: str
    existing_importance: float
    goal_relevance: float
    recurrence: float
    consequence: float
    future_reuse: float

    input_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise TypeError("content must be str.")

        if not self.content.strip():
            raise ValueError("content must not be empty.")

        for name in (
            "existing_importance",
            "goal_relevance",
            "recurrence",
            "consequence",
            "future_reuse",
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
class MemoryImportanceResult:
    level: MemoryImportanceLevel
    importance_score: float
    input_id: str
    reason: str

    result_id: str = field(
        default_factory=lambda: str(uuid4())
    )


class MemoryImportanceEngine:
    """
    Canonical SAHIBEX Memory Importance Engine.

    Determines how important a memory is for retention,
    retrieval, consolidation, and future reuse.

    This engine does NOT:
    - modify persistent memory
    - delete memory
    - execute actions
    - grant permissions
    - access credentials
    - modify the Constitution
    - determine truth
    - determine confidence
    """

    VERSION = MEMORY_IMPORTANCE_VERSION

    EXISTING_IMPORTANCE_WEIGHT = 0.25
    GOAL_RELEVANCE_WEIGHT = 0.25
    RECURRENCE_WEIGHT = 0.15
    CONSEQUENCE_WEIGHT = 0.20
    FUTURE_REUSE_WEIGHT = 0.15

    CRITICAL_THRESHOLD = 0.85
    HIGH_THRESHOLD = 0.65
    MEDIUM_THRESHOLD = 0.40

    def evaluate(
        self,
        importance_input: MemoryImportanceInput,
    ) -> MemoryImportanceResult:
        if not isinstance(
            importance_input,
            MemoryImportanceInput,
        ):
            raise TypeError(
                "importance_input must be "
                "MemoryImportanceInput."
            )

        score = (
            importance_input.existing_importance
            * self.EXISTING_IMPORTANCE_WEIGHT
            + importance_input.goal_relevance
            * self.GOAL_RELEVANCE_WEIGHT
            + importance_input.recurrence
            * self.RECURRENCE_WEIGHT
            + importance_input.consequence
            * self.CONSEQUENCE_WEIGHT
            + importance_input.future_reuse
            * self.FUTURE_REUSE_WEIGHT
        )

        score = round(score, 6)

        if score >= self.CRITICAL_THRESHOLD:
            level = MemoryImportanceLevel.CRITICAL
            reason = (
                "Memory has critical value for "
                "SAHIBEX retention and future use."
            )

        elif score >= self.HIGH_THRESHOLD:
            level = MemoryImportanceLevel.HIGH
            reason = (
                "Memory has high value for "
                "retention and future retrieval."
            )

        elif score >= self.MEDIUM_THRESHOLD:
            level = MemoryImportanceLevel.MEDIUM
            reason = (
                "Memory has meaningful value and "
                "should remain available."
            )

        else:
            level = MemoryImportanceLevel.LOW
            reason = (
                "Memory has relatively low importance "
                "for long-term retention."
            )

        return MemoryImportanceResult(
            level=level,
            importance_score=score,
            input_id=importance_input.input_id,
            reason=reason,
        )
