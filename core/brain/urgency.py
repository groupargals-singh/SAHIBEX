from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class UrgencyLevel(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class UrgencyInput:
    """
    Information used to determine how quickly an event
    should receive cognitive attention.

    This layer does not execute or authorize anything.
    """

    content: str

    time_pressure: float
    deadline_proximity: float
    consequence_of_delay: float
    user_urgency: float
    dependency_blocking: float

    input_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise TypeError("content must be str.")

        if not self.content.strip():
            raise ValueError("content must not be empty.")

        for name in (
            "time_pressure",
            "deadline_proximity",
            "consequence_of_delay",
            "user_urgency",
            "dependency_blocking",
        ):
            value = getattr(self, name)

            if not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be numeric.")

            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(
                    f"{name} must be between 0.0 and 1.0."
                )

        if not isinstance(self.input_id, str):
            raise TypeError("input_id must be str.")

        if not self.input_id.strip():
            raise ValueError("input_id must not be empty.")


@dataclass(frozen=True)
class UrgencyResult:
    """
    Cognitive urgency result.

    Urgency does NOT grant permission or execution authority.
    """

    level: UrgencyLevel
    urgency_score: float
    input_id: str
    reason: str

    result_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    @property
    def urgent(self) -> bool:
        return self.level in (
            UrgencyLevel.HIGH,
            UrgencyLevel.CRITICAL,
        )


class UrgencyEngine:
    """
    Canonical SAHIBEX Urgency Engine.

    Determines how quickly an input should receive
    cognitive attention.

    It does NOT:
    - execute actions
    - grant permissions
    - approve protected actions
    - access credentials
    - modify the Constitution
    - override Human Authority
    """

    VERSION = "1.0"

    TIME_PRESSURE_WEIGHT = 0.25
    DEADLINE_WEIGHT = 0.25
    CONSEQUENCE_WEIGHT = 0.20
    USER_URGENCY_WEIGHT = 0.15
    DEPENDENCY_WEIGHT = 0.15

    CRITICAL_THRESHOLD = 0.80
    HIGH_THRESHOLD = 0.60
    NORMAL_THRESHOLD = 0.35

    def evaluate(
        self,
        urgency_input: UrgencyInput,
    ) -> UrgencyResult:
        if not isinstance(
            urgency_input,
            UrgencyInput,
        ):
            raise TypeError(
                "urgency_input must be UrgencyInput."
            )

        score = (
            urgency_input.time_pressure
            * self.TIME_PRESSURE_WEIGHT
            + urgency_input.deadline_proximity
            * self.DEADLINE_WEIGHT
            + urgency_input.consequence_of_delay
            * self.CONSEQUENCE_WEIGHT
            + urgency_input.user_urgency
            * self.USER_URGENCY_WEIGHT
            + urgency_input.dependency_blocking
            * self.DEPENDENCY_WEIGHT
        )

        score = round(score, 6)

        if score >= self.CRITICAL_THRESHOLD:
            level = UrgencyLevel.CRITICAL
            reason = (
                "Immediate cognitive attention is required "
                "because urgency is critical."
            )

        elif score >= self.HIGH_THRESHOLD:
            level = UrgencyLevel.HIGH
            reason = (
                "The input requires prompt cognitive "
                "attention."
            )

        elif score >= self.NORMAL_THRESHOLD:
            level = UrgencyLevel.NORMAL
            reason = (
                "The input requires normal cognitive "
                "scheduling."
            )

        else:
            level = UrgencyLevel.LOW
            reason = (
                "The input has low time pressure and can "
                "wait for normal processing."
            )

        return UrgencyResult(
            level=level,
            urgency_score=score,
            input_id=urgency_input.input_id,
            reason=reason,
        )
