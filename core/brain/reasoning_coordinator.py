from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from core.brain.hypothesis_reasoning import HypothesisReasoningEngine
from core.brain.reasoning_constraints import ConstraintReasoningEngine
from core.brain.reasoning_modes import ReasoningModesEngine
from core.brain.uncertainty import UncertaintyEngine


@dataclass(frozen=True)
class ReasoningAssessment:
    """Structured reasoning state; stores rationale metadata, not hidden chain-of-thought."""

    reasoning_id: str
    goal: str
    steps: tuple[str, ...]
    assumptions: tuple[str, ...]
    selected_strategy: str
    confidence: float
    uncertainty: float
    needs_verification: bool
    conflicts: tuple[str, ...]
    verified: bool
    corrected: bool
    correction_count: int
    reusable_context: dict[str, Any] = field(default_factory=dict)


class ReasoningCoordinator:
    """Coordinates structured reasoning primitives without executing protected actions."""

    def __init__(self) -> None:
        self.modes = ReasoningModesEngine()
        self.hypotheses = HypothesisReasoningEngine()
        self.constraints = ConstraintReasoningEngine()
        self.uncertainty = UncertaintyEngine()
        self._sessions: dict[str, ReasoningAssessment] = {}

    def assess(
        self,
        *,
        goal: str,
        intent: str = "",
        confidence: float = 0.5,
        quality_score: float = 0.7,
        conflict_score: float = 0.0,
        missing_information: bool = False,
        ambiguous: bool = False,
        assumptions: list[str] | None = None,
        evidence: list[bool] | None = None,
        constraints: list[bool] | None = None,
        prior_context: dict[str, Any] | None = None,
    ) -> ReasoningAssessment:
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("goal must be a non-empty string")
        if not isinstance(intent, str):
            raise TypeError("intent must be str")
        assumptions = assumptions or []
        evidence = evidence or []
        constraints = constraints or []
        if not all(isinstance(x, str) and x.strip() for x in assumptions):
            raise TypeError("assumptions must contain non-empty strings")
        if not all(isinstance(x, bool) for x in evidence):
            raise TypeError("evidence must contain bool values")
        if not all(isinstance(x, bool) for x in constraints):
            raise TypeError("constraints must contain bool values")

        # Strategy selection is deterministic and explainable.
        if constraints:
            strategy = "constraint"
        elif evidence:
            strategy = "evidence"
        elif conflict_score > 0.0:
            strategy = "abductive_conflict_resolution"
        elif intent.strip():
            strategy = "intent_guided"
        else:
            strategy = "general"

        steps = [
            "understand_goal",
            "identify_assumptions",
            "select_reasoning_strategy",
            "evaluate_available_evidence",
            "check_constraints",
            "assess_uncertainty",
            "verify_conclusion",
        ]

        conflicts: list[str] = []
        if constraints:
            conflicts.extend(
                f"constraint_{i}" for i, value in enumerate(constraints) if not value
            )
        if evidence and not all(evidence):
            conflicts.append("insufficient_or_conflicting_evidence")

        evidence_quality = (
            sum(evidence) / len(evidence) if evidence else float(quality_score)
        )
        uncertainty = self.uncertainty.assess(
            input_id=goal.strip(),
            confidence=confidence,
            quality_score=evidence_quality,
            conflict_score=conflict_score,
            missing_information=missing_information,
            ambiguous=ambiguous,
            reasons=tuple(conflicts),
        )

        base_confidence = max(0.0, min(1.0, float(confidence)))
        if evidence:
            base_confidence = (base_confidence + evidence_quality) / 2.0
        if conflicts:
            base_confidence = max(0.0, base_confidence - 0.15 * len(conflicts))
        # Missing inputs and ambiguity are blockers in their own right; a low
        # numeric uncertainty score must not silently override either flag.
        verified = (
            not conflicts
            and not missing_information
            and not ambiguous
            and not uncertainty.requires_verification
            and (not constraints or all(constraints))
        )
        corrected = False
        correction_count = 0

        # A failed first assessment is corrected by explicitly marking the
        # weak signal and lowering confidence rather than pretending certainty.
        if not verified:
            correction_count = 1
            corrected = True
            steps.append("apply_correction")
            base_confidence = min(base_confidence, max(0.0, 1.0 - uncertainty.uncertainty))

        prior = dict(prior_context or {})
        prior["goal"] = goal.strip()
        prior["intent"] = intent.strip()
        prior["strategy"] = strategy
        prior["confidence"] = round(base_confidence, 4)
        prior["uncertainty"] = uncertainty.uncertainty

        result = ReasoningAssessment(
            reasoning_id=str(uuid4()),
            goal=goal.strip(),
            steps=tuple(steps),
            assumptions=tuple(x.strip() for x in assumptions),
            selected_strategy=strategy,
            confidence=round(base_confidence, 4),
            uncertainty=uncertainty.uncertainty,
            needs_verification=(
                uncertainty.requires_verification or missing_information or ambiguous
            ),
            conflicts=tuple(dict.fromkeys(conflicts)),
            verified=verified,
            corrected=corrected,
            correction_count=correction_count,
            reusable_context=prior,
        )
        self._sessions[result.reasoning_id] = result
        return result

    def resume(self, reasoning_id: str) -> ReasoningAssessment:
        if not isinstance(reasoning_id, str) or not reasoning_id.strip():
            raise ValueError("reasoning_id must be a non-empty string")
        try:
            return self._sessions[reasoning_id]
        except KeyError as exc:
            raise KeyError(f"Unknown reasoning session: {reasoning_id}") from exc

    def verify(self, assessment: ReasoningAssessment) -> ReasoningAssessment:
        if not isinstance(assessment, ReasoningAssessment):
            raise TypeError("assessment must be ReasoningAssessment")
        # Rechecking unchanged metadata is not new evidence. This method may
        # revoke a prior verified flag when quality thresholds fail, but it may
        # not promote an unverified assessment without an evidence-bearing
        # assessment cycle.
        verified = (
            assessment.verified
            and not assessment.needs_verification
            and not assessment.conflicts
            and assessment.uncertainty < 0.60
            and assessment.confidence >= 0.50
        )
        if verified == assessment.verified:
            return assessment
        updated = ReasoningAssessment(
            reasoning_id=assessment.reasoning_id,
            goal=assessment.goal,
            steps=assessment.steps + ("reverify_result",),
            assumptions=assessment.assumptions,
            selected_strategy=assessment.selected_strategy,
            confidence=assessment.confidence,
            uncertainty=assessment.uncertainty,
            needs_verification=assessment.needs_verification or not verified,
            conflicts=assessment.conflicts,
            verified=verified,
            corrected=assessment.corrected,
            correction_count=assessment.correction_count,
            reusable_context=dict(assessment.reusable_context),
        )
        self._sessions[updated.reasoning_id] = updated
        return updated

    @staticmethod
    def capability_contract() -> dict[str, bool]:
        return {
            "understand": True,
            "decompose": True,
            "strategy_selection": True,
            "assumption_tracking": True,
            "uncertainty": True,
            "evidence_check": True,
            "constraint_check": True,
            "conflict_detection": True,
            "verification": True,
            "correction": True,
            "long_running_resume": True,
            "context_reuse": True,
            "protected_execution": False,
            "permission_grant": False,
            "constitution_override": False,
        }
