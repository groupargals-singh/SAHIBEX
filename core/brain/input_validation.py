from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class InputValidationResult:
    """Read-only structural validation result for one incoming input."""

    valid: bool
    input_id: str
    modality: str
    source_id: str
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    validation_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.valid, bool):
            raise TypeError("valid must be a boolean.")
        for name, value in (
            ("input_id", self.input_id),
            ("modality", self.modality),
            ("source_id", self.source_id),
            ("validation_id", self.validation_id),
        ):
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string.")
            if not value.strip():
                raise ValueError(f"{name} must be non-empty.")
        if not isinstance(self.errors, tuple):
            raise TypeError("errors must be a tuple.")
        if not isinstance(self.warnings, tuple):
            raise TypeError("warnings must be a tuple.")


class InputValidationEngine:
    """Model-independent, read-only validation gate for incoming observations.

    Validation checks structure and safety of the input envelope only.
    It does not establish truth, grant permission, execute actions,
    access devices/network, or modify source systems.
    """

    SUPPORTED_MODALITIES = {
        "text", "voice", "image", "file", "web",
        "sensor", "telemetry", "multimodal", "child",
    }

    def validate(
        self,
        *,
        input_id: str,
        modality: str,
        content: object,
        source_id: str,
        timestamp: str,
        confidence: float,
        metadata: dict[str, object] | None = None,
    ) -> InputValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        if not isinstance(input_id, str) or not input_id.strip():
            errors.append("invalid_input_id")
        if not isinstance(modality, str) or not modality.strip():
            errors.append("invalid_modality")
        if isinstance(modality, str) and modality.strip().lower() not in self.SUPPORTED_MODALITIES:
            warnings.append("unknown_modality")

        if not isinstance(content, str):
            errors.append("content_must_be_string")
        elif not content.strip():
            errors.append("empty_content")

        if not isinstance(source_id, str) or not source_id.strip():
            errors.append("invalid_source_id")

        if not isinstance(timestamp, str) or not timestamp.strip():
            errors.append("invalid_timestamp")

        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
            errors.append("invalid_confidence")
        elif not 0.0 <= float(confidence) <= 1.0:
            errors.append("confidence_out_of_range")

        if metadata is not None and not isinstance(metadata, dict):
            errors.append("metadata_must_be_dictionary")

        return InputValidationResult(
            valid=not errors,
            input_id=input_id.strip() if isinstance(input_id, str) and input_id.strip() else "invalid",
            modality=modality.strip().lower() if isinstance(modality, str) and modality.strip() else "invalid",
            source_id=source_id.strip() if isinstance(source_id, str) and source_id.strip() else "invalid",
            errors=tuple(errors),
            warnings=tuple(warnings),
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
    def verifies_truth() -> bool:
        return False

    @staticmethod
    def modifies_sources() -> bool:
        return False
