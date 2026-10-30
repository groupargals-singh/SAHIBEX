from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


SUPPORTED_STATUSES = {"SUPPORTED", "MULTI_SOURCE_SUPPORTED"}


@dataclass(frozen=True)
class AnswerArbitrationResult:
    """Deterministic third-pass comparison of the two existing answer paths."""

    status: str
    accepted: bool
    candidate_a_claim_ids: tuple[str, ...]
    candidate_b_claim_ids: tuple[str, ...]
    reasons: tuple[str, ...]
    version: str = "1.0"


class AnswerArbitrator:
    """Compare quality-aware claim synthesis with evidence-linked answer synthesis.

    This is a deterministic verifier, not a third language model. It must not
    claim independent model consensus. It fails closed when the two synthesis
    paths disagree or quality/conflict gates are not satisfied.
    """

    @staticmethod
    def _unique(values: Iterable[object]) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            if not isinstance(value, str) or not value.strip():
                continue
            normalized = value.strip()
            if normalized not in seen:
                seen.add(normalized)
                result.append(normalized)
        return tuple(result)

    def arbitrate(self, *, quality_answer, synthesized_answer, unresolved_conflicts: int) -> AnswerArbitrationResult:
        quality_claims = tuple(getattr(quality_answer, "claims", ()) or ())
        candidate_a = self._unique(
            getattr(claim, "knowledge_id", None) for claim in quality_claims
        )
        candidate_b = self._unique(
            getattr(synthesized_answer, "knowledge_ids", ()) or ()
        )
        reasons: list[str] = []

        if not candidate_a or not candidate_b:
            reasons.append("one_or_both_candidates_empty")
        if set(candidate_a) != set(candidate_b):
            reasons.append("candidate_claim_sets_disagree")

        quality_status = str(getattr(quality_answer, "overall_status", "")).upper()
        if quality_status not in SUPPORTED_STATUSES:
            reasons.append("quality_candidate_not_supported")

        if getattr(synthesized_answer, "verified", False) is not True:
            reasons.append("synthesis_candidate_not_verified")

        if unresolved_conflicts:
            reasons.append("unresolved_conflicts_present")

        accepted = not reasons
        return AnswerArbitrationResult(
            status="ACCEPTED" if accepted else "REJECTED",
            accepted=accepted,
            candidate_a_claim_ids=candidate_a,
            candidate_b_claim_ids=candidate_b,
            reasons=tuple(reasons),
        )
