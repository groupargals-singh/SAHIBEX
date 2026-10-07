from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class DistractionDecision(str, Enum):
    ALLOW = "allow"
    HOLD = "hold"
    FILTER = "filter"


@dataclass(frozen=True)
class DistractionFilterInput:
    content: str
    relevance: float
    goal_relevance: float
    urgency: float
    priority: float
    distraction_strength: float

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
            "relevance",
            "goal_relevance",
            "urgency",
            "priority",
            "distraction_strength",
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
class DistractionFilterResult:
    decision: DistractionDecision
    distraction_score: float
    signal_score: float
    input_id: str
    reason: str
    result_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    @property
    def filtered(self) -> bool:
        return self.decision == DistractionDecision.FILTER


class DistractionFilterEngine:
    """
    SAHIBEX Distraction Filtering Engine.

    Determines whether an incoming signal is useful,
    temporarily worth holding, or likely distracting.

    This engine does not:
    - execute actions
    - grant permissions
    - modify memory
    - access credentials
    - modify the Constitution
    - override Human Authority
    """

    VERSION = "1.0"

    RELEVANCE_WEIGHT = 0.25
    GOAL_WEIGHT = 0.25
    URGENCY_WEIGHT = 0.15
    PRIORITY_WEIGHT = 0.15
    DISTRACTION_WEIGHT = 0.20

    ALLOW_THRESHOLD = 0.60
    HOLD_THRESHOLD = 0.35

    def evaluate(
        self,
        filter_input: DistractionFilterInput,
    ) -> DistractionFilterResult:
        if not isinstance(
            filter_input,
            DistractionFilterInput,
        ):
            raise TypeError(
                "filter_input must be DistractionFilterInput."
            )

        signal_score = (
            filter_input.relevance
            * self.RELEVANCE_WEIGHT
            + filter_input.goal_relevance
            * self.GOAL_WEIGHT
            + filter_input.urgency
            * self.URGENCY_WEIGHT
            + filter_input.priority
            * self.PRIORITY_WEIGHT
        )

        distraction_score = round(
            (
                filter_input.distraction_strength
                * self.DISTRACTION_WEIGHT
                + (1.0 - signal_score)
                * (
                    self.RELEVANCE_WEIGHT
                    + self.GOAL_WEIGHT
                    + self.URGENCY_WEIGHT
                    + self.PRIORITY_WEIGHT
                )
            ),
            6,
        )

        signal_score = round(signal_score, 6)

        if (
            signal_score >= self.ALLOW_THRESHOLD
            and distraction_score < 0.50
        ):
            decision = DistractionDecision.ALLOW
            reason = (
                "Input is sufficiently relevant and "
                "does not present strong distraction risk."
            )

        elif (
            signal_score >= self.HOLD_THRESHOLD
            or distraction_score < 0.70
        ):
            decision = DistractionDecision.HOLD
            reason = (
                "Input has some value but should not "
                "immediately interrupt the current focus."
            )

        else:
            decision = DistractionDecision.FILTER
            reason = (
                "Input has low useful signal and high "
                "distraction risk."
            )

        return DistractionFilterResult(
            decision=decision,
            distraction_score=distraction_score,
            signal_score=signal_score,
            input_id=filter_input.input_id,
            reason=reason,
        )
