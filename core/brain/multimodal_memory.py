from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class MultimodalMemoryReference:
    """
    Contract representing a multimodal reference prepared for memory.

    This layer only represents validated references.
    It does not write to persistent memory or modify existing memories.
    """

    input_id: str
    modality: str
    summary: str
    reference_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.input_id, str):
            raise TypeError("input_id must be a string.")

        if not self.input_id.strip():
            raise ValueError(
                "input_id must be a non-empty string."
            )

        if not isinstance(self.modality, str):
            raise TypeError("modality must be a string.")

        if not self.modality.strip():
            raise ValueError(
                "modality must be a non-empty string."
            )

        if not isinstance(self.summary, str):
            raise TypeError("summary must be a string.")

        if not self.summary.strip():
            raise ValueError(
                "summary must be a non-empty string."
            )

        if (
            not isinstance(self.reference_id, str)
            or not self.reference_id.strip()
        ):
            raise ValueError(
                "reference_id must be a non-empty string."
            )


class MultimodalMemoryIntegration:
    """
    Contract-level integration between multimodal inputs and memory.

    This class only creates validated memory references.
    It does not persist, delete, or modify memory records.
    """

    def create_reference(
        self,
        *,
        input_id: str,
        modality: str,
        summary: str,
    ) -> MultimodalMemoryReference:
        return MultimodalMemoryReference(
            input_id=input_id,
            modality=modality,
            summary=summary,
        )
