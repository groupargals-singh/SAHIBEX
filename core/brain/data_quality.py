from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4


DATA_QUALITY_VERSION = "P1-33-1"


@dataclass(frozen=True)
class DataQualityAssessment:
    """
    Structural quality assessment for an input.

    This measures data quality characteristics only.
    It is NOT a truth, reliability, or authority score.
    """

    input_id: str
    quality_score: float
    completeness_score: float
    format_score: float
    consistency_score: float
    metadata_score: float
    freshness_score: float
    issues: tuple[str, ...] = ()
    assessment_id: str = field(default_factory=lambda: str(uuid4()))
    version: str = DATA_QUALITY_VERSION

    def __post_init__(self) -> None:
        scores = (
            self.quality_score,
            self.completeness_score,
            self.format_score,
            self.consistency_score,
            self.metadata_score,
            self.freshness_score,
        )

        for value in scores:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError("data quality scores must be numeric")
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(
                    "data quality scores must be between 0 and 1"
                )

        if not self.input_id.strip():
            raise ValueError("input_id cannot be empty")

    @property
    def acceptable(self) -> bool:
        return self.quality_score >= 0.50

    @property
    def high_quality(self) -> bool:
        return self.quality_score >= 0.80


class DataQualityEngine:
    """
    Evaluates structural quality of already-normalized input data.

    Security boundary:
    - read-only
    - no truth verification
    - no permission granting
    - no action execution
    - no source mutation
    """

    WEIGHTS = {
        "completeness": 0.25,
        "format": 0.20,
        "consistency": 0.20,
        "metadata": 0.15,
        "freshness": 0.20,
    }

    def assess(
        self,
        *,
        input_id: str,
        content: str,
        source_id: str,
        timestamp: str,
        confidence: float,
        metadata: Mapping[str, Any] | None = None,
        now: datetime | None = None,
    ) -> DataQualityAssessment:
        if not isinstance(input_id, str) or not input_id.strip():
            raise ValueError("input_id cannot be empty")

        if not isinstance(content, str):
            raise TypeError("content must be a string")

        if not isinstance(source_id, str):
            raise TypeError("source_id must be a string")

        if not isinstance(timestamp, str):
            raise TypeError("timestamp must be a string")

        if (
            not isinstance(confidence, (int, float))
            or isinstance(confidence, bool)
        ):
            raise TypeError("confidence must be numeric")

        if not 0.0 <= float(confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        metadata_dict = dict(metadata or {})
        issues: list[str] = []

        completeness = self._completeness(
            content=content,
            source_id=source_id,
            timestamp=timestamp,
            issues=issues,
        )

        format_score = self._format(
            input_id=input_id,
            timestamp=timestamp,
            confidence=float(confidence),
            issues=issues,
        )

        consistency = self._consistency(
            content=content,
            source_id=source_id,
            timestamp=timestamp,
            issues=issues,
        )

        metadata_score = self._metadata(
            metadata_dict,
            issues,
        )

        freshness = self._freshness(
            timestamp=timestamp,
            now=now,
            issues=issues,
        )

        quality = (
            completeness * self.WEIGHTS["completeness"]
            + format_score * self.WEIGHTS["format"]
            + consistency * self.WEIGHTS["consistency"]
            + metadata_score * self.WEIGHTS["metadata"]
            + freshness * self.WEIGHTS["freshness"]
        )

        return DataQualityAssessment(
            input_id=input_id,
            quality_score=round(quality, 4),
            completeness_score=round(completeness, 4),
            format_score=round(format_score, 4),
            consistency_score=round(consistency, 4),
            metadata_score=round(metadata_score, 4),
            freshness_score=round(freshness, 4),
            issues=tuple(issues),
        )

    @staticmethod
    def _completeness(
        *,
        content: str,
        source_id: str,
        timestamp: str,
        issues: list[str],
    ) -> float:
        checks = (
            bool(content.strip()),
            bool(source_id.strip()),
            bool(timestamp.strip()),
        )

        if not checks[0]:
            issues.append("missing_content")

        if not checks[1]:
            issues.append("missing_source_id")

        if not checks[2]:
            issues.append("missing_timestamp")

        return sum(checks) / len(checks)

    @staticmethod
    def _format(
        *,
        input_id: str,
        timestamp: str,
        confidence: float,
        issues: list[str],
    ) -> float:
        score = 1.0

        if not input_id.strip():
            score -= 0.4

        if not timestamp.strip():
            score -= 0.3

        if not 0.0 <= confidence <= 1.0:
            score -= 0.3

        if timestamp.strip():
            try:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                score -= 0.3
                issues.append("invalid_timestamp_format")

        return max(0.0, min(1.0, score))

    @staticmethod
    def _consistency(
        *,
        content: str,
        source_id: str,
        timestamp: str,
        issues: list[str],
    ) -> float:
        score = 1.0

        if content != content.strip():
            score -= 0.20
            issues.append("content_whitespace_inconsistency")

        if source_id != source_id.strip():
            score -= 0.20
            issues.append("source_id_whitespace_inconsistency")

        if timestamp != timestamp.strip():
            score -= 0.20
            issues.append("timestamp_whitespace_inconsistency")

        if not content.strip():
            score -= 0.40

        return max(0.0, min(1.0, score))

    @staticmethod
    def _metadata(
        metadata: Mapping[str, Any],
        issues: list[str],
    ) -> float:
        if not metadata:
            issues.append("metadata_missing")
            return 0.0

        useful_keys = (
            "modality",
            "source_type",
            "origin",
            "content_type",
            "language",
        )

        present = sum(
            1
            for key in useful_keys
            if key in metadata
            and metadata[key] is not None
            and str(metadata[key]).strip()
        )

        if present == 0:
            issues.append("metadata_without_quality_fields")

        return min(1.0, present / len(useful_keys))

    @staticmethod
    def _freshness(
        *,
        timestamp: str,
        now: datetime | None,
        issues: list[str],
    ) -> float:
        if not timestamp.strip():
            return 0.0

        try:
            observed = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00")
            )

            if observed.tzinfo is None:
                observed = observed.replace(tzinfo=timezone.utc)

            reference = now or datetime.now(timezone.utc)

            if reference.tzinfo is None:
                reference = reference.replace(tzinfo=timezone.utc)

            age_seconds = (reference - observed).total_seconds()

            if age_seconds < 0:
                issues.append("future_timestamp")
                return 0.50

            if age_seconds <= 300:
                return 1.0

            if age_seconds <= 3600:
                return 0.90

            if age_seconds <= 86400:
                return 0.70

            if age_seconds <= 604800:
                return 0.50

            return 0.30

        except ValueError:
            return 0.0

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
    def modifies_source() -> bool:
        return False
