from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class MultimodalMasterBrainResult:
    """
    Result of integrating multimodal context with the master brain.

    This object carries a validated reference to an existing
    multimodal result. It does not access devices, invoke models,
    execute actions, or grant permissions.
    """

    success: bool
    multimodal_result_id: str
    modalities: list[str]
    summary: str
    integration_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")

        if not isinstance(
            self.multimodal_result_id,
            str,
        ):
            raise TypeError(
                "multimodal_result_id must be a string."
            )

        if not self.multimodal_result_id.strip():
            raise ValueError(
                "multimodal_result_id must be a non-empty string."
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

        if not isinstance(self.summary, str):
            raise TypeError("summary must be a string.")

        if not self.summary.strip():
            raise ValueError(
                "summary must be a non-empty string."
            )

        if (
            not isinstance(self.integration_id, str)
            or not self.integration_id.strip()
        ):
            raise ValueError(
                "integration_id must be a non-empty string."
            )


class MultimodalMasterBrainIntegration:
    """
    Contract-level integration between multimodal processing
    and the master brain.

    This layer validates and normalizes multimodal references.
    It does not access microphones, cameras, models, external
    systems, protected actions, or permission mechanisms.
    """

    def integrate(
        self,
        *,
        multimodal_result_id: str,
        modalities: list[str],
        summary: str,
    ) -> MultimodalMasterBrainResult:
        if not isinstance(
            multimodal_result_id,
            str,
        ):
            raise TypeError(
                "multimodal_result_id must be a string."
            )

        normalized_result_id = (
            multimodal_result_id.strip()
        )

        if not normalized_result_id:
            raise ValueError(
                "multimodal_result_id must be a non-empty string."
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

        if not isinstance(summary, str):
            raise TypeError("summary must be a string.")

        if not summary.strip():
            raise ValueError(
                "summary must be a non-empty string."
            )

        return MultimodalMasterBrainResult(
            success=True,
            multimodal_result_id=normalized_result_id,
            modalities=normalized_modalities,
            summary=summary,
        )
