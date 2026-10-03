from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class VoiceInputFormat(str, Enum):
    TEXT = "text"
    AUDIO = "audio"


@dataclass(frozen=True)
class VoiceInput:
    """
    Contract representing one voice input.

    This layer only represents voice input data.
    It does not access a microphone, perform speech recognition,
    or execute any external action.
    """

    content: str
    input_format: VoiceInputFormat
    language: str
    input_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise TypeError("content must be a string.")

        if not self.content.strip():
            raise ValueError("content must be a non-empty string.")

        if not isinstance(self.input_format, VoiceInputFormat):
            raise TypeError(
                "input_format must be a VoiceInputFormat."
            )

        if not isinstance(self.language, str):
            raise TypeError("language must be a string.")

        if not self.language.strip():
            raise ValueError("language must be a non-empty string.")

        if not isinstance(self.input_id, str) or not self.input_id.strip():
            raise ValueError("input_id must be a non-empty string.")
