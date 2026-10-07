from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class AttentionSwitchDecision(str, Enum):
    SWITCH = "switch"
    HOLD = "hold"
    NO_FOCUS = "no_focus"


@dataclass(frozen=True)
class AttentionSwitchInput:
    current_focus_score: float
    new_input_score: float
    current_focus_urgency: float
    new_input_urgency: float
    current_focus_risk: float
    new_input_risk: float
    current_goal_relevance: float
    new_goal_relevance: float
    current_priority: float
    new_priority: float

    input_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        for name in (
            "current_focus_score",
            "new_input_score",
            "current_focus_urgency",
            "new_input_urgency",
            "current_focus_risk",
            "new_input_risk",
            "current_goal_relevance",
            "new_goal_relevance",
            "current_priority",
            "new_priority",
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
class AttentionSwitchResult:
    decision: AttentionSwitchDecision
    switch_score: float
    current_score: float
    new_score: float
    reason: str
    input_id: str
    result_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    @property
    def should_switch(self) -> bool:
        return self.decision == AttentionSwitchDecision.SWITCH


class AttentionSwitchingEngine:
    """
    SAHIBEX Attention Switching Engine.

    Compares the current focus with a new input and
    determines whether attention should switch.

    This engine does not:
    - execute actions
    - grant permissions
    - approve protected actions
    - access credentials
    - modify the Constitution
    - override Human Authority
    """

    VERSION = "1.0"

    FOCUS_WEIGHT = 0.20
    URGENCY_WEIGHT = 0.20
    RISK_WEIGHT = 0.20
    GOAL_WEIGHT = 0.25
    PRIORITY_WEIGHT = 0.15

    SWITCH_MARGIN = 0.10
    MIN_NEW_SCORE = 0.35

    def _score(
        self,
        focus: float,
        urgency: float,
        risk: float,
        goal_relevance: float,
        priority: float,
    ) -> float:
        return round(
            focus * self.FOCUS_WEIGHT
            + urgency * self.URGENCY_WEIGHT
            + risk * self.RISK_WEIGHT
            + goal_relevance * self.GOAL_WEIGHT
            + priority * self.PRIORITY_WEIGHT,
            6,
        )

    def evaluate(
        self,
        switch_input: AttentionSwitchInput,
    ) -> AttentionSwitchResult:
        if not isinstance(
            switch_input,
            AttentionSwitchInput,
        ):
            raise TypeError(
                "switch_input must be AttentionSwitchInput."
            )

        current_score = self._score(
            switch_input.current_focus_score,
            switch_input.current_focus_urgency,
            switch_input.current_focus_risk,
            switch_input.current_goal_relevance,
            switch_input.current_priority,
        )

        new_score = self._score(
            switch_input.new_input_score,
            switch_input.new_input_urgency,
            switch_input.new_input_risk,
            switch_input.new_goal_relevance,
            switch_input.new_priority,
        )

        switch_score = round(
            new_score - current_score,
            6,
        )

        if new_score < self.MIN_NEW_SCORE:
            decision = AttentionSwitchDecision.NO_FOCUS
            reason = (
                "New input does not have enough "
                "attention value."
            )

        elif switch_score >= self.SWITCH_MARGIN:
            decision = AttentionSwitchDecision.SWITCH
            reason = (
                "New input has materially higher "
                "attention value than the current focus."
            )

        else:
            decision = AttentionSwitchDecision.HOLD
            reason = (
                "Current focus remains sufficiently "
                "valuable; no attention switch required."
            )

        return AttentionSwitchResult(
            decision=decision,
            switch_score=switch_score,
            current_score=current_score,
            new_score=new_score,
            reason=reason,
            input_id=switch_input.input_id,
        )
