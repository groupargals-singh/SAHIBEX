from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping


SOURCE_RANKING_VERSION = "6G-8"

RELIABILITY_WEIGHT = 0.20
QUALITY_WEIGHT = 0.15
EVIDENCE_WEIGHT = 0.15
AGREEMENT_WEIGHT = 0.15
CONFLICT_WEIGHT = 0.10
FRESHNESS_WEIGHT = 0.10
CONFIDENCE_WEIGHT = 0.15


@dataclass(frozen=True)
class SourceRankingAssessment:
    source_id: str
    ranking_score: float

    reliability_score: float
    quality_score: float
    evidence_strength_score: float
    agreement_score: float
    conflict_score: float
    freshness_score: float
    confidence_score: float

    rank: int = 0
    version: str = SOURCE_RANKING_VERSION

    def __post_init__(self) -> None:
        scores = (
            self.ranking_score,
            self.reliability_score,
            self.quality_score,
            self.evidence_strength_score,
            self.agreement_score,
            self.conflict_score,
            self.freshness_score,
            self.confidence_score,
        )

        for value in scores:
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    "source ranking scores must be between 0 and 1"
                )

        if self.rank < 0:
            raise ValueError(
                "rank must be zero or greater"
            )


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _safe_score(value: object) -> float:
    try:
        return _clamp(float(value))
    except (TypeError, ValueError):
        return 0.0


def _average(values: Iterable[float]) -> float:
    values = list(values)

    if not values:
        return 0.0

    return _clamp(
        sum(values) / len(values)
    )


def _get_value(
    item: object,
    attribute: str,
) -> float:
    value = getattr(item, attribute, None)

    if value is None and isinstance(item, Mapping):
        value = item.get(attribute)

    return _safe_score(value)


def _source_id(item: object) -> str:
    source_id = getattr(
        item,
        "source_id",
        None,
    )

    if source_id is None and isinstance(item, Mapping):
        source_id = item.get("source_id")

    if source_id is None:
        return ""

    return str(source_id)


def _reliability_score(
    source: object,
) -> float:
    return _get_value(
        source,
        "reliability",
    )


def _quality_score(
    source_id: str,
    quality_assessments: Iterable[object],
) -> float:
    matches = [
        item
        for item in quality_assessments
        if _source_id(item) == source_id
    ]

    return _average(
        _get_value(item, "quality_score")
        for item in matches
    )


def _evidence_strength_score(
    source_id: str,
    evidence_assessments: Iterable[object],
) -> float:
    matches = [
        item
        for item in evidence_assessments
        if _source_id(item) == source_id
    ]

    return _average(
        _get_value(item, "strength_score")
        for item in matches
    )


def _agreement_score(
    source_id: str,
    agreement_assessments: Iterable[object],
) -> float:
    matches = [
        item
        for item in agreement_assessments
        if source_id in getattr(
            item,
            "source_ids",
            [],
        )
    ]

    return _average(
        _get_value(item, "agreement_score")
        for item in matches
    )


def _conflict_score(
    source_id: str,
    conflict_assessments: Iterable[object],
    source_knowledge_ids: Iterable[str] = (),
) -> float:
    """
    Calculate the conflict contribution for a source.

    A source inherits conflict information through the
    knowledge candidates linked to that source.

    Resolved conflict:
        0.80

    Unresolved conflict:
        0.00

    No relevant conflict:
        1.00
    """

    knowledge_ids = set(source_knowledge_ids)
    relevant: list[float] = []

    for item in conflict_assessments:
        first_id = str(
            getattr(
                item,
                "first_knowledge_id",
                "",
            )
        )

        second_id = str(
            getattr(
                item,
                "second_knowledge_id",
                "",
            )
        )

        if not (
            first_id in knowledge_ids
            or second_id in knowledge_ids
        ):
            continue

        status = str(
            getattr(
                item,
                "resolution_status",
                "UNRESOLVED",
            )
        ).upper()

        if status == "RESOLVED":
            relevant.append(0.80)
        else:
            relevant.append(0.00)

    if not relevant:
        return 1.0

    return _average(relevant)


def _freshness_score(
    source_id: str,
    freshness_assessments: Iterable[object],
) -> float:
    matches = [
        item
        for item in freshness_assessments
        if _source_id(item) == source_id
    ]

    return _average(
        _get_value(item, "freshness_score")
        for item in matches
    )


def _confidence_score(
    source_id: str,
    confidence_assessments: Iterable[object],
    source_knowledge_map: Mapping[
        str,
        Iterable[str],
    ],
) -> float:
    knowledge_ids = set(
        source_knowledge_map.get(
            source_id,
            [],
        )
    )

    matches = [
        item
        for item in confidence_assessments
        if getattr(
            item,
            "knowledge_id",
            None,
        ) in knowledge_ids
    ]

    return _average(
        _get_value(
            item,
            "confidence_score",
        )
        for item in matches
    )


def calculate_source_ranking(
    *,
    sources: Iterable[object],
    quality_assessments: Iterable[object] = (),
    evidence_assessments: Iterable[object] = (),
    agreement_assessments: Iterable[object] = (),
    conflict_assessments: Iterable[object] = (),
    freshness_assessments: Iterable[object] = (),
    confidence_assessments: Iterable[object] = (),
    source_knowledge_map: Mapping[
        str,
        Iterable[str],
    ] | None = None,
) -> List[SourceRankingAssessment]:
    """
    Calculate deterministic source rankings.

    This function is observational only.

    It does not:
    - mutate sources
    - mutate evidence
    - mutate knowledge
    - change existing confidence
    - delete or modify conflicts
    - perform network access
    """

    source_knowledge_map = (
        source_knowledge_map or {}
    )

    sources = list(sources)
    quality_assessments = list(
        quality_assessments
    )
    evidence_assessments = list(
        evidence_assessments
    )
    agreement_assessments = list(
        agreement_assessments
    )
    conflict_assessments = list(
        conflict_assessments
    )
    freshness_assessments = list(
        freshness_assessments
    )
    confidence_assessments = list(
        confidence_assessments
    )

    assessments: List[
        SourceRankingAssessment
    ] = []

    for source in sources:
        source_id = _source_id(source)

        if not source_id:
            continue

        reliability = _reliability_score(
            source
        )

        quality = _quality_score(
            source_id,
            quality_assessments,
        )

        evidence = _evidence_strength_score(
            source_id,
            evidence_assessments,
        )

        agreement = _agreement_score(
            source_id,
            agreement_assessments,
        )

        conflict = _conflict_score(
            source_id,
            conflict_assessments,
            source_knowledge_map.get(
                source_id,
                [],
            ),
        )

        freshness = _freshness_score(
            source_id,
            freshness_assessments,
        )

        confidence = _confidence_score(
            source_id,
            confidence_assessments,
            source_knowledge_map,
        )

        ranking_score = (
            reliability
            * RELIABILITY_WEIGHT
            + quality
            * QUALITY_WEIGHT
            + evidence
            * EVIDENCE_WEIGHT
            + agreement
            * AGREEMENT_WEIGHT
            + conflict
            * CONFLICT_WEIGHT
            + freshness
            * FRESHNESS_WEIGHT
            + confidence
            * CONFIDENCE_WEIGHT
        )

        assessments.append(
            SourceRankingAssessment(
                source_id=source_id,
                ranking_score=round(
                    _clamp(ranking_score),
                    4,
                ),
                reliability_score=round(
                    reliability,
                    4,
                ),
                quality_score=round(
                    quality,
                    4,
                ),
                evidence_strength_score=round(
                    evidence,
                    4,
                ),
                agreement_score=round(
                    agreement,
                    4,
                ),
                conflict_score=round(
                    conflict,
                    4,
                ),
                freshness_score=round(
                    freshness,
                    4,
                ),
                confidence_score=round(
                    confidence,
                    4,
                ),
            )
        )

    assessments.sort(
        key=lambda item: (
            -item.ranking_score,
            item.source_id,
        )
    )

    ranked: List[
        SourceRankingAssessment
    ] = []

    for index, item in enumerate(
        assessments,
        start=1,
    ):
        ranked.append(
            SourceRankingAssessment(
                source_id=item.source_id,
                ranking_score=item.ranking_score,
                reliability_score=item.reliability_score,
                quality_score=item.quality_score,
                evidence_strength_score=(
                    item.evidence_strength_score
                ),
                agreement_score=item.agreement_score,
                conflict_score=item.conflict_score,
                freshness_score=item.freshness_score,
                confidence_score=item.confidence_score,
                rank=index,
                version=item.version,
            )
        )

    return ranked


class SourceRankingEngine:
    """
    Stateless 6G-8 source ranking engine.
    """

    def rank(
        self,
        *,
        sources: Iterable[object],
        quality_assessments: Iterable[object] = (),
        evidence_assessments: Iterable[object] = (),
        agreement_assessments: Iterable[object] = (),
        conflict_assessments: Iterable[object] = (),
        freshness_assessments: Iterable[object] = (),
        confidence_assessments: Iterable[object] = (),
        source_knowledge_map: Mapping[
            str,
            Iterable[str],
        ] | None = None,
    ) -> List[SourceRankingAssessment]:
        return calculate_source_ranking(
            sources=sources,
            quality_assessments=quality_assessments,
            evidence_assessments=evidence_assessments,
            agreement_assessments=agreement_assessments,
            conflict_assessments=conflict_assessments,
            freshness_assessments=freshness_assessments,
            confidence_assessments=confidence_assessments,
            source_knowledge_map=source_knowledge_map,
        )
