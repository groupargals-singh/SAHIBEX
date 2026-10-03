from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from core.research.models import ResearchSource


FRESHNESS_VERSION = "6G-6"

STATUS_FRESH = "FRESH"
STATUS_AGING = "AGING"
STATUS_STALE = "STALE"
STATUS_UNKNOWN = "UNKNOWN"
STATUS_INVALID = "INVALID"


@dataclass(frozen=True)
class FreshnessAssessment:
    """
    Deterministic timestamp/freshness assessment.

    Freshness is a temporal signal only.

    It does NOT represent:
        - truth
        - source reliability
        - source quality
        - evidence strength
        - multi-source agreement
        - conflict resolution
    """

    source_id: str
    reference_time: datetime
    publication_time: Optional[datetime]
    accessed_time: datetime

    age_seconds: Optional[float]
    freshness_score: float
    status: str

    publication_before_access: Optional[bool]

    version: str = FRESHNESS_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str):
            raise TypeError(
                "source_id must be a string"
            )

        if not self.source_id.strip():
            raise ValueError(
                "source_id cannot be empty"
            )

        if self.reference_time.tzinfo is None:
            raise ValueError(
                "reference_time must be timezone-aware"
            )

        if self.accessed_time.tzinfo is None:
            raise ValueError(
                "accessed_time must be timezone-aware"
            )

        if (
            self.publication_time is not None
            and self.publication_time.tzinfo is None
        ):
            raise ValueError(
                "publication_time must be timezone-aware"
            )

        if not 0.0 <= self.freshness_score <= 1.0:
            raise ValueError(
                "freshness_score must be between 0 and 1"
            )

        valid_statuses = {
            STATUS_FRESH,
            STATUS_AGING,
            STATUS_STALE,
            STATUS_UNKNOWN,
            STATUS_INVALID,
        }

        if self.status not in valid_statuses:
            raise ValueError(
                f"invalid freshness status: {self.status}"
            )

        if self.age_seconds is not None:
            if self.age_seconds < 0:
                raise ValueError(
                    "age_seconds cannot be negative"
                )


def _ensure_aware(value: datetime, name: str) -> None:
    if value.tzinfo is None:
        raise ValueError(
            f"{name} must be timezone-aware"
        )


def _age_seconds(
    publication_time: datetime,
    reference_time: datetime,
) -> float:
    return (
        reference_time - publication_time
    ).total_seconds()


def _freshness_score(age_seconds: float) -> float:
    """
    Deterministic freshness score.

    0-1 day:
        1.00

    1-7 days:
        1.00 -> 0.80

    7-30 days:
        0.80 -> 0.50

    30-90 days:
        0.50 -> 0.20

    >90 days:
        0.20 -> 0.00
    """

    day = 24 * 60 * 60

    if age_seconds <= day:
        return 1.0

    if age_seconds <= 7 * day:
        progress = (
            age_seconds - day
        ) / (6 * day)

        return round(
            1.0 - (0.20 * progress),
            4,
        )

    if age_seconds <= 30 * day:
        progress = (
            age_seconds - 7 * day
        ) / (23 * day)

        return round(
            0.80 - (0.30 * progress),
            4,
        )

    if age_seconds <= 90 * day:
        progress = (
            age_seconds - 30 * day
        ) / (60 * day)

        return round(
            0.50 - (0.30 * progress),
            4,
        )

    progress = (
        age_seconds - 90 * day
    ) / (365 * day)

    return round(
        max(0.0, 0.20 * (1.0 - progress)),
        4,
    )


def _freshness_status(
    age_seconds: float,
) -> str:
    day = 24 * 60 * 60

    if age_seconds <= 7 * day:
        return STATUS_FRESH

    if age_seconds <= 90 * day:
        return STATUS_AGING

    return STATUS_STALE


def assess_source_freshness(
    source: ResearchSource,
    *,
    reference_time: datetime,
) -> FreshnessAssessment:
    """
    Assess freshness of one ResearchSource.

    Rules:

    1. published_at=None -> UNKNOWN.
    2. Naive timestamps -> invalid.
    3. Future publication -> INVALID.
    4. Publication after access -> INVALID.
    5. Otherwise calculate deterministic age and score.
    """

    if not isinstance(source, ResearchSource):
        raise TypeError(
            "source must be a ResearchSource"
        )

    _ensure_aware(
        reference_time,
        "reference_time",
    )

    publication_time = source.published_at
    accessed_time = source.accessed_at

    _ensure_aware(
        accessed_time,
        "source.accessed_at",
    )

    if publication_time is None:
        return FreshnessAssessment(
            source_id=source.source_id,
            reference_time=reference_time,
            publication_time=None,
            accessed_time=accessed_time,
            age_seconds=None,
            freshness_score=0.0,
            status=STATUS_UNKNOWN,
            publication_before_access=None,
        )

    _ensure_aware(
        publication_time,
        "source.published_at",
    )

    age_seconds = _age_seconds(
        publication_time,
        reference_time,
    )

    if age_seconds < 0:
        return FreshnessAssessment(
            source_id=source.source_id,
            reference_time=reference_time,
            publication_time=publication_time,
            accessed_time=accessed_time,
            age_seconds=None,
            freshness_score=0.0,
            status=STATUS_INVALID,
            publication_before_access=(
                publication_time <= accessed_time
            ),
        )

    publication_before_access = (
        publication_time <= accessed_time
    )

    if not publication_before_access:
        return FreshnessAssessment(
            source_id=source.source_id,
            reference_time=reference_time,
            publication_time=publication_time,
            accessed_time=accessed_time,
            age_seconds=None,
            freshness_score=0.0,
            status=STATUS_INVALID,
            publication_before_access=False,
        )

    score = _freshness_score(
        age_seconds
    )

    status = _freshness_status(
        age_seconds
    )

    return FreshnessAssessment(
        source_id=source.source_id,
        reference_time=reference_time,
        publication_time=publication_time,
        accessed_time=accessed_time,
        age_seconds=round(
            age_seconds,
            4,
        ),
        freshness_score=score,
        status=status,
        publication_before_access=True,
    )
