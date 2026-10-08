from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from core.brain.reasoning import ReasoningEngine
from core.brain.reasoning_coordinator import ReasoningCoordinator
from core.brain.operational_model import (
    OperationalModelIntegration,
    OperationalModelResult,
)


@dataclass(frozen=True)
class OperationalReasoningResult:
    success: bool
    user_input: str
    intent: str
    action: str
    reasoning_response: str
    model_response: str
    model_provider: str
    model: str
    requires_confirmation: bool
    verification_status: str
    reasoning_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool")

        if not isinstance(self.user_input, str):
            raise TypeError("user_input must be str")

        if not self.user_input.strip():
            raise ValueError("user_input must not be empty")

        if not isinstance(self.intent, str):
            raise TypeError("intent must be str")

        if not self.intent.strip():
            raise ValueError("intent must not be empty")

        if not isinstance(self.action, str):
            raise TypeError("action must be str")

        if not self.action.strip():
            raise ValueError("action must not be empty")

        if not isinstance(self.reasoning_response, str):
            raise TypeError("reasoning_response must be str")

        if not isinstance(self.model_response, str):
            raise TypeError("model_response must be str")

        if not isinstance(self.model_provider, str):
            raise TypeError("model_provider must be str")

        if not self.model_provider.strip():
            raise ValueError("model_provider must not be empty")

        if not isinstance(self.model, str):
            raise TypeError("model must be str")

        if not self.model.strip():
            raise ValueError("model must not be empty")

        if not isinstance(self.requires_confirmation, bool):
            raise TypeError(
                "requires_confirmation must be bool"
            )

        if not isinstance(self.verification_status, str):
            raise TypeError(
                "verification_status must be str"
            )

        if not self.verification_status.strip():
            raise ValueError(
                "verification_status must not be empty"
            )

        if not isinstance(self.reasoning_id, str):
            raise TypeError("reasoning_id must be str")

        if not self.reasoning_id.strip():
            raise ValueError("reasoning_id must not be empty")


class OperationalReasoningEngine:
    """
    Operational reasoning layer for SAHIBEX.

    Pipeline:

        User Input
            ↓
        ReasoningEngine
            ↓
        Intent / Action / Permission / Verification
            ↓
        OperationalModelIntegration
            ↓
        ModelGateway
            ↓
        Model Response

    Protected or unverified requests are stopped before
    the model execution stage.

    This layer does not:

    - execute tools
    - execute shell commands
    - access external systems
    - grant permissions
    - override the constitution
    - execute protected actions
    """

    def __init__(
        self,
        *,
        reasoning_engine: ReasoningEngine | None = None,
        model_integration: OperationalModelIntegration,
    ) -> None:
        self.reasoning_engine = (
            reasoning_engine
            if reasoning_engine is not None
            else ReasoningEngine()
        )
        self.reasoning_coordinator = ReasoningCoordinator()

        if not isinstance(
            model_integration,
            OperationalModelIntegration,
        ):
            raise TypeError(
                "model_integration must be "
                "OperationalModelIntegration"
            )

        self.model_integration = model_integration

    def process(
        self,
        *,
        user_input: str,
        provider: str,
    ) -> OperationalReasoningResult:
        if not isinstance(user_input, str):
            raise TypeError("user_input must be str")

        if not user_input.strip():
            raise ValueError(
                "user_input must not be empty"
            )

        if not isinstance(provider, str):
            raise TypeError("provider must be str")

        if not provider.strip():
            raise ValueError(
                "provider must not be empty"
            )

        text = user_input.strip()
        selected_provider = provider.strip()

        reasoning = self.reasoning_engine.analyze(text)

        verification_status = str(
            reasoning.metadata.get(
                "verification",
                "UNKNOWN",
            )
        )

        if not reasoning.success:
            return OperationalReasoningResult(
                success=False,
                user_input=text,
                intent=reasoning.intent,
                action=reasoning.action,
                reasoning_response=reasoning.response,
                model_response="",
                model_provider=selected_provider,
                model="not_called",
                requires_confirmation=(
                    reasoning.requires_confirmation
                ),
                verification_status=verification_status,
            )

        if verification_status != "VERIFIED":
            return OperationalReasoningResult(
                success=False,
                user_input=text,
                intent=reasoning.intent,
                action=reasoning.action,
                reasoning_response=reasoning.response,
                model_response="",
                model_provider=selected_provider,
                model="not_called",
                requires_confirmation=(
                    reasoning.requires_confirmation
                ),
                verification_status=verification_status,
            )

        structured_reasoning = self.reasoning_coordinator.assess(
            goal=text,
            intent=reasoning.intent,
            confidence=reasoning.confidence,
            quality_score=1.0 if verification_status == "VERIFIED" else 0.0,
            ambiguous=reasoning.confidence < 0.50,
            prior_context=reasoning.metadata.get("context"),
        )
        structured_reasoning = self.reasoning_coordinator.verify(structured_reasoning)

        if reasoning.requires_confirmation:
            return OperationalReasoningResult(
                success=False,
                user_input=text,
                intent=reasoning.intent,
                action=reasoning.action,
                reasoning_response=reasoning.response,
                model_response="",
                model_provider=selected_provider,
                model="not_called",
                requires_confirmation=True,
                verification_status=verification_status,
            )

        model_prompt = (
            "Process the following user request as the "
            "reasoning model for SAHIBEX.\n\n"
            f"User request: {text}\n\n"
            f"Detected intent: {reasoning.intent}\n"
            f"Detected action: {reasoning.action}\n\n"
            "Provide a useful response. Do not claim that "
            "an external action was executed unless an "
            "execution result is explicitly supplied.\n\n"
            "Structured reasoning control signals: "
            f"strategy={structured_reasoning.selected_strategy}; "
            f"confidence={structured_reasoning.confidence}; "
            f"uncertainty={structured_reasoning.uncertainty}; "
            f"verified={structured_reasoning.verified}; "
            f"corrections={structured_reasoning.correction_count}."
        )

        model_result: OperationalModelResult = (
            self.model_integration.generate(
                objective=text,
                intent=reasoning.intent,
                prompt=model_prompt,
                provider=selected_provider,
            )
        )

        return OperationalReasoningResult(
            success=model_result.success,
            user_input=text,
            intent=reasoning.intent,
            action=reasoning.action,
            reasoning_response=reasoning.response,
            model_response=model_result.response_text,
            model_provider=model_result.provider,
            model=model_result.model,
            requires_confirmation=(
                reasoning.requires_confirmation
            ),
            verification_status=verification_status,
        )
