from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class InputConfidenceLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass(frozen=True)
class InputConfidenceAssessment:
    """
    Cognitive confidence assessment for one normalized input.

    This is an assessment of input confidence, not truth probability.
    It does not replace verification or research confidence.
    """

    input_id: str
    confidence: float
    level: InputConfidenceLevel
    reason: str
    assessment_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.input_id, str):
            raise TypeError("input_id must be a string.")

        if not self.input_id.strip():
            raise ValueError(
                "input_id must be non-empty."
            )

        if not isinstance(self.confidence, (int, float)):
            raise TypeError(
                "confidence must be numeric."
            )

        if isinstance(self.confidence, bool):
            raise TypeError(
                "confidence must be numeric."
            )

        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if not isinstance(
            self.level,
            InputConfidenceLevel,
        ):
            raise TypeError(
                "level must be an InputConfidenceLevel."
            )

        if not isinstance(self.reason, str):
            raise TypeError(
                "reason must be a string."
            )

        if not self.reason.strip():
            raise ValueError(
                "reason must be non-empty."
            )

        if not isinstance(
            self.assessment_id,
            str,
        ):
            raise TypeError(
                "assessment_id must be a string."
            )

        if not self.assessment_id.strip():
            raise ValueError(
                "assessment_id must be non-empty."
            )


class InputConfidenceEngine:
    """
    Dedicated input-confidence assessment engine.

    It evaluates an already supplied input-confidence value.
    It does not claim the input is true and does not perform
    research or verification.
    """

    def assess(
        self,
        *,
        input_id: str,
        confidence: float,
    ) -> InputConfidenceAssessment:
        if not isinstance(input_id, str):
            raise TypeError(
                "input_id must be a string."
            )

        normalized_input_id = input_id.strip()

        if not normalized_input_id:
            raise ValueError(
                "input_id must be non-empty."
            )

        if not isinstance(confidence, (int, float)):
            raise TypeError(
                "confidence must be numeric."
            )

        if isinstance(confidence, bool):
            raise TypeError(
                "confidence must be numeric."
            )

        normalized_confidence = float(confidence)

        if not 0.0 <= normalized_confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if normalized_confidence >= 0.90:
            level = InputConfidenceLevel.VERY_HIGH
            reason = "Input confidence is very high."

        elif normalized_confidence >= 0.70:
            level = InputConfidenceLevel.HIGH
            reason = "Input confidence is high."

        elif normalized_confidence >= 0.40:
            level = InputConfidenceLevel.MEDIUM
            reason = "Input confidence is medium."

        elif normalized_confidence >= 0.20:
            level = InputConfidenceLevel.LOW
            reason = "Input confidence is low."

        else:
            level = InputConfidenceLevel.VERY_LOW
            reason = "Input confidence is very low."

        return InputConfidenceAssessment(
            input_id=normalized_input_id,
            confidence=normalized_confidence,
            level=level,
            reason=reason,
        )

    @staticmethod
    def is_truth_score() -> bool:
        return False

    @staticmethod
    def replaces_verification() -> bool:
        return False

    @staticmethod
    def replaces_research_confidence() -> bool:
        return False

    @staticmethod
    def grants_permission() -> bool:
        return False

    @staticmethod
    def executes_actions() -> bool:
        return False
