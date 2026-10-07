from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


PHASE_M_VERSION = "PHASE-M-LEARNING-1"


@dataclass(frozen=True)
class LearningAssessment:
    """Read-only assessment of the Phase M learning capabilities."""

    phase: str
    version: str
    scores: Mapping[str, float]
    ready: bool


class LearningExpansion:
    """Read-only learning coverage and safety assessment layer.

    This layer does not execute actions, grant permissions, modify the
    Constitution, or override Human Authority. It evaluates learning
    readiness using bounded evidence supplied by existing subsystems.
    """

    ITEM_IDS = tuple(f"M-{index:02d}" for index in range(1, 16))
    ITEM_NAMES = (
        "Learning Foundation",
        "Experience-Based Learning",
        "Feedback Learning",
        "Pattern Learning",
        "Lesson Extraction",
        "Knowledge Update Learning",
        "Reinforcement Learning",
        "Correction Learning",
        "Knowledge Transfer",
        "Adaptive Learning",
        "Learning Confidence",
        "Learning Verification",
        "Memory-Learning Integration",
        "Knowledge-Learning Integration",
        "Safe Learning Boundary",
    )

    def assess(
        self,
        *,
        foundation: float = 1.0,
        experience: float = 1.0,
        feedback: float = 1.0,
        patterns: float = 1.0,
        lessons: float = 1.0,
        knowledge_update: float = 1.0,
        reinforcement: float = 1.0,
        correction: float = 1.0,
        transfer: float = 1.0,
        adaptation: float = 1.0,
        confidence: float = 1.0,
        verification: float = 1.0,
        memory_integration: float = 1.0,
        knowledge_integration: float = 1.0,
        safety: float = 1.0,
    ) -> LearningAssessment:
        values = (
            foundation, experience, feedback, patterns, lessons,
            knowledge_update, reinforcement, correction, transfer,
            adaptation, confidence, verification, memory_integration,
            knowledge_integration, safety,
        )
        scores = {}
        for item_id, value in zip(self.ITEM_IDS, values):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{item_id} score must be numeric")
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{item_id} score must be between 0 and 1")
            scores[item_id] = round(float(value), 6)

        return LearningAssessment(
            phase="M",
            version=PHASE_M_VERSION,
            scores=scores,
            ready=all(score >= 0.8 for score in scores.values()),
        )

    @staticmethod
    def security_summary() -> dict[str, bool]:
        return {
            "read_only": True,
            "executes_actions": False,
            "grants_permission": False,
            "modifies_constitution": False,
            "overrides_human_authority": False,
        }
