from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from core.brain.multimodal import InputModality, MultimodalInput


class FusionStatus(str, Enum):
    FUSED = "fused"
    SINGLE = "single"


@dataclass(frozen=True)
class FusionInput:
    """
    Validated observation prepared for cognitive multi-source fusion.

    This layer preserves provenance and confidence while remaining
    completely non-authoritative.

    It does not:
    - execute actions
    - access devices
    - access the network
    - grant permissions
    - modify memory
    - modify source systems
    """

    source_id: str
    modality: str
    content: str
    timestamp: str
    confidence: float
    input_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str):
            raise TypeError("source_id must be a string.")
        if not self.source_id.strip():
            raise ValueError("source_id must be non-empty.")

        if not isinstance(self.modality, str):
            raise TypeError("modality must be a string.")
        if not self.modality.strip():
            raise ValueError("modality must be non-empty.")

        if not isinstance(self.content, str):
            raise TypeError("content must be a string.")
        if not self.content.strip():
            raise ValueError("content must be non-empty.")

        if not isinstance(self.timestamp, str):
            raise TypeError("timestamp must be a string.")
        if not self.timestamp.strip():
            raise ValueError("timestamp must be non-empty.")

        if not isinstance(self.confidence, (int, float)):
            raise TypeError("confidence must be a number.")
        if isinstance(self.confidence, bool):
            raise TypeError("confidence must be a number.")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1.")

        if not isinstance(self.input_id, str):
            raise TypeError("input_id must be a string.")
        if not self.input_id.strip():
            raise ValueError("input_id must be non-empty.")


@dataclass(frozen=True)
class InputFusionResult:
    """
    Read-only result of cognitive multi-source input fusion.
    """

    fusion_id: str
    inputs: list[FusionInput]
    source_ids: list[str]
    modalities: list[str]
    confidence: float
    status: FusionStatus
    summary: str

    def __post_init__(self) -> None:
        if not isinstance(self.fusion_id, str):
            raise TypeError("fusion_id must be a string.")
        if not self.fusion_id.strip():
            raise ValueError("fusion_id must be non-empty.")

        if not isinstance(self.inputs, list):
            raise TypeError("inputs must be a list.")
        if not self.inputs:
            raise ValueError("inputs must contain at least one item.")

        for item in self.inputs:
            if not isinstance(item, FusionInput):
                raise TypeError(
                    "every fusion input must be a FusionInput."
                )

        if not isinstance(self.source_ids, list):
            raise TypeError("source_ids must be a list.")

        if not isinstance(self.modalities, list):
            raise TypeError("modalities must be a list.")

        if not isinstance(self.confidence, (int, float)):
            raise TypeError("confidence must be a number.")
        if isinstance(self.confidence, bool):
            raise TypeError("confidence must be a number.")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1.")

        if not isinstance(self.status, FusionStatus):
            raise TypeError("status must be a FusionStatus.")

        if not isinstance(self.summary, str):
            raise TypeError("summary must be a string.")
        if not self.summary.strip():
            raise ValueError("summary must be non-empty.")


class InputFusionEngine:
    """
    Cognitive multi-source input fusion.

    Responsibilities:
    - accept already validated input observations
    - preserve source identity
    - preserve modality
    - preserve timestamps
    - preserve confidence
    - remove duplicate input IDs
    - associate multiple observations into one fusion result

    This engine does NOT:
    - execute actions
    - access network/devices
    - grant permissions
    - modify memory
    - modify source systems
    - override Constitution/Human authority
    """

    def from_multimodal(
        self,
        inputs: list[MultimodalInput],
        *,
        source_id: str = "multimodal",
        timestamp: str | None = None,
        confidence: float = 1.0,
    ) -> InputFusionResult:
        if not isinstance(inputs, list):
            raise TypeError("inputs must be a list.")

        if not inputs:
            raise ValueError("inputs must contain at least one input.")

        for item in inputs:
            if not isinstance(item, MultimodalInput):
                raise TypeError(
                    "every input must be a MultimodalInput."
                )

        if not isinstance(source_id, str):
            raise TypeError("source_id must be a string.")

        normalized_source = source_id.strip()
        if not normalized_source:
            raise ValueError("source_id must be non-empty.")

        if timestamp is None:
            normalized_timestamp = datetime.now(
                timezone.utc
            ).isoformat()
        else:
            if not isinstance(timestamp, str):
                raise TypeError("timestamp must be a string.")
            normalized_timestamp = timestamp.strip()
            if not normalized_timestamp:
                raise ValueError("timestamp must be non-empty.")

        if not isinstance(confidence, (int, float)):
            raise TypeError("confidence must be a number.")
        if isinstance(confidence, bool):
            raise TypeError("confidence must be a number.")
        if not 0.0 <= float(confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1.")

        fusion_inputs: list[FusionInput] = []
        seen_ids: set[str] = set()

        for item in inputs:
            if item.input_id in seen_ids:
                continue

            seen_ids.add(item.input_id)

            fusion_inputs.append(
                FusionInput(
                    source_id=normalized_source,
                    modality=item.modality.value,
                    content=item.content.strip(),
                    timestamp=normalized_timestamp,
                    confidence=float(confidence),
                    input_id=item.input_id,
                )
            )

        return self.fuse(fusion_inputs)

    def fuse(
        self,
        inputs: list[FusionInput],
    ) -> InputFusionResult:
        if not isinstance(inputs, list):
            raise TypeError("inputs must be a list.")

        if not inputs:
            raise ValueError("inputs must contain at least one input.")

        unique_inputs: list[FusionInput] = []
        seen_ids: set[str] = set()

        for item in inputs:
            if not isinstance(item, FusionInput):
                raise TypeError(
                    "every input must be a FusionInput."
                )

            if item.input_id in seen_ids:
                continue

            seen_ids.add(item.input_id)
            unique_inputs.append(item)

        source_ids: list[str] = []
        modalities: list[str] = []

        for item in unique_inputs:
            if item.source_id not in source_ids:
                source_ids.append(item.source_id)

            if item.modality not in modalities:
                modalities.append(item.modality)

        confidence = sum(
            float(item.confidence)
            for item in unique_inputs
        ) / len(unique_inputs)

        status = (
            FusionStatus.FUSED
            if len(unique_inputs) > 1
            else FusionStatus.SINGLE
        )

        summary_parts = [
            f"[{item.modality}] {item.content}"
            for item in unique_inputs
        ]

        summary = " | ".join(summary_parts)

        return InputFusionResult(
            fusion_id=str(uuid4()),
            inputs=unique_inputs,
            source_ids=source_ids,
            modalities=modalities,
            confidence=confidence,
            status=status,
            summary=summary,
        )

    @staticmethod
    def is_read_only() -> bool:
        return True

    @staticmethod
    def grants_permission() -> bool:
        return False

    @staticmethod
    def executes_actions() -> bool:
        return False

    @staticmethod
    def modifies_memory() -> bool:
        return False

    @staticmethod
    def modifies_sources() -> bool:
        return False
