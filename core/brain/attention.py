from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class AttentionDecision(str, Enum):
    FOCUS = "focus"
    HOLD = "hold"
    IGNORE = "ignore"


@dataclass(frozen=True)
class AttentionInput:
    """
    Cognitive input presented to the Attention Engine.

    This layer only decides cognitive attention.
    It does not grant authority or execute actions.
    """

    content: str
    relevance: float
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
            raise ValueError("content must not be empty.")

        for name in (
            "relevance",
            "urgency",
            "risk",
            "goal_relevance",
            "priority",
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
class AttentionResult:
    """
    Result produced by the Attention Engine.

    Attention is cognitive prioritization only.
    It is NOT permission or execution authority.
    """

    decision: AttentionDecision
    attention_score: float
    input_id: str
    reason: str
    result_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    @property
    def focused(self) -> bool:
        return self.decision == AttentionDecision.FOCUS

    @property
    def ignored(self) -> bool:
        return self.decision == AttentionDecision.IGNORE


class AttentionEngine:
    """
    Canonical cognitive Attention / Relevance Engine.

    Responsibilities:
    - relevance evaluation
    - urgency evaluation
    - risk awareness
    - goal relevance
    - priority
    - focus selection
    - distraction filtering

    This layer does NOT:
    - execute actions
    - grant permissions
    - approve protected actions
    - access credentials
    - modify the Constitution
    - bypass Human Authority
    """

    VERSION = "1.0"

    RELEVANCE_WEIGHT = 0.25
    URGENCY_WEIGHT = 0.20
    RISK_WEIGHT = 0.20
    GOAL_WEIGHT = 0.20
    PRIORITY_WEIGHT = 0.15

    FOCUS_THRESHOLD = 0.60
    HOLD_THRESHOLD = 0.35

    def evaluate(
        self,
        attention_input: AttentionInput,
    ) -> AttentionResult:
        if not isinstance(
            attention_input,
            AttentionInput,
        ):
            raise TypeError(
                "attention_input must be AttentionInput."
            )

        score = (
            attention_input.relevance
            * self.RELEVANCE_WEIGHT
            + attention_input.urgency
            * self.URGENCY_WEIGHT
            + attention_input.risk
            * self.RISK_WEIGHT
            + attention_input.goal_relevance
            * self.GOAL_WEIGHT
            + attention_input.priority
            * self.PRIORITY_WEIGHT
        )

        score = round(score, 6)

        if score >= self.FOCUS_THRESHOLD:
            decision = AttentionDecision.FOCUS
            reason = (
                "Input has sufficient cognitive relevance "
                "for active focus."
            )

        elif score >= self.HOLD_THRESHOLD:
            decision = AttentionDecision.HOLD
            reason = (
                "Input is potentially relevant but does not "
                "currently justify active focus."
            )

        else:
            decision = AttentionDecision.IGNORE
            reason = (
                "Input is below the cognitive attention "
                "threshold and is treated as distraction."
            )

        return AttentionResult(
            decision=decision,
            attention_score=score,
            input_id=attention_input.input_id,
            reason=reason,
        )
