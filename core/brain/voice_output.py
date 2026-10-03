from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class VoiceOutputFormat(str, Enum):
    TEXT = "text"
    AUDIO = "audio"


@dataclass(frozen=True)
class VoiceOutput:
    """
    Contract representing one voice output.

    This layer only represents output data.
    It does not access speakers, perform text-to-speech,
    or execute any external action.
    """

    content: str
    output_format: VoiceOutputFormat
    language: str
    output_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise TypeError("content must be a string.")

        if not self.content.strip():
            raise ValueError("content must be a non-empty string.")

        if not isinstance(self.output_format, VoiceOutputFormat):
            raise TypeError(
                "output_format must be a VoiceOutputFormat."
            )

        if not isinstance(self.language, str):
            raise TypeError("language must be a string.")

        if not self.language.strip():
            raise ValueError("language must be a non-empty string.")

        if not isinstance(self.output_id, str) or not self.output_id.strip():
            raise ValueError("output_id must be a non-empty string.")
