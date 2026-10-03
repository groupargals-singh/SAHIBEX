from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class MasterBrainIntelligenceResult:
    """
    Aggregated context result for the master brain.

    This object combines already-prepared context from intent,
    specialist brain, memory, knowledge, tools, multimodal
    processing, verification, trust, and permission systems.

    It does not execute actions or grant permissions.
    """

    success: bool
    intent: str
    brain_id: str
    memory_ids: list[str]
    knowledge_ids: list[str]
    tool_name: str
    modalities: list[str]
    verification_id: str
    trust_status: str
    confidence: float
    allowed: bool
    requires_confirmation: bool
    summary: str
    intelligence_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")

        if not isinstance(self.intent, str):
            raise TypeError("intent must be a string.")
        if not self.intent.strip():
            raise ValueError(
                "intent must be a non-empty string."
            )

        if not isinstance(self.brain_id, str):
            raise TypeError("brain_id must be a string.")
        if not self.brain_id.strip():
            raise ValueError(
                "brain_id must be a non-empty string."
            )

        if not isinstance(self.memory_ids, list):
            raise TypeError("memory_ids must be a list.")
        if not self.memory_ids:
            raise ValueError(
                "memory_ids must contain at least one ID."
            )

        for memory_id in self.memory_ids:
            if not isinstance(memory_id, str):
                raise TypeError(
                    "every memory ID must be a string."
                )
            if not memory_id.strip():
                raise ValueError(
                    "memory IDs must not be empty."
                )

        if not isinstance(self.knowledge_ids, list):
            raise TypeError("knowledge_ids must be a list.")
        if not self.knowledge_ids:
            raise ValueError(
                "knowledge_ids must contain at least one ID."
            )

        for knowledge_id in self.knowledge_ids:
            if not isinstance(knowledge_id, str):
                raise TypeError(
                    "every knowledge ID must be a string."
                )
            if not knowledge_id.strip():
                raise ValueError(
                    "knowledge IDs must not be empty."
                )

        if not isinstance(self.tool_name, str):
            raise TypeError("tool_name must be a string.")
        if not self.tool_name.strip():
            raise ValueError(
                "tool_name must be a non-empty string."
            )

        if not isinstance(self.modalities, list):
            raise TypeError("modalities must be a list.")
        if not self.modalities:
            raise ValueError(
                "modalities must contain at least one modality."
            )

        for modality in self.modalities:
            if not isinstance(modality, str):
                raise TypeError(
                    "every modality must be a string."
                )
            if not modality.strip():
                raise ValueError(
                    "modalities must not contain empty values."
                )

        if not isinstance(self.verification_id, str):
            raise TypeError(
                "verification_id must be a string."
            )
        if not self.verification_id.strip():
            raise ValueError(
                "verification_id must be a non-empty string."
            )

        if not isinstance(self.trust_status, str):
            raise TypeError(
                "trust_status must be a string."
            )
        if not self.trust_status.strip():
            raise ValueError(
                "trust_status must be a non-empty string."
            )

        if not isinstance(self.confidence, (int, float)):
            raise TypeError(
                "confidence must be a number."
            )

        if isinstance(self.confidence, bool):
            raise TypeError(
                "confidence must be a number."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if not isinstance(self.allowed, bool):
            raise TypeError("allowed must be a boolean.")

        if not isinstance(
            self.requires_confirmation,
            bool,
        ):
            raise TypeError(
                "requires_confirmation must be a boolean."
            )

        if not isinstance(self.summary, str):
            raise TypeError("summary must be a string.")
        if not self.summary.strip():
            raise ValueError(
                "summary must be a non-empty string."
            )

        if (
            not isinstance(self.intelligence_id, str)
            or not self.intelligence_id.strip()
        ):
            raise ValueError(
                "intelligence_id must be a non-empty string."
            )


class MasterBrainIntelligence:
    """
    Contract-level master brain intelligence aggregation.

    This layer normalizes and aggregates context that has already
    been prepared by other subsystems.

    It does not:
    - grant permissions
    - execute tools
    - execute actions
    - override the constitution
    - modify trust decisions
    """

    def aggregate(
        self,
        *,
        intent: str,
        brain_id: str,
        memory_ids: list[str],
        knowledge_ids: list[str],
        tool_name: str,
        modalities: list[str],
        verification_id: str,
        trust_status: str,
        confidence: float,
        allowed: bool,
        requires_confirmation: bool,
        summary: str,
    ) -> MasterBrainIntelligenceResult:
        if not isinstance(intent, str):
            raise TypeError("intent must be a string.")
        normalized_intent = intent.strip().lower()
        if not normalized_intent:
            raise ValueError(
                "intent must be a non-empty string."
            )

        if not isinstance(brain_id, str):
            raise TypeError("brain_id must be a string.")
        normalized_brain_id = brain_id.strip()
        if not normalized_brain_id:
            raise ValueError(
                "brain_id must be a non-empty string."
            )

        if not isinstance(memory_ids, list):
            raise TypeError("memory_ids must be a list.")
        if not memory_ids:
            raise ValueError(
                "memory_ids must contain at least one ID."
            )

        normalized_memory_ids: list[str] = []
        for memory_id in memory_ids:
            if not isinstance(memory_id, str):
                raise TypeError(
                    "every memory ID must be a string."
                )
            normalized = memory_id.strip()
            if not normalized:
                raise ValueError(
                    "memory IDs must not be empty."
                )
            if normalized not in normalized_memory_ids:
                normalized_memory_ids.append(normalized)

        if not isinstance(knowledge_ids, list):
            raise TypeError("knowledge_ids must be a list.")
        if not knowledge_ids:
            raise ValueError(
                "knowledge_ids must contain at least one ID."
            )

        normalized_knowledge_ids: list[str] = []
        for knowledge_id in knowledge_ids:
            if not isinstance(knowledge_id, str):
                raise TypeError(
                    "every knowledge ID must be a string."
                )
            normalized = knowledge_id.strip()
            if not normalized:
                raise ValueError(
                    "knowledge IDs must not be empty."
                )
            if normalized not in normalized_knowledge_ids:
                normalized_knowledge_ids.append(normalized)

        if not isinstance(tool_name, str):
            raise TypeError("tool_name must be a string.")
        normalized_tool_name = tool_name.strip()
        if not normalized_tool_name:
            raise ValueError(
                "tool_name must be a non-empty string."
            )

        if not isinstance(modalities, list):
            raise TypeError("modalities must be a list.")
        if not modalities:
            raise ValueError(
                "modalities must contain at least one modality."
            )

        normalized_modalities: list[str] = []
        for modality in modalities:
            if not isinstance(modality, str):
                raise TypeError(
                    "every modality must be a string."
                )
            normalized = modality.strip().lower()
            if not normalized:
                raise ValueError(
                    "modalities must not contain empty values."
                )
            if normalized not in normalized_modalities:
                normalized_modalities.append(normalized)

        if not isinstance(verification_id, str):
            raise TypeError(
                "verification_id must be a string."
            )
        normalized_verification_id = verification_id.strip()
        if not normalized_verification_id:
            raise ValueError(
                "verification_id must be a non-empty string."
            )

        if not isinstance(trust_status, str):
            raise TypeError(
                "trust_status must be a string."
            )
        normalized_trust_status = trust_status.strip().lower()
        if not normalized_trust_status:
            raise ValueError(
                "trust_status must be a non-empty string."
            )

        if not isinstance(confidence, (int, float)):
            raise TypeError(
                "confidence must be a number."
            )
        if isinstance(confidence, bool):
            raise TypeError(
                "confidence must be a number."
            )
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if not isinstance(allowed, bool):
            raise TypeError(
                "allowed must be a boolean."
            )

        if not isinstance(
            requires_confirmation,
            bool,
        ):
            raise TypeError(
                "requires_confirmation must be a boolean."
            )

        if not isinstance(summary, str):
            raise TypeError("summary must be a string.")
        normalized_summary = summary.strip()
        if not normalized_summary:
            raise ValueError(
                "summary must be a non-empty string."
            )

        return MasterBrainIntelligenceResult(
            success=True,
            intent=normalized_intent,
            brain_id=normalized_brain_id,
            memory_ids=normalized_memory_ids,
            knowledge_ids=normalized_knowledge_ids,
            tool_name=normalized_tool_name,
            modalities=normalized_modalities,
            verification_id=normalized_verification_id,
            trust_status=normalized_trust_status,
            confidence=float(confidence),
            allowed=allowed,
            requires_confirmation=requires_confirmation,
            summary=normalized_summary,
        )
