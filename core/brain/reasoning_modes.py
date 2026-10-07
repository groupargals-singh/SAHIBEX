from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReasoningModeResult:
    mode: str
    conclusion: Any
    confidence: float
    evidence_count: int
    verified: bool
    conflict: bool = False
    metadata: dict[str, Any] | None = None


class ReasoningModesEngine:
    """Read-only structured reasoning primitives for Phase H."""

    MODES = ("deductive", "inductive", "abductive", "causal", "comparative")

    @staticmethod
    def _confidence(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def deductive(self, *, premises: list[bool], conclusion: bool) -> ReasoningModeResult:
        if not isinstance(premises, list) or not all(isinstance(x, bool) for x in premises):
            raise TypeError("premises must be a list of bool")
        valid = all(premises)
        verified = valid == bool(conclusion)
        return ReasoningModeResult("deductive", bool(conclusion), 1.0 if verified else 0.0, len(premises), verified, not verified, {"premises_satisfied": valid})

    def inductive(self, *, observations: list[Any], pattern_support: float) -> ReasoningModeResult:
        if not isinstance(observations, list):
            raise TypeError("observations must be a list")
        confidence = self._confidence(pattern_support)
        return ReasoningModeResult("inductive", "supported_pattern" if confidence >= 0.5 else "insufficient_pattern", confidence, len(observations), confidence >= 0.5, False, {"generalization": confidence >= 0.5})

    def abductive(self, *, hypotheses: list[tuple[str, float]]) -> ReasoningModeResult:
        if not isinstance(hypotheses, list):
            raise TypeError("hypotheses must be a list")
        clean = [(str(name), self._confidence(score)) for name, score in hypotheses]
        clean.sort(key=lambda item: item[1], reverse=True)
        best = clean[0] if clean else ("no_hypothesis", 0.0)
        return ReasoningModeResult("abductive", best[0], best[1], len(clean), bool(clean) and best[1] > 0.0, False, {"ranked_hypotheses": clean})

    def causal(self, *, cause: Any, effect: Any, evidence_strength: float) -> ReasoningModeResult:
        confidence = self._confidence(evidence_strength)
        return ReasoningModeResult("causal", {"cause": cause, "effect": effect}, confidence, 1, confidence >= 0.5, False, {"causal_claim": confidence >= 0.5})

    def comparative(self, *, candidates: dict[str, float]) -> ReasoningModeResult:
        if not isinstance(candidates, dict):
            raise TypeError("candidates must be a dict")
        scores = {str(k): self._confidence(v) for k, v in candidates.items()}
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        conflict = len(ranked) > 1 and ranked[0][1] == ranked[1][1]
        best = ranked[0] if ranked else ("no_candidate", 0.0)
        return ReasoningModeResult("comparative", best[0], best[1], len(ranked), bool(ranked), conflict, {"ranking": ranked})
