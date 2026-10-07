from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


PHASE_E_VERSION = "PHASE-E-WM-1"


@dataclass(frozen=True)
class WorkingMemoryAssessment:
    item_id: str
    value: float
    retained: bool
    reason: str


class WorkingMemoryExpansionEngine:
    """Additive verification layer for Phase E working-memory coverage.

    Cognitive/read-only only. It does not grant permission, execute actions,
    modify long-term storage, or modify the Constitution.
    """

    ITEM_IDS = tuple(f"E-{index:02d}" for index in range(1, 13))

    def __init__(self, retention_threshold: float = 0.50) -> None:
        if not 0.0 <= retention_threshold <= 1.0:
            raise ValueError("retention_threshold must be between 0 and 1")
        self.retention_threshold = retention_threshold

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def assess(
        self,
        *,
        relevance: float,
        priority: float,
        recency: float,
        confidence: float,
        goal_relevance: float,
        access_strength: float,
        interference: float,
        cognitive_load: float,
        task_context: float,
        stability: float,
        importance: float,
        continuity: float,
    ) -> WorkingMemoryAssessment:
        values = (
            relevance, priority, recency, confidence, goal_relevance,
            access_strength, interference, cognitive_load, task_context,
            stability, importance, continuity,
        )
        if any(not 0.0 <= float(value) <= 1.0 for value in values):
            raise ValueError("all assessment inputs must be between 0 and 1")

        positive = (
            relevance + priority + recency + confidence
            + goal_relevance + access_strength + task_context
            + stability + importance + continuity
        ) / 10.0
        penalty = (interference + cognitive_load) / 2.0
        score = self._clamp(positive * 0.75 + (1.0 - penalty) * 0.25)
        retained = score >= self.retention_threshold

        return WorkingMemoryAssessment(
            item_id="E-01:E-12",
            value=score,
            retained=retained,
            reason="retained" if retained else "below working-memory threshold",
        )

    def rank(self, values: Iterable[float]) -> tuple[float, ...]:
        checked = tuple(self._clamp(value) for value in values)
        return tuple(sorted(checked, reverse=True))

    def security_summary(self) -> dict:
        return {
            "version": PHASE_E_VERSION,
            "bounded_cognitive_layer": True,
            "grants_permission": False,
            "executes_actions": False,
            "writes_long_term_storage": False,
            "modifies_constitution": False,
            "overrides_human_authority": False,
        }
