from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

PHASE_F_VERSION = "PHASE-F-LTM-1"


@dataclass(frozen=True)
class LongTermMemoryAssessment:
    memory_id: str
    update_score: float
    decay_score: float
    reinforcement_score: float
    forgetting_score: float
    context_link_score: float
    storage_ready: bool
    provenance_ready: bool
    verification_ready: bool
    safe_forget_candidate: bool
    reason: str


class LongTermMemoryExpansionEngine:
    """Non-destructive Phase-F lifecycle assessment."""

    ITEM_IDS: Tuple[str, ...] = (
        "F-11", "F-12", "F-13", "F-14", "F-15",
        "F-16", "F-17", "F-18", "F-19", "F-20",
    )

    def assess(
        self,
        *,
        memory_id: str,
        confidence: float,
        importance: float,
        recency: float,
        access_frequency: float,
        reinforcement_events: float,
        context_strength: float,
        verification_score: float,
        provenance_score: float,
        conflict_score: float = 0.0,
    ) -> LongTermMemoryAssessment:
        if not isinstance(memory_id, str) or not memory_id.strip():
            raise ValueError("memory_id must be a non-empty string")
        values = locals()
        for name in (
            "confidence", "importance", "recency", "access_frequency",
            "reinforcement_events", "context_strength",
            "verification_score", "provenance_score", "conflict_score",
        ):
            if not 0.0 <= float(values[name]) <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

        update_score = round(
            confidence * 0.25 + importance * 0.20 + recency * 0.20
            + verification_score * 0.20 + context_strength * 0.15, 6)
        decay_score = round(
            (1 - recency) * 0.45 + (1 - access_frequency) * 0.30
            + (1 - reinforcement_events) * 0.25, 6)
        reinforcement_score = round(
            reinforcement_events * 0.35 + access_frequency * 0.20
            + confidence * 0.20 + verification_score * 0.25, 6)
        forgetting_score = round(
            decay_score * 0.45 + (1 - importance) * 0.30
            + (1 - context_strength) * 0.25, 6)
        context_link_score = round(
            context_strength * 0.50 + importance * 0.20
            + confidence * 0.15 + verification_score * 0.15, 6)

        return LongTermMemoryAssessment(
            memory_id=memory_id,
            update_score=update_score,
            decay_score=decay_score,
            reinforcement_score=reinforcement_score,
            forgetting_score=forgetting_score,
            context_link_score=context_link_score,
            storage_ready=provenance_score >= 0.5,
            provenance_ready=provenance_score >= 0.7,
            verification_ready=verification_score >= 0.7,
            safe_forget_candidate=(
                forgetting_score >= 0.75
                and importance < 0.40
                and conflict_score < 0.50
            ),
            reason="Assessment only; no destructive memory operation is performed.",
        )
