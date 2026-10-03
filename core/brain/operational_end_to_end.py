from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from core.brain.operational_brain import (
    OperationalBrain,
    OperationalBrainResult,
)
from core.brain.operational_memory_knowledge import (
    OperationalMemoryKnowledgeIntegration,
    OperationalMemoryKnowledgeResult,
)
from core.brain.operational_multimodal import (
    OperationalMultimodalIntegration,
    OperationalMultimodalResult,
)
from core.brain.operational_reasoning import (
    OperationalReasoningEngine,
    OperationalReasoningResult,
)
from core.brain.operational_verification import (
    OperationalVerificationRecovery,
    OperationalVerificationResult,
)
from core.brain.multimodal import MultimodalInput


@dataclass(frozen=True)
class OperationalEndToEndResult:
    success: bool
    objective: str
    intent: str
    brain: OperationalBrainResult
    retrieval: OperationalMemoryKnowledgeResult
    multimodal: OperationalMultimodalResult | None
    reasoning: OperationalReasoningResult | None
    verification: OperationalVerificationResult
    final_response: str
    status: str
    integration_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool.")

        if not isinstance(self.objective, str):
            raise TypeError("objective must be str.")
        if not self.objective.strip():
            raise ValueError("objective must not be empty.")

        if not isinstance(self.intent, str):
            raise TypeError("intent must be str.")
        if not self.intent.strip():
            raise ValueError("intent must not be empty.")

        if not isinstance(self.brain, OperationalBrainResult):
            raise TypeError("brain must be OperationalBrainResult.")

        if not isinstance(
            self.retrieval,
            OperationalMemoryKnowledgeResult,
        ):
            raise TypeError(
                "retrieval must be OperationalMemoryKnowledgeResult."
            )

        if self.multimodal is not None and not isinstance(
            self.multimodal,
            OperationalMultimodalResult,
        ):
            raise TypeError(
                "multimodal must be OperationalMultimodalResult or None."
            )

        if self.reasoning is not None and not isinstance(
            self.reasoning,
            OperationalReasoningResult,
        ):
            raise TypeError(
                "reasoning must be OperationalReasoningResult or None."
            )

        if not isinstance(
            self.verification,
            OperationalVerificationResult,
        ):
            raise TypeError(
                "verification must be OperationalVerificationResult."
            )

        if not isinstance(self.final_response, str):
            raise TypeError("final_response must be str.")

        if not isinstance(self.status, str):
            raise TypeError("status must be str.")
        if not self.status.strip():
            raise ValueError("status must not be empty.")

        if not isinstance(self.integration_id, str):
            raise TypeError("integration_id must be str.")
        if not self.integration_id.strip():
            raise ValueError("integration_id must not be empty.")


class OperationalEndToEndBrain:
    """
    End-to-end operational brain orchestration boundary.

    Pipeline:

        Objective
            ↓
        OperationalBrain
            ↓
        Memory / Knowledge Retrieval
            ↓
        Optional Multimodal Integration
            ↓
        Operational Reasoning
            ↓
        Operational Verification / Recovery
            ↓
        Final Operational Result

    This layer does NOT:

        - grant permissions
        - bypass the Constitution
        - execute protected actions directly
        - execute shell commands directly
        - access credentials
        - modify memory or knowledge
        - modify its own constitution
    """

    def __init__(
        self,
        *,
        operational_brain: OperationalBrain,
        memory_knowledge: OperationalMemoryKnowledgeIntegration,
        reasoning_engine: OperationalReasoningEngine,
        verification: OperationalVerificationRecovery,
        multimodal: OperationalMultimodalIntegration | None = None,
    ) -> None:
        if not isinstance(
            operational_brain,
            OperationalBrain,
        ):
            raise TypeError(
                "operational_brain must be OperationalBrain."
            )

        if not isinstance(
            memory_knowledge,
            OperationalMemoryKnowledgeIntegration,
        ):
            raise TypeError(
                "memory_knowledge must be "
                "OperationalMemoryKnowledgeIntegration."
            )

        if not isinstance(
            reasoning_engine,
            OperationalReasoningEngine,
        ):
            raise TypeError(
                "reasoning_engine must be OperationalReasoningEngine."
            )

        if not isinstance(
            verification,
            OperationalVerificationRecovery,
        ):
            raise TypeError(
                "verification must be "
                "OperationalVerificationRecovery."
            )

        if multimodal is not None and not isinstance(
            multimodal,
            OperationalMultimodalIntegration,
        ):
            raise TypeError(
                "multimodal must be "
                "OperationalMultimodalIntegration or None."
            )

        self.operational_brain = operational_brain
        self.memory_knowledge = memory_knowledge
        self.reasoning_engine = reasoning_engine
        self.verification = verification
        self.multimodal = multimodal

    def process(
        self,
        *,
        objective: str,
        intent: str,
        provider: str,
        inputs: list[MultimodalInput] | None = None,
    ) -> OperationalEndToEndResult:
        if not isinstance(objective, str):
            raise TypeError("objective must be str.")

        normalized_objective = objective.strip()

        if not normalized_objective:
            raise ValueError("objective must not be empty.")

        if not isinstance(intent, str):
            raise TypeError("intent must be str.")

        normalized_intent = intent.strip().lower()

        if not normalized_intent:
            raise ValueError("intent must not be empty.")

        if not isinstance(provider, str):
            raise TypeError("provider must be str.")

        normalized_provider = provider.strip()

        if not normalized_provider:
            raise ValueError("provider must not be empty.")

        if inputs is not None:
            if not isinstance(inputs, list):
                raise TypeError("inputs must be a list.")

            for item in inputs:
                if not isinstance(item, MultimodalInput):
                    raise TypeError(
                        "every input must be MultimodalInput."
                    )

        brain_result = self.operational_brain.process(
            objective=normalized_objective,
            intent=normalized_intent,
        )

        if not brain_result.success:
            verification = OperationalVerificationResult(
                success=False,
                verified=False,
                verification_status="FAILED",
                recovery_status="FAILED",
                attempts=1,
                retryable=False,
                reason="Operational brain rejected the objective.",
                result=None,
            )

            retrieval = self.memory_knowledge.retrieve(
                query=normalized_objective
            )

            return OperationalEndToEndResult(
                success=False,
                objective=normalized_objective,
                intent=normalized_intent,
                brain=brain_result,
                retrieval=retrieval,
                multimodal=None,
                reasoning=None,
                verification=verification,
                final_response="",
                status="BLOCKED",
            )

        retrieval = self.memory_knowledge.retrieve(
            query=normalized_objective
        )

        multimodal_result: OperationalMultimodalResult | None = None

        if inputs:
            if self.multimodal is None:
                verification = OperationalVerificationResult(
                    success=False,
                    verified=False,
                    verification_status="BLOCKED",
                    recovery_status="BLOCKED",
                    attempts=1,
                    retryable=False,
                    reason=(
                        "Multimodal inputs were supplied but "
                        "multimodal integration is not configured."
                    ),
                    result=None,
                )

                return OperationalEndToEndResult(
                    success=False,
                    objective=normalized_objective,
                    intent=normalized_intent,
                    brain=brain_result,
                    retrieval=retrieval,
                    multimodal=None,
                    reasoning=None,
                    verification=verification,
                    final_response="",
                    status="BLOCKED",
                )

            multimodal_result = self.multimodal.process(
                objective=normalized_objective,
                inputs=inputs,
                provider=normalized_provider,
            )

            if not multimodal_result.success:
                verification = OperationalVerificationResult(
                    success=False,
                    verified=False,
                    verification_status="FAILED",
                    recovery_status="FAILED",
                    attempts=1,
                    retryable=False,
                    reason=(
                        "Multimodal operational reasoning "
                        "did not complete successfully."
                    ),
                    result=None,
                )

                return OperationalEndToEndResult(
                    success=False,
                    objective=normalized_objective,
                    intent=normalized_intent,
                    brain=brain_result,
                    retrieval=retrieval,
                    multimodal=multimodal_result,
                    reasoning=multimodal_result.reasoning,
                    verification=verification,
                    final_response="",
                    status="FAILED",
                )

            reasoning = multimodal_result.reasoning

        else:
            reasoning = self.reasoning_engine.process(
                user_input=normalized_objective,
                provider=normalized_provider,
            )

        if reasoning is None:
            verification = OperationalVerificationResult(
                success=False,
                verified=False,
                verification_status="FAILED",
                recovery_status="FAILED",
                attempts=1,
                retryable=False,
                reason="No operational reasoning result was produced.",
                result=None,
            )

            return OperationalEndToEndResult(
                success=False,
                objective=normalized_objective,
                intent=normalized_intent,
                brain=brain_result,
                retrieval=retrieval,
                multimodal=multimodal_result,
                reasoning=None,
                verification=verification,
                final_response="",
                status="FAILED",
            )

        verification = self.verification.verify_reasoning(
            reasoning
        )

        if not verification.success or not verification.verified:
            return OperationalEndToEndResult(
                success=False,
                objective=normalized_objective,
                intent=normalized_intent,
                brain=brain_result,
                retrieval=retrieval,
                multimodal=multimodal_result,
                reasoning=reasoning,
                verification=verification,
                final_response="",
                status=verification.recovery_status,
            )

        final_response = str(verification.result)

        return OperationalEndToEndResult(
            success=True,
            objective=normalized_objective,
            intent=normalized_intent,
            brain=brain_result,
            retrieval=retrieval,
            multimodal=multimodal_result,
            reasoning=reasoning,
            verification=verification,
            final_response=final_response,
            status="COMPLETED",
        )
