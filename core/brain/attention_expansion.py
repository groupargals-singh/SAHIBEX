from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AttentionState(str, Enum):
    ACTIVE = "active"
    HELD = "held"
    RECOVERING = "recovering"
    DISTRACTED = "distracted"


@dataclass(frozen=True)
class AttentionAssessment:
    selection_score: float
    relevance: float
    priority: float
    urgency: float
    risk: float
    goal_relevance: float
    state: AttentionState
    reason: str


@dataclass(frozen=True)
class AttentionConflict:
    current_score: float
    competing_score: float
    conflict: bool
    preferred: str
    reason: str


@dataclass(frozen=True)
class AttentionRecovery:
    previous_state: AttentionState
    recovered: bool
    recovery_score: float
    reason: str


class AttentionExpansionEngine:
    """
    Additive Phase D coverage layer.

    This module complements the existing AttentionEngine,
    AttentionSwitchingEngine, and UrgencyEngine.

    It is cognitive-only:
    - no permissions
    - no protected execution
    - no credentials
    - no system changes
    - no Constitution changes
    - no Human Authority override
    """

    VERSION = "1.0"

    SELECTION_WEIGHT = 0.25
    RELEVANCE_WEIGHT = 0.15
    PRIORITY_WEIGHT = 0.15
    URGENCY_WEIGHT = 0.15
    RISK_WEIGHT = 0.15
    GOAL_WEIGHT = 0.15

    RETENTION_THRESHOLD = 0.55
    DISTRACTION_THRESHOLD = 0.35
    RECOVERY_THRESHOLD = 0.60
    CONFLICT_MARGIN = 0.10

    @staticmethod
    def _validate_score(name: str, value: float) -> float:
        if not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be numeric.")
        value = float(value)
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be between 0.0 and 1.0.")
        return value

    def assess(
        self,
        *,
        selection: float,
        relevance: float,
        priority: float,
        urgency: float,
        risk: float,
        goal_relevance: float,
    ) -> AttentionAssessment:
        values = {
            "selection": selection,
            "relevance": relevance,
            "priority": priority,
            "urgency": urgency,
            "risk": risk,
            "goal_relevance": goal_relevance,
        }
        values = {
            name: self._validate_score(name, value)
            for name, value in values.items()
        }

        score = round(
            values["selection"] * self.SELECTION_WEIGHT
            + values["relevance"] * self.RELEVANCE_WEIGHT
            + values["priority"] * self.PRIORITY_WEIGHT
            + values["urgency"] * self.URGENCY_WEIGHT
            + values["risk"] * self.RISK_WEIGHT
            + values["goal_relevance"] * self.GOAL_WEIGHT,
            6,
        )

        if score >= self.RETENTION_THRESHOLD:
            state = AttentionState.ACTIVE
            reason = "Attention value supports active retention."
        elif score >= self.DISTRACTION_THRESHOLD:
            state = AttentionState.HELD
            reason = "Attention value is useful but not dominant."
        else:
            state = AttentionState.DISTRACTED
            reason = "Attention value is below the distraction threshold."

        return AttentionAssessment(
            selection_score=score,
            relevance=values["relevance"],
            priority=values["priority"],
            urgency=values["urgency"],
            risk=values["risk"],
            goal_relevance=values["goal_relevance"],
            state=state,
            reason=reason,
        )

    def resolve_conflict(
        self,
        *,
        current_score: float,
        competing_score: float,
    ) -> AttentionConflict:
        current = self._validate_score("current_score", current_score)
        competing = self._validate_score("competing_score", competing_score)
        delta = competing - current

        if delta >= self.CONFLICT_MARGIN:
            return AttentionConflict(
                current_score=current,
                competing_score=competing,
                conflict=True,
                preferred="competing",
                reason="Competing attention has a materially higher score.",
            )

        if -delta >= self.CONFLICT_MARGIN:
            return AttentionConflict(
                current_score=current,
                competing_score=competing,
                conflict=True,
                preferred="current",
                reason="Current attention has a materially higher score.",
            )

        return AttentionConflict(
            current_score=current,
            competing_score=competing,
            conflict=False,
            preferred="current",
            reason="Scores are too close to justify an attention switch.",
        )

    def recover(
        self,
        *,
        previous_state: AttentionState,
        recovery_signal: float,
    ) -> AttentionRecovery:
        if not isinstance(previous_state, AttentionState):
            raise TypeError("previous_state must be AttentionState.")

        signal = self._validate_score("recovery_signal", recovery_signal)

        recovered = signal >= self.RECOVERY_THRESHOLD
        if recovered:
            reason = "Recovery signal is sufficient to re-focus attention."
        else:
            reason = "Recovery signal is insufficient for re-focus."

        return AttentionRecovery(
            previous_state=previous_state,
            recovered=recovered,
            recovery_score=signal,
            reason=reason,
        )
