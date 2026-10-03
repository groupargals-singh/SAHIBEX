from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class VisionInputFormat(str, Enum):
    IMAGE = "image"
    FRAME = "frame"


@dataclass(frozen=True)
class VisionInput:
    """
    Contract representing one vision input.

    This layer only represents vision input data.
    It does not access a camera, process images,
    or execute any external action.
    """

    content: str
    input_format: VisionInputFormat
    source: str
    input_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise TypeError("content must be a string.")

        if not self.content.strip():
            raise ValueError("content must be a non-empty string.")

        if not isinstance(self.input_format, VisionInputFormat):
            raise TypeError(
                "input_format must be a VisionInputFormat."
            )

        if not isinstance(self.source, str):
            raise TypeError("source must be a string.")

        if not self.source.strip():
            raise ValueError("source must be a non-empty string.")

        if not isinstance(self.input_id, str) or not self.input_id.strip():
            raise ValueError("input_id must be a non-empty string.")
