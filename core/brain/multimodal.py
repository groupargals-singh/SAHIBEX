from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class InputModality(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    FILE = "file"
    CHILD = "child"

@dataclass(frozen=True)
class MultimodalInput:
    """
    Immutable contract representing one multimodal input.

    Supported input modalities:
    - text
    - voice
    - image
    - file

    This is an input representation only.
    It does not execute models, access devices,
    perform file operations, or grant permissions.
    """

    modality: InputModality
    content: str
    input_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.modality, InputModality):
            raise TypeError("modality must be an InputModality.")

        if not isinstance(self.content, str):
            raise TypeError("content must be a string.")

        if not self.content.strip():
            raise ValueError("content must be a non-empty string.")

        if (
            not isinstance(self.input_id, str)
            or not self.input_id.strip()
        ):
            raise ValueError(
                "input_id must be a non-empty string."
            )
