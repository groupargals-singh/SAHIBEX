from __future__ import annotations

from dataclasses import dataclass, field

from core.brain.reasoning import ReasoningEngine
from core.brain.reasoning_coordinator import ReasoningCoordinator


@dataclass(frozen=True)
class MotherReasoningResult:
    success: bool
    user_input: str
    intent: str
    action: str
    reasoning_response: str
    reasoning_status: str
    context_summary: dict = field(default_factory=dict)
    reasoning_assessment: object | None = None


class MotherReasoningIntegration:
    """
    Mother Brain controlled reasoning integration.

    MasterBrain remains authoritative for:
    - Constitution
    - Permission
    - Protected actions
    - Verification
    - Human authority

    This adapter MUST NOT rerun the full ReasoningEngine pipeline.

    It receives an already-approved request from MasterBrain and
    uses the existing ReasoningEngine only for cognitive response
    construction.
    """

    VERSION = "1.1"

    def __init__(
        self,
        *,
        reasoning_engine: ReasoningEngine | None = None,
    ) -> None:
        self.reasoning = (
            reasoning_engine
            if reasoning_engine is not None
            else ReasoningEngine()
        )
        self.reasoning_coordinator = ReasoningCoordinator()

    def analyze_approved_request(
        self,
        *,
        user_input: str,
        intent: str,
        action: str,
        decision_context: dict | None = None,
    ) -> MotherReasoningResult:
        if not isinstance(user_input, str):
            raise TypeError("user_input must be str")

        if not user_input.strip():
            raise ValueError("user_input must not be empty")

        if not isinstance(intent, str):
            raise TypeError("intent must be str")

        if not intent.strip():
            raise ValueError("intent must not be empty")

        if not isinstance(action, str):
            raise TypeError("action must be str")

        if not action.strip():
            raise ValueError("action must not be empty")

        text = user_input.strip()
        normalized_intent = intent.strip()
        normalized_action = action.strip()

        context_summary = (
            dict(decision_context)
            if isinstance(decision_context, dict)
            else {}
        )
        # Feed the bounded context into the structured reasoning coordinator
        # as reusable prior context. Missing evidence is explicit: this
        # assessment is not a factual verification or execution approval.
        reasoning_assessment = self.reasoning_coordinator.assess(
            goal=text,
            intent=normalized_intent,
            confidence=0.5,
            quality_score=0.5,
            missing_information=True,
            prior_context=context_summary,
        )
        response = self.reasoning._build_response(
            text=text,
            intent=normalized_intent,
            action=normalized_action,
            allowed=True,
            requires_confirmation=False,
            verification_status="VERIFIED",
        )

        self.reasoning.context.add_turn(
            user=text,
            assistant=response,
            intent=normalized_intent,
        )

        return MotherReasoningResult(
            success=True,
            user_input=text,
            intent=normalized_intent,
            action=normalized_action,
            reasoning_response=response,
            reasoning_status="COMPLETED",
            context_summary=context_summary,
            reasoning_assessment=reasoning_assessment,
        )
