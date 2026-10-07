from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class SourceType(str, Enum):
    HUMAN = "human"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    WEB = "web"
    IMAGE = "image"
    VOICE = "voice"
    FILE = "file"
    CHILD = "child"
    SYSTEM_TELEMETRY = "system_telemetry"
    SENSOR = "sensor"
    EXTERNAL_MODEL = "external_model"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SourceIdentificationResult:
    input_id: str
    source_type: SourceType
    source_id: str
    origin: str
    provenance_reference: str | None = None
    identification_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.input_id, str) or not self.input_id.strip():
            raise ValueError("input_id must be a non-empty string.")

        if not isinstance(self.source_type, SourceType):
            raise TypeError("source_type must be a SourceType.")

        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("source_id must be a non-empty string.")

        if not isinstance(self.origin, str) or not self.origin.strip():
            raise ValueError("origin must be a non-empty string.")

        if self.provenance_reference is not None:
            if not isinstance(self.provenance_reference, str):
                raise TypeError(
                    "provenance_reference must be a string or None."
                )
            if not self.provenance_reference.strip():
                raise ValueError(
                    "provenance_reference must not be empty."
                )

        if (
            not isinstance(self.identification_id, str)
            or not self.identification_id.strip()
        ):
            raise ValueError(
                "identification_id must be a non-empty string."
            )

    def summary(self) -> dict[str, object]:
        return {
            "identification_id": self.identification_id,
            "input_id": self.input_id,
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "origin": self.origin,
            "provenance_reference": self.provenance_reference,
        }


class SourceIdentificationEngine:
    """
    Identifies where an input originated.

    This layer does not:
    - judge source quality
    - determine truth
    - grant authority
    - execute actions
    - modify memory
    - modify knowledge
    """

    def identify(
        self,
        *,
        input_id: str,
        source_type: SourceType | str,
        source_id: str,
        origin: str | None = None,
        provenance_reference: str | None = None,
    ) -> SourceIdentificationResult:
        if not isinstance(input_id, str) or not input_id.strip():
            raise ValueError("input_id must be a non-empty string.")

        if isinstance(source_type, str):
            try:
                source_type = SourceType(source_type.strip().lower())
            except ValueError as exc:
                raise ValueError(
                    f"unknown source_type: {source_type}"
                ) from exc

        if not isinstance(source_type, SourceType):
            raise TypeError("source_type must be a SourceType.")

        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("source_id must be a non-empty string.")

        if origin is None:
            origin = source_type.value

        if not isinstance(origin, str) or not origin.strip():
            raise ValueError("origin must be a non-empty string.")

        return SourceIdentificationResult(
            input_id=input_id.strip(),
            source_type=source_type,
            source_id=source_id.strip(),
            origin=origin.strip(),
            provenance_reference=(
                provenance_reference.strip()
                if isinstance(provenance_reference, str)
                else provenance_reference
            ),
        )

    @staticmethod
    def is_read_only() -> bool:
        return True

    @staticmethod
    def judges_quality() -> bool:
        return False

    @staticmethod
    def determines_truth() -> bool:
        return False

    @staticmethod
    def grants_permission() -> bool:
        return False

    @staticmethod
    def executes_actions() -> bool:
        return False

    @staticmethod
    def modifies_memory() -> bool:
        return False

    @staticmethod
    def modifies_knowledge() -> bool:
        return False
