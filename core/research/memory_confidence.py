from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


MEMORY_CONFIDENCE_VERSION = "P2-MC-1"


class MemoryConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass(frozen=True)
class MemoryConfidenceInput:
    content: str
    existing_confidence: float
    verification_score: float
    provenance_score: float
    evidence_score: float
    source_reliability: float
    freshness_score: float
    conflict_score: float

    input_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise TypeError("content must be str.")

        if not self.content.strip():
            raise ValueError("content must not be empty.")

        for name in (
            "existing_confidence",
            "verification_score",
            "provenance_score",
            "evidence_score",
            "source_reliability",
            "freshness_score",
            "conflict_score",
        ):
            value = getattr(self, name)

            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"{name} must be numeric."
                )

            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(
                    f"{name} must be between 0.0 and 1.0."
                )

        if not isinstance(self.input_id, str):
            raise TypeError("input_id must be str.")

        if not self.input_id.strip():
            raise ValueError(
                "input_id must not be empty."
            )


@dataclass(frozen=True)
class MemoryConfidenceResult:
    level: MemoryConfidenceLevel
    confidence_score: float
    input_id: str
    reason: str

    result_id: str = field(
        default_factory=lambda: str(uuid4())
    )


class MemoryConfidenceEngine:
    """
    Canonical SAHIBEX Memory Confidence Engine.

    Assesses confidence in a stored memory using existing
    confidence, verification, provenance, evidence,
    source reliability, freshness, and conflict signals.

    This engine does NOT:
    - declare a memory true
    - modify memory
    - verify evidence itself
    - resolve conflicts
    - delete memory
    - execute actions
    - grant permissions
    - access credentials
    - modify the Constitution
    """

    VERSION = MEMORY_CONFIDENCE_VERSION

    EXISTING_CONFIDENCE_WEIGHT = 0.20
    VERIFICATION_WEIGHT = 0.25
    PROVENANCE_WEIGHT = 0.15
    EVIDENCE_WEIGHT = 0.15
    SOURCE_WEIGHT = 0.10
    FRESHNESS_WEIGHT = 0.10
    CONFLICT_WEIGHT = 0.05

    VERY_HIGH_THRESHOLD = 0.85
    HIGH_THRESHOLD = 0.65
    MEDIUM_THRESHOLD = 0.40

    def assess(
        self,
        confidence_input: MemoryConfidenceInput,
    ) -> MemoryConfidenceResult:
        if not isinstance(
            confidence_input,
            MemoryConfidenceInput,
        ):
            raise TypeError(
                "confidence_input must be "
                "MemoryConfidenceInput."
            )

        score = (
            confidence_input.existing_confidence
            * self.EXISTING_CONFIDENCE_WEIGHT
            + confidence_input.verification_score
            * self.VERIFICATION_WEIGHT
            + confidence_input.provenance_score
            * self.PROVENANCE_WEIGHT
            + confidence_input.evidence_score
            * self.EVIDENCE_WEIGHT
            + confidence_input.source_reliability
            * self.SOURCE_WEIGHT
            + confidence_input.freshness_score
            * self.FRESHNESS_WEIGHT
            + confidence_input.conflict_score
            * self.CONFLICT_WEIGHT
        )

        score = round(score, 6)

        if score >= self.VERY_HIGH_THRESHOLD:
            level = MemoryConfidenceLevel.VERY_HIGH
            reason = (
                "Memory has very high confidence based on "
                "its available verification and evidence signals."
            )

        elif score >= self.HIGH_THRESHOLD:
            level = MemoryConfidenceLevel.HIGH
            reason = (
                "Memory has high confidence based on "
                "its available supporting signals."
            )

        elif score >= self.MEDIUM_THRESHOLD:
            level = MemoryConfidenceLevel.MEDIUM
            reason = (
                "Memory has moderate confidence and may "
                "require additional verification for critical use."
            )

        else:
            level = MemoryConfidenceLevel.LOW
            reason = (
                "Memory has low confidence and should not "
                "be treated as strongly established information."
            )

        return MemoryConfidenceResult(
            level=level,
            confidence_score=score,
            input_id=confidence_input.input_id,
            reason=reason,
        )
