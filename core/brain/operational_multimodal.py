from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from core.brain.multimodal import MultimodalInput
from core.brain.multimodal_intelligence import MultimodalIntelligence
from core.brain.operational_model import OperationalModelIntegration
from core.brain.operational_reasoning import (
    OperationalReasoningEngine,
    OperationalReasoningResult,
)


@dataclass(frozen=True)
class OperationalMultimodalResult:
    """
    Runtime bridge between multimodal input and operational reasoning.

    This layer:
    - accepts validated multimodal inputs
    - normalizes their modalities
    - prepares a multimodal summary
    - sends the normalized request through OperationalReasoningEngine
    - returns the model-backed reasoning result

    This layer does not:
    - access microphones
    - access cameras
    - control speakers
    - execute tools
    - execute shell commands
    - grant permissions
    - bypass the constitution
    - perform protected actions
    """

    success: bool
    objective: str
    modalities: list[str]
    summary: str
    reasoning: OperationalReasoningResult | None
    integration_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool.")

        if not isinstance(self.objective, str):
            raise TypeError("objective must be str.")

        if not self.objective.strip():
            raise ValueError("objective must not be empty.")

        if not isinstance(self.modalities, list):
            raise TypeError("modalities must be a list.")

        if not self.modalities:
            raise ValueError("modalities must not be empty.")

        for modality in self.modalities:
            if not isinstance(modality, str):
                raise TypeError("every modality must be a string.")
            if not modality.strip():
                raise ValueError(
                    "modalities must not contain empty values."
                )

        if not isinstance(self.summary, str):
            raise TypeError("summary must be str.")

        if not self.summary.strip():
            raise ValueError("summary must not be empty.")

        if self.reasoning is not None and not isinstance(
            self.reasoning,
            OperationalReasoningResult,
        ):
            raise TypeError(
                "reasoning must be OperationalReasoningResult or None."
            )

        if not isinstance(self.integration_id, str):
            raise TypeError("integration_id must be str.")

        if not self.integration_id.strip():
            raise ValueError("integration_id must not be empty.")


class OperationalMultimodalIntegration:
    """
    Runtime multimodal integration for SAHIBEX.

    Flow:

        MultimodalInput objects
                    ↓
        MultimodalIntelligence
                    ↓
        Normalized multimodal context
                    ↓
        OperationalReasoningEngine
                    ↓
        OperationalModelIntegration
                    ↓
        ModelGateway

    The existing reasoning, verification, permission and
    constitution boundaries remain authoritative.
    """

    def __init__(
        self,
        *,
        multimodal_intelligence: MultimodalIntelligence | None = None,
        reasoning_engine: OperationalReasoningEngine,
    ) -> None:
        if multimodal_intelligence is not None and not isinstance(
            multimodal_intelligence,
            MultimodalIntelligence,
        ):
            raise TypeError(
                "multimodal_intelligence must be "
                "MultimodalIntelligence or None."
            )

        if not isinstance(
            reasoning_engine,
            OperationalReasoningEngine,
        ):
            raise TypeError(
                "reasoning_engine must be OperationalReasoningEngine."
            )

        self.multimodal_intelligence = (
            multimodal_intelligence
            if multimodal_intelligence is not None
            else MultimodalIntelligence()
        )
        self.reasoning_engine = reasoning_engine

    def process(
        self,
        *,
        objective: str,
        inputs: list[MultimodalInput],
        provider: str,
    ) -> OperationalMultimodalResult:
        if not isinstance(objective, str):
            raise TypeError("objective must be str.")

        normalized_objective = objective.strip()

        if not normalized_objective:
            raise ValueError("objective must not be empty.")

        if not isinstance(inputs, list):
            raise TypeError("inputs must be a list.")

        if not inputs:
            raise ValueError("inputs must contain at least one input.")

        for item in inputs:
            if not isinstance(item, MultimodalInput):
                raise TypeError(
                    "every input must be a MultimodalInput."
                )

        if not isinstance(provider, str):
            raise TypeError("provider must be str.")

        normalized_provider = provider.strip()

        if not normalized_provider:
            raise ValueError("provider must not be empty.")

        modalities = []
        content_parts = []

        for item in inputs:
            modality = item.modality.value

            if modality not in modalities:
                modalities.append(modality)

            content_parts.append(
                f"[{modality}] {item.content.strip()}"
            )

        summary = " | ".join(content_parts)

        multimodal_result = self.multimodal_intelligence.process(
            modalities=modalities,
            summary=summary,
        )

        if not multimodal_result.success:
            return OperationalMultimodalResult(
                success=False,
                objective=normalized_objective,
                modalities=modalities,
                summary=summary,
                reasoning=None,
            )

        reasoning_input = (
            f"{normalized_objective}\n\n"
            "Multimodal context:\n"
            f"{summary}"
        )

        reasoning = self.reasoning_engine.process(
            user_input=reasoning_input,
            provider=normalized_provider,
        )

        return OperationalMultimodalResult(
            success=reasoning.success,
            objective=normalized_objective,
            modalities=multimodal_result.modalities,
            summary=multimodal_result.summary,
            reasoning=reasoning,
        )
