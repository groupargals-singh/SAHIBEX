from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class NormalizedInput:
    """
    Common cognitive representation of an already prepared input.

    This layer standardizes representation only.

    It does not:
    - execute actions
    - access devices
    - access the network
    - grant permissions
    - modify source systems
    - change the semantic meaning of content
    - invent confidence
    """

    modality: str
    content: str
    source_id: str
    timestamp: str
    confidence: float
    input_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.modality, str):
            raise TypeError("modality must be a string.")

        if not self.modality.strip():
            raise ValueError("modality must be non-empty.")

        if not isinstance(self.content, str):
            raise TypeError("content must be a string.")

        if not self.content.strip():
            raise ValueError("content must be non-empty.")

        if not isinstance(self.source_id, str):
            raise TypeError("source_id must be a string.")

        if not self.source_id.strip():
            raise ValueError("source_id must be non-empty.")

        if not isinstance(self.timestamp, str):
            raise TypeError("timestamp must be a string.")

        if not self.timestamp.strip():
            raise ValueError("timestamp must be non-empty.")

        if not isinstance(self.confidence, (int, float)):
            raise TypeError("confidence must be numeric.")

        if isinstance(self.confidence, bool):
            raise TypeError("confidence must be numeric.")

        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if not isinstance(self.input_id, str):
            raise TypeError("input_id must be a string.")

        if not self.input_id.strip():
            raise ValueError("input_id must be non-empty.")

        if not isinstance(self.metadata, dict):
            raise TypeError("metadata must be a dictionary.")

    def normalized(self) -> "NormalizedInput":
        """
        Return a canonical representation without changing meaning.
        """
        return NormalizedInput(
            modality=self.modality.strip().lower(),
            content=" ".join(self.content.strip().split()),
            source_id=self.source_id.strip(),
            timestamp=self.timestamp.strip(),
            confidence=float(self.confidence),
            input_id=self.input_id.strip(),
            metadata=dict(self.metadata),
        )


class InputNormalizationEngine:
    """
    Model-independent cognitive input normalization.

    Converts already validated observations into one common
    representation for perception and downstream processing.
    """

    def normalize(
        self,
        *,
        modality: str,
        content: str,
        source_id: str,
        timestamp: str,
        confidence: float,
        input_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> NormalizedInput:
        if input_id is None:
            input_id = str(uuid4())

        if metadata is None:
            metadata = {}

        raw = NormalizedInput(
            modality=modality,
            content=content,
            source_id=source_id,
            timestamp=timestamp,
            confidence=confidence,
            input_id=input_id,
            metadata=dict(metadata),
        )

        return raw.normalized()

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
    def modifies_sources() -> bool:
        return False

    @staticmethod
    def changes_semantic_meaning() -> bool:
        return False
