from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class MultimodalIntelligenceResult:
    """
    Result of multimodal intelligence processing.

    This object represents a normalized multimodal
    understanding result only.

    It does not grant permissions or execute actions.
    """

    success: bool
    modalities: list[str]
    summary: str
    result_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")

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

        if not isinstance(self.summary, str):
            raise TypeError("summary must be a string.")

        if not self.summary.strip():
            raise ValueError(
                "summary must be a non-empty string."
            )

        if (
            not isinstance(self.result_id, str)
            or not self.result_id.strip()
        ):
            raise ValueError(
                "result_id must be a non-empty string."
            )


class MultimodalIntelligence:
    """
    Contract-level multimodal intelligence.

    This layer combines modality references into a
    normalized intelligence result.

    Supported modalities:
    - text
    - voice
    - image

    It does not access devices, models, credentials,
    permissions, or external systems.
    """

    _SUPPORTED_MODALITIES = {
        "text",
        "voice",
        "image",
    }

    def process(
        self,
        *,
        modalities: list[str],
        summary: str,
    ) -> MultimodalIntelligenceResult:
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

            if normalized not in self._SUPPORTED_MODALITIES:
                raise ValueError(
                    f"Unsupported modality: {modality}"
                )

            if normalized not in normalized_modalities:
                normalized_modalities.append(normalized)

        if not isinstance(summary, str):
            raise TypeError("summary must be a string.")

        if not summary.strip():
            raise ValueError(
                "summary must be a non-empty string."
            )

        return MultimodalIntelligenceResult(
            success=True,
            modalities=normalized_modalities,
            summary=summary,
        )
