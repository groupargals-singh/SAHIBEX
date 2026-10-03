from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from core.research.models import ResearchSource


SOURCE_QUALITY_VERSION = "6G-2"

PROVENANCE_WEIGHT = 0.25
AUTHORITY_WEIGHT = 0.25
METADATA_COMPLETENESS_WEIGHT = 0.25
ACQUISITION_INTEGRITY_WEIGHT = 0.25


@dataclass(frozen=True)
class SourceQualityAssessment:
    """
    Transparent source-quality assessment.

    This score describes source-quality characteristics only.
    It is not a truth score and does not replace reliability.
    """

    source_id: str
    quality_score: float
    provenance_score: float
    authority_score: float
    metadata_completeness_score: float
    acquisition_integrity_score: float
    version: str = SOURCE_QUALITY_VERSION

    def __post_init__(self) -> None:
        values = (
            self.quality_score,
            self.provenance_score,
            self.authority_score,
            self.metadata_completeness_score,
            self.acquisition_integrity_score,
        )

        for value in values:
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    "source quality scores must be between 0 and 1"
                )


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _text_present(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _provenance_score(source: ResearchSource) -> float:
    """
    Evaluate source identity/provenance integrity.

    No freshness or truth judgement is performed here.
    """
    score = 0.0

    if _text_present(source.source_id):
        score += 0.30

    if _text_present(source.title):
        score += 0.15

    if _text_present(source.locator):
        score += 0.30

    metadata = source.metadata

    if _text_present(metadata.get("provider")) or _text_present(
        metadata.get("provider_name")
    ):
        score += 0.15

    if _text_present(metadata.get("reliability_source")):
        score += 0.05

    if _text_present(metadata.get("reliability_version")):
        score += 0.05

    return _clamp(score)


def _authority_score(source: ResearchSource) -> float:
    """
    Assign a conservative authority characteristic based on source type.

    This is a source-type heuristic, not a truth verification system.
    """
    source_type = source.source_type.strip().lower()

    authority_by_type = {
        "document": 1.00,
        "api": 0.90,
        "rss": 0.80,
        "web": 0.70,
        "search": 0.50,
    }

    return authority_by_type.get(source_type, 0.40)


def _metadata_completeness_score(
    source: ResearchSource,
) -> float:
    """
    Measure completeness of useful source metadata.

    Freshness is intentionally excluded from this calculation.
    """
    checks = (
        _text_present(source.title),
        _text_present(source.locator),
        _text_present(source.publisher),
        _text_present(source.author),
        source.published_at is not None,
        _text_present(source.metadata.get("provider"))
        or _text_present(source.metadata.get("provider_name")),
        _text_present(source.metadata.get("content_type")),
        _text_present(source.metadata.get("reliability_source")),
    )

    return _clamp(
        sum(1 for item in checks if item) / len(checks)
    )


def _acquisition_integrity_score(
    source: ResearchSource,
) -> float:
    """
    Evaluate whether acquisition produced useful integrity signals.

    This does not evaluate whether the content is true.
    """
    metadata = source.metadata

    score = 0.0

    if _text_present(metadata.get("acquired_at")):
        score += 0.20

    if _text_present(metadata.get("content_hash")):
        score += 0.30

    content_bytes = metadata.get("content_bytes")
    if isinstance(content_bytes, int) and content_bytes > 0:
        score += 0.20

    if metadata.get("discovery_only") is False:
        score += 0.15

    if (
        metadata.get("content_is_full_document") is True
        or metadata.get("content_is_api_result") is True
        or metadata.get("content_is_feed_item") is True
    ):
        score += 0.15

    return _clamp(score)


def assess_source_quality(
    source: ResearchSource,
) -> SourceQualityAssessment:
    """
    Calculate the canonical 6G-2 source-quality assessment.
    """
    if not isinstance(source, ResearchSource):
        raise TypeError(
            "source must be a ResearchSource"
        )

    provenance = _provenance_score(source)
    authority = _authority_score(source)
    metadata_completeness = _metadata_completeness_score(
        source
    )
    acquisition_integrity = _acquisition_integrity_score(
        source
    )

    quality_score = (
        provenance * PROVENANCE_WEIGHT
        + authority * AUTHORITY_WEIGHT
        + metadata_completeness
        * METADATA_COMPLETENESS_WEIGHT
        + acquisition_integrity
        * ACQUISITION_INTEGRITY_WEIGHT
    )

    return SourceQualityAssessment(
        source_id=source.source_id,
        quality_score=round(quality_score, 4),
        provenance_score=round(provenance, 4),
        authority_score=round(authority, 4),
        metadata_completeness_score=round(
            metadata_completeness,
            4,
        ),
        acquisition_integrity_score=round(
            acquisition_integrity,
            4,
        ),
    )


def assess_source_quality_from_metadata(
    *,
    source_id: str,
    title: str,
    source_type: str,
    locator: str,
    publisher: str | None = None,
    author: str | None = None,
    published_at: Any = None,
    reliability: float = 0.0,
    metadata: Mapping[str, Any] | None = None,
) -> SourceQualityAssessment:
    """
    Convenience wrapper for callers that have source fields
    but have not yet constructed a ResearchSource.
    """
    source = ResearchSource(
        source_id=source_id,
        title=title,
        source_type=source_type,
        locator=locator,
        publisher=publisher,
        author=author,
        published_at=published_at,
        reliability=reliability,
        metadata=dict(metadata or {}),
    )

    return assess_source_quality(source)
