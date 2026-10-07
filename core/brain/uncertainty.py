from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


UNCERTAINTY_VERSION = "P1-34-1"


class UncertaintyLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass(frozen=True)
class UncertaintyAssessment:
    """
    Cognitive uncertainty assessment.

    This represents uncertainty in available input signals.
    It is NOT a truth score and does not determine whether
    a statement is true or false.
    """

    input_id: str
    uncertainty: float
    level: UncertaintyLevel
    reasons: tuple[str, ...] = ()
    confidence_signal: float = 0.0
    quality_signal: float = 0.0
    conflict_signal: float = 0.0
    assessment_id: str = field(default_factory=lambda: str(uuid4()))
    version: str = UNCERTAINTY_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.input_id, str):
            raise TypeError("input_id must be a string")

        if not self.input_id.strip():
            raise ValueError("input_id cannot be empty")

        values = (
            self.uncertainty,
            self.confidence_signal,
            self.quality_signal,
            self.conflict_signal,
        )

        for value in values:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError("uncertainty signals must be numeric")

            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(
                    "uncertainty signals must be between 0 and 1"
                )

        if not isinstance(self.level, UncertaintyLevel):
            raise TypeError("level must be an UncertaintyLevel")

        if not isinstance(self.reasons, tuple):
            raise TypeError("reasons must be a tuple")

    @property
    def uncertain(self) -> bool:
        return self.uncertainty >= 0.40

    @property
    def requires_verification(self) -> bool:
        return self.uncertainty >= 0.60


class UncertaintyEngine:
    """
    Converts existing cognitive quality/confidence signals into
    an explicit uncertainty assessment.

    This engine:
    - does not verify truth
    - does not perform research
    - does not resolve conflicts
    - does not grant permission
    - does not execute actions
    - does not modify source data
    """

    CONFIDENCE_WEIGHT = 0.35
    QUALITY_WEIGHT = 0.30
    CONFLICT_WEIGHT = 0.35

    def assess(
        self,
        *,
        input_id: str,
        confidence: float,
        quality_score: float,
        conflict_score: float = 0.0,
        missing_information: bool = False,
        ambiguous: bool = False,
        reasons: tuple[str, ...] = (),
    ) -> UncertaintyAssessment:
        self._validate_score("confidence", confidence)
        self._validate_score("quality_score", quality_score)
        self._validate_score("conflict_score", conflict_score)

        if not isinstance(missing_information, bool):
            raise TypeError("missing_information must be bool")

        if not isinstance(ambiguous, bool):
            raise TypeError("ambiguous must be bool")

        if not isinstance(reasons, tuple):
            raise TypeError("reasons must be a tuple")

        normalized_confidence = float(confidence)
        normalized_quality = float(quality_score)
        normalized_conflict = float(conflict_score)

        uncertainty = (
            (1.0 - normalized_confidence)
            * self.CONFIDENCE_WEIGHT
            + (1.0 - normalized_quality)
            * self.QUALITY_WEIGHT
            + normalized_conflict
            * self.CONFLICT_WEIGHT
        )

        reason_list = list(reasons)

        if missing_information:
            uncertainty += 0.10
            reason_list.append("missing_information")

        if ambiguous:
            uncertainty += 0.10
            reason_list.append("ambiguous_input")

        if normalized_confidence < 0.40:
            reason_list.append("low_input_confidence")

        if normalized_quality < 0.50:
            reason_list.append("low_data_quality")

        if normalized_conflict > 0.50:
            reason_list.append("conflicting_signals")

        uncertainty = max(0.0, min(1.0, uncertainty))

        level = self._level(uncertainty)

        return UncertaintyAssessment(
            input_id=input_id.strip(),
            uncertainty=round(uncertainty, 4),
            level=level,
            reasons=tuple(dict.fromkeys(reason_list)),
            confidence_signal=normalized_confidence,
            quality_signal=normalized_quality,
            conflict_signal=normalized_conflict,
        )

    @staticmethod
    def _validate_score(name: str, value: float) -> None:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError(f"{name} must be numeric")

        if not 0.0 <= float(value) <= 1.0:
            raise ValueError(f"{name} must be between 0 and 1")

    @staticmethod
    def _level(value: float) -> UncertaintyLevel:
        if value >= 0.80:
            return UncertaintyLevel.VERY_HIGH

        if value >= 0.60:
            return UncertaintyLevel.HIGH

        if value >= 0.40:
            return UncertaintyLevel.MEDIUM

        if value >= 0.20:
            return UncertaintyLevel.LOW

        return UncertaintyLevel.VERY_LOW

    @staticmethod
    def is_truth_score() -> bool:
        return False

    @staticmethod
    def performs_verification() -> bool:
        return False

    @staticmethod
    def performs_research() -> bool:
        return False

    @staticmethod
    def resolves_conflicts() -> bool:
        return False

    @staticmethod
    def grants_permission() -> bool:
        return False

    @staticmethod
    def executes_actions() -> bool:
        return False

    @staticmethod
    def modifies_source() -> bool:
        return False
