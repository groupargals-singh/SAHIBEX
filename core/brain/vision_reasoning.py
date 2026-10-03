from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class VisionReasoningResult:
    """
    Contract representing a vision observation prepared
    for reasoning.

    This layer only represents validated observation data.
    It does not access cameras, vision models, or execute actions.
    """

    vision_input_id: str
    observation: str
    result_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.vision_input_id, str):
            raise TypeError("vision_input_id must be a string.")

        if not self.vision_input_id.strip():
            raise ValueError(
                "vision_input_id must be a non-empty string."
            )

        if not isinstance(self.observation, str):
            raise TypeError("observation must be a string.")

        if not self.observation.strip():
            raise ValueError(
                "observation must be a non-empty string."
            )

        if not isinstance(self.result_id, str) or not self.result_id.strip():
            raise ValueError("result_id must be a non-empty string.")


class VisionReasoningIntegration:
    """
    Contract-level vision ↔ reasoning integration.

    This class validates and represents observations only.
    It does not perform actual computer vision or reasoning.
    """

    def analyze(
        self,
        *,
        vision_input_id: str,
        observation: str,
    ) -> VisionReasoningResult:
        return VisionReasoningResult(
            vision_input_id=vision_input_id,
            observation=observation,
        )
