from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class MultimodalContext:
    """
    Shared context for multimodal input references.

    This layer only stores input identifiers.
    It does not execute models, access devices,
    grant permissions, or perform external actions.
    """

    context_id: str = field(default_factory=lambda: str(uuid4()))
    inputs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.context_id, str) or not self.context_id.strip():
            raise ValueError("context_id must be a non-empty string.")

        if not isinstance(self.inputs, list):
            raise TypeError("inputs must be a list.")

        for input_id in self.inputs:
            if not isinstance(input_id, str):
                raise TypeError("every input ID must be a string.")

            if not input_id.strip():
                raise ValueError("input IDs must be non-empty strings.")

    def add_input(self, input_id: str) -> None:
        if not isinstance(input_id, str):
            raise TypeError("input_id must be a string.")

        if not input_id.strip():
            raise ValueError("input_id must be a non-empty string.")

        self.inputs.append(input_id)

    def remove_input(self, input_id: str) -> bool:
        if not isinstance(input_id, str):
            raise TypeError("input_id must be a string.")

        if input_id in self.inputs:
            self.inputs.remove(input_id)
            return True

        return False

    @property
    def input_count(self) -> int:
        return len(self.inputs)
