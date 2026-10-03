from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.research.agreement import (
    MultiSourceAgreementAssessment,
)
from core.research.evidence_strength import (
    EvidenceStrengthAssessment,
)
from core.research.freshness import (
    FreshnessAssessment,
    STATUS_INVALID,
    STATUS_UNKNOWN,
)
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)
from core.research.source_quality import (
    SourceQualityAssessment,
    assess_source_quality,
)


CONFIDENCE_VERSION = "6G-7"

SOURCE_RELIABILITY_WEIGHT = 0.20
SOURCE_QUALITY_WEIGHT = 0.15
EVIDENCE_STRENGTH_WEIGHT = 0.20
AGREEMENT_WEIGHT = 0.15
CONFLICT_WEIGHT = 0.15
FRESHNESS_WEIGHT = 0.15


STATUS_HIGH = "HIGH"
STATUS_MEDIUM = "MEDIUM"
STATUS_LOW = "LOW"
STATUS_UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True)
class ResearchConfidenceAssessment:
    """
    Transparent 6G-7 research-confidence assessment.

    This score represents confidence in the quality and
    consistency of the available research evidence.

    It is NOT:
        - a truth score
        - a probability that a claim is true
        - a guarantee of correctness
        - a replacement for verification
        - a replacement for conflict resolution
    """

    knowledge_id: str

    confidence_score: float

    source_reliability_score: float
    source_quality_score: float
    evidence_strength_score: float
    agreement_score: float
    conflict_score: float
    freshness_score: float

    conflict_count: int
    unresolved_conflict_count: int

    status: str

    version: str = CONFIDENCE_VERSION

    def __post_init__(self) -> None:
        scores = (
            self.confidence_score,
            self.source_reliability_score,
            self.source_quality_score,
            self.evidence_strength_score,
            self.agreement_score,
            self.conflict_score,
            self.freshness_score,
        )

        for value in scores:
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    "confidence scores must be between 0 and 1"
                )

        if self.conflict_count < 0:
            raise ValueError(
                "conflict_count cannot be negative"
            )

        if self.unresolved_conflict_count < 0:
            raise ValueError(
                "unresolved_conflict_count cannot be negative"
            )

        if (
            self.unresolved_conflict_count
            > self.conflict_count
        ):
            raise ValueError(
                "unresolved conflicts cannot exceed "
                "total conflicts"
            )

        valid_statuses = {
            STATUS_HIGH,
            STATUS_MEDIUM,
            STATUS_LOW,
            STATUS_UNCERTAIN,
        }

        if self.status not in valid_statuses:
            raise ValueError(
                f"invalid confidence status: {self.status}"
            )


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _linked_evidence(
    knowledge: KnowledgeCandidate,
    evidence_items: Iterable[Evidence],
) -> list[Evidence]:
    return [
        evidence
        for evidence in evidence_items
        if (
            isinstance(evidence, Evidence)
            and (evidence.metadata or {}).get("knowledge_id")
            == knowledge.knowledge_id
        )
    ]


def _linked_sources(
    evidence_items: list[Evidence],
    sources: Iterable[ResearchSource],
) -> list[ResearchSource]:
    source_map = {
        source.source_id: source
        for source in sources
        if isinstance(source, ResearchSource)
    }

    linked: list[ResearchSource] = []
    seen: set[str] = set()

    for evidence in evidence_items:
        source = source_map.get(evidence.source_id)

        if source is None:
            continue

        if source.source_id in seen:
            continue

        seen.add(source.source_id)
        linked.append(source)

    return linked


def _reliability_score(
    sources: list[ResearchSource],
) -> float:
    """
    Average reliability of distinct linked sources.

    Reliability comes from 6G-1 only.
    """

    if not sources:
        return 0.0

    values = [
        _clamp(source.reliability)
        for source in sources
    ]

    return sum(values) / len(values)


def _quality_score(
    sources: list[ResearchSource],
    quality_assessments: Iterable[
        SourceQualityAssessment
    ],
) -> float:
    """
    Average 6G-2 quality score of distinct linked sources.

    Quality is intentionally separate from reliability.
    """

    assessments = {
        assessment.source_id: assessment
        for assessment in quality_assessments
    }

    values: list[float] = []

    for source in sources:
        assessment = assessments.get(
            source.source_id
        )

        if assessment is None:
            assessment = assess_source_quality(
                source
            )

        values.append(
            _clamp(
                assessment.quality_score
            )
        )

    if not values:
        return 0.0

    return sum(values) / len(values)


def _evidence_strength_score(
    evidence_items: list[Evidence],
    evidence_assessments: Iterable[
        EvidenceStrengthAssessment
    ],
) -> float:
    """
    Average 6G-3 evidence-strength score.

    Missing assessments are treated conservatively as zero.
    """

    assessments = {
        assessment.evidence_id: assessment
        for assessment in evidence_assessments
    }

    values: list[float] = []

    for evidence in evidence_items:
        assessment = assessments.get(
            evidence.evidence_id
        )

        if assessment is None:
            continue

        values.append(
            _clamp(
                assessment.strength_score
            )
        )

    if not values:
        return 0.0

    return sum(values) / len(values)


def _agreement_score(
    knowledge_id: str,
    assessments: Iterable[
        MultiSourceAgreementAssessment
    ],
) -> float:
    for assessment in assessments:
        if assessment.knowledge_id != knowledge_id:
            continue

        return _clamp(
            assessment.agreement_score
        )

    return 0.0


def _conflict_metrics(
    knowledge_id: str,
    conflict_assessments: Iterable[object],
) -> tuple[int, int]:
    """
    Read 6G-5 conflict intelligence outcomes.

    A conflict is relevant when this knowledge candidate
    appears on either side of the conflict.

    Unknown objects are ignored safely.
    """

    total = 0
    unresolved = 0

    for assessment in conflict_assessments:
        first_id = getattr(
            assessment,
            "first_knowledge_id",
            None,
        )

        second_id = getattr(
            assessment,
            "second_knowledge_id",
            None,
        )

        if knowledge_id not in {
            first_id,
            second_id,
        }:
            continue

        total += 1

        if (
            getattr(
                assessment,
                "resolution_status",
                None,
            )
            == "UNRESOLVED"
        ):
            unresolved += 1

    return total, unresolved


def _conflict_score(
    conflict_count: int,
    unresolved_conflict_count: int,
) -> float:
    """
    Convert conflict state into a confidence signal.

    Rules:

        no conflict -> 1.00

        resolved conflicts only ->
            0.80

        unresolved conflicts ->
            confidence is progressively reduced

    The signal is deliberately conservative.
    """

    if conflict_count == 0:
        return 1.0

    if unresolved_conflict_count == 0:
        return 0.80

    unresolved_ratio = (
        unresolved_conflict_count
        / conflict_count
    )

    return _clamp(
        0.80
        * (1.0 - unresolved_ratio)
    )


def _freshness_score(
    sources: list[ResearchSource],
    freshness_assessments: Iterable[
        FreshnessAssessment
    ],
) -> float:
    """
    Average freshness across linked sources.

    UNKNOWN and INVALID timestamps do not receive
    positive freshness credit.
    """

    assessments = {
        assessment.source_id: assessment
        for assessment in freshness_assessments
    }

    values: list[float] = []

    for source in sources:
        assessment = assessments.get(
            source.source_id
        )

        if assessment is None:
            continue

        if assessment.status in {
            STATUS_UNKNOWN,
            STATUS_INVALID,
        }:
            values.append(0.0)
            continue

        values.append(
            _clamp(
                assessment.freshness_score
            )
        )

    if not values:
        return 0.0

    return sum(values) / len(values)


def _confidence_status(
    confidence_score: float,
    unresolved_conflict_count: int,
) -> str:
    """
    Convert the composite score into a descriptive status.

    An unresolved conflict prevents HIGH status.
    """

    if unresolved_conflict_count > 0:
        if confidence_score >= 0.60:
            return STATUS_MEDIUM
        return STATUS_UNCERTAIN

    if confidence_score >= 0.80:
        return STATUS_HIGH

    if confidence_score >= 0.60:
        return STATUS_MEDIUM

    if confidence_score >= 0.40:
        return STATUS_LOW

    return STATUS_UNCERTAIN


def assess_research_confidence(
    *,
    knowledge: KnowledgeCandidate,
    evidence_items: Iterable[Evidence] = (),
    sources: Iterable[ResearchSource] = (),
    evidence_assessments: Iterable[
        EvidenceStrengthAssessment
    ] = (),
    agreement_assessments: Iterable[
        MultiSourceAgreementAssessment
    ] = (),
    conflict_assessments: Iterable[object] = (),
    freshness_assessments: Iterable[
        FreshnessAssessment
    ] = (),
    quality_assessments: Iterable[
        SourceQualityAssessment
    ] = (),
) -> ResearchConfidenceAssessment:
    """
    Calculate the canonical 6G-7 research-confidence score.

    All inputs are observational.

    No research object is mutated.
    """

    if not isinstance(
        knowledge,
        KnowledgeCandidate,
    ):
        raise TypeError(
            "knowledge must be a KnowledgeCandidate"
        )

    evidence_list = _linked_evidence(
        knowledge,
        evidence_items,
    )

    source_list = _linked_sources(
        evidence_list,
        sources,
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

    quality_assessments = list(
        quality_assessments
    )

    reliability = _reliability_score(
        source_list
    )

    quality = _quality_score(
        source_list,
        quality_assessments,
    )

    evidence_strength = (
        _evidence_strength_score(
            evidence_list,
            evidence_assessments,
        )
    )

    agreement = _agreement_score(
        knowledge.knowledge_id,
        agreement_assessments,
    )

    conflict_count, unresolved_count = (
        _conflict_metrics(
            knowledge.knowledge_id,
            conflict_assessments,
        )
    )

    conflict = _conflict_score(
        conflict_count,
        unresolved_count,
    )

    freshness = _freshness_score(
        source_list,
        freshness_assessments,
    )

    composite = (
        reliability
        * SOURCE_RELIABILITY_WEIGHT
        + quality
        * SOURCE_QUALITY_WEIGHT
        + evidence_strength
        * EVIDENCE_STRENGTH_WEIGHT
        + agreement
        * AGREEMENT_WEIGHT
        + conflict
        * CONFLICT_WEIGHT
        + freshness
        * FRESHNESS_WEIGHT
    )

    composite = round(
        _clamp(composite),
        4,
    )

    status = _confidence_status(
        composite,
        unresolved_count,
    )

    return ResearchConfidenceAssessment(
        knowledge_id=knowledge.knowledge_id,
        confidence_score=composite,
        source_reliability_score=round(
            reliability,
            4,
        ),
        source_quality_score=round(
            quality,
            4,
        ),
        evidence_strength_score=round(
            evidence_strength,
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
        conflict_count=conflict_count,
        unresolved_conflict_count=(
            unresolved_count
        ),
        status=status,
    )


class ResearchConfidenceEngine:
    """
    Stateless 6G-7 confidence engine.

    The engine does not:
        - mutate knowledge
        - mutate evidence
        - mutate sources
        - resolve conflicts
        - modify verification state
        - make network requests
        - persist data
    """

    def assess(
        self,
        *,
        knowledge: KnowledgeCandidate,
        evidence_items: Iterable[Evidence] = (),
        sources: Iterable[ResearchSource] = (),
        evidence_assessments: Iterable[
            EvidenceStrengthAssessment
        ] = (),
        agreement_assessments: Iterable[
            MultiSourceAgreementAssessment
        ] = (),
        conflict_assessments: Iterable[object] = (),
        freshness_assessments: Iterable[
            FreshnessAssessment
        ] = (),
        quality_assessments: Iterable[
            SourceQualityAssessment
        ] = (),
    ) -> ResearchConfidenceAssessment:
        return assess_research_confidence(
            knowledge=knowledge,
            evidence_items=evidence_items,
            sources=sources,
            evidence_assessments=evidence_assessments,
            agreement_assessments=agreement_assessments,
            conflict_assessments=conflict_assessments,
            freshness_assessments=freshness_assessments,
            quality_assessments=quality_assessments,
        )
