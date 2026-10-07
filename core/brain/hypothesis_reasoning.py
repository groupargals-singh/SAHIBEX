from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HypothesisResult:
    hypothesis: str
    score: float
    accepted: bool
    evidence_count: int
    metadata: dict[str, Any]


class HypothesisReasoningEngine:
    """Read-only hypothesis formation and evaluation."""

    def form(self, *, observations: list[Any], candidate: str) -> HypothesisResult:
        if not isinstance(observations, list):
            raise TypeError("observations must be a list")
        if not isinstance(candidate, str) or not candidate.strip():
            raise ValueError("candidate must be a non-empty string")
        return HypothesisResult(candidate.strip(), min(1.0, len(observations) / 5.0), False, len(observations), {"stage": "formed", "requires_evaluation": True})

    def evaluate(self, *, hypothesis: str, evidence: list[bool], contradictions: int = 0) -> HypothesisResult:
        if not isinstance(hypothesis, str) or not hypothesis.strip():
            raise ValueError("hypothesis must be a non-empty string")
        if not isinstance(evidence, list) or not all(isinstance(x, bool) for x in evidence):
            raise TypeError("evidence must be a list of bool")
        if contradictions < 0:
            raise ValueError("contradictions must be >= 0")
        positive = sum(evidence)
        total = len(evidence)
        base = positive / total if total else 0.0
        penalty = min(0.5, contradictions * 0.1)
        score = max(0.0, min(1.0, base - penalty))
        return HypothesisResult(hypothesis.strip(), score, bool(total) and score >= 0.7 and contradictions == 0, total, {"positive_evidence": positive, "contradictions": contradictions})
