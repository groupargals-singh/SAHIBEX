from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from core.research.freshness import STATUS_UNKNOWN
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)


ANSWER_SYNTHESIS_VERSION = "6G-9"

SUPPORTED = "SUPPORTED"
MULTI_SOURCE_SUPPORTED = "MULTI_SOURCE_SUPPORTED"
CONFLICTED = "CONFLICTED"
STALE = "STALE"
LOW_CONFIDENCE = "LOW_CONFIDENCE"
UNCERTAIN = "UNCERTAIN"
UNVERIFIED = "UNVERIFIED"


@dataclass(frozen=True)
class AnswerClaimAssessment:
    knowledge_id: str
    statement: str

    status: str

    confidence_score: float
    source_count: int
    evidence_count: int

    agreement_score: float
    conflict_score: float
    freshness_score: float
    source_ranking_score: float

    verified: bool
    supported: bool

    explanation: str
    version: str = ANSWER_SYNTHESIS_VERSION


@dataclass(frozen=True)
class QualityAwareAnswer:
    answer: str
    claims: tuple[AnswerClaimAssessment, ...]

    supported_claims: tuple[str, ...]
    uncertain_claims: tuple[str, ...]
    conflicted_claims: tuple[str, ...]
    stale_claims: tuple[str, ...]

    overall_status: str
    overall_confidence: float

    version: str = ANSWER_SYNTHESIS_VERSION

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )


def _clamp(value: Any) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0

    return max(0.0, min(1.0, value))


def _safe_score(
    item: Any,
    field_name: str,
) -> float:
    return _clamp(
        getattr(item, field_name, 0.0)
    )


def _average(values: Iterable[float]) -> float:
    values = list(values)

    if not values:
        return 0.0

    return sum(values) / len(values)


def _knowledge_evidence(
    knowledge: KnowledgeCandidate,
    evidence_items: Sequence[Evidence],
) -> list[Evidence]:
    evidence_ids = set(knowledge.evidence)

    return [
        evidence
        for evidence in evidence_items
        if evidence.evidence_id in evidence_ids
    ]


def _knowledge_sources(
    evidence_items: Sequence[Evidence],
    sources: Sequence[ResearchSource],
) -> list[ResearchSource]:
    source_map = {
        source.source_id: source
        for source in sources
    }

    source_ids = {
        evidence.source_id
        for evidence in evidence_items
    }

    return [
        source_map[source_id]
        for source_id in sorted(source_ids)
        if source_id in source_map
    ]


def _find_assessment(
    assessments: Sequence[Any],
    knowledge_id: str,
) -> Any | None:
    for assessment in assessments:
        if (
            getattr(
                assessment,
                "knowledge_id",
                None,
            )
            == knowledge_id
        ):
            return assessment

    return None


def _source_ranking_for_knowledge(
    knowledge_id: str,
    evidence_items: Sequence[Evidence],
    source_ranking_assessments: Sequence[Any],
) -> float:
    linked_source_ids = {
        evidence.source_id
        for evidence in evidence_items
        if (
            (evidence.metadata or {}).get(
                "knowledge_id"
            )
            == knowledge_id
        )
    }

    scores = []

    for assessment in source_ranking_assessments:
        source_id = getattr(
            assessment,
            "source_id",
            None,
        )

        if source_id in linked_source_ids:
            scores.append(
                _safe_score(
                    assessment,
                    "ranking_score",
                )
            )

    return _average(scores)


def _evidence_strength_for_knowledge(
    evidence_items: Sequence[Evidence],
) -> float:
    scores = []

    for evidence in evidence_items:
        metadata = evidence.metadata or {}
        assessment = metadata.get(
            "evidence_strength"
        )

        if isinstance(assessment, Mapping):
            scores.append(
                _clamp(
                    assessment.get(
                        "strength_score",
                        0.0,
                    )
                )
            )

    return _average(scores)


def _status_for_claim(
    *,
    knowledge: KnowledgeCandidate,
    source_count: int,
    evidence_count: int,
    agreement_score: float,
    conflict_score: float,
    freshness_score: float,
    freshness_unknown: bool,
    freshness_sensitive: bool,
    confidence_score: float,
    source_ranking_score: float,
    unresolved_conflict_count: int,
) -> tuple[str, str]:

    if unresolved_conflict_count > 0:
        return (
            CONFLICTED,
            "Conflicting evidence remains unresolved.",
        )

    if not knowledge.verified:
        if confidence_score < 0.40:
            return (
                UNCERTAIN,
                "Knowledge is unverified and confidence is low.",
            )

        return (
            UNVERIFIED,
            "Knowledge has not passed verification.",
        )

    if freshness_sensitive and freshness_score < 0.40 and not freshness_unknown:
        return (
            STALE,
            "Supporting information has low freshness.",
        )

    if confidence_score < 0.60:
        return (
            LOW_CONFIDENCE,
            "Confidence is below the strong-support threshold.",
        )

    if source_count >= 2 and agreement_score >= 0.50:
        return (
            MULTI_SOURCE_SUPPORTED,
            "The claim is supported by multiple sources.",
        )

    if evidence_count > 0:
        return (
            SUPPORTED,
            "The claim has verified supporting evidence.",
        )

    return (
        UNCERTAIN,
        "No sufficient supporting evidence was found.",
    )


def assess_claim(
    *,
    knowledge: KnowledgeCandidate,
    evidence_items: Sequence[Evidence],
    sources: Sequence[ResearchSource],
    confidence_assessments: Sequence[Any] = (),
    agreement_assessments: Sequence[Any] = (),
    conflict_assessments: Sequence[Any] = (),
    freshness_assessments: Sequence[Any] = (),
    source_ranking_assessments: Sequence[Any] = (),
    freshness_sensitive: bool = True,
) -> AnswerClaimAssessment:

    linked_evidence = _knowledge_evidence(
        knowledge,
        evidence_items,
    )

    linked_sources = _knowledge_sources(
        linked_evidence,
        sources,
    )

    confidence = _find_assessment(
        confidence_assessments,
        knowledge.knowledge_id,
    )

    agreement = _find_assessment(
        agreement_assessments,
        knowledge.knowledge_id,
    )

    confidence_score = (
        _safe_score(
            confidence,
            "confidence_score",
        )
        if confidence is not None
        else _clamp(knowledge.confidence)
    )

    agreement_score = (
        _safe_score(
            agreement,
            "agreement_score",
        )
        if agreement is not None
        else 0.0
    )

    conflict_items = [
        item
        for item in conflict_assessments
        if (
            getattr(
                item,
                "first_knowledge_id",
                None,
            )
            == knowledge.knowledge_id
            or getattr(
                item,
                "second_knowledge_id",
                None,
            )
            == knowledge.knowledge_id
        )
    ]

    unresolved_conflicts = [
        item
        for item in conflict_items
        if getattr(
            item,
            "resolution_status",
            "",
        )
        == "UNRESOLVED"
    ]

    if not conflict_items:
        conflict_score = 1.0
    elif unresolved_conflicts:
        conflict_score = 0.0
    else:
        conflict_score = 0.80

    linked_source_ids = {
        source.source_id
        for source in linked_sources
    }

    freshness_scores = []
    linked_freshness_statuses = []

    for assessment in freshness_assessments:
        if getattr(assessment, "source_id", None) in linked_source_ids:
            freshness_scores.append(_safe_score(assessment, "freshness_score"))
            linked_freshness_statuses.append(str(getattr(assessment, "status", "")).upper())

    freshness_score = _average(freshness_scores)
    if not freshness_scores and linked_sources:
        freshness_score = 0.0

    # UNKNOWN publication date is not the same as a known stale source. For
    # stable facts, do not reject solely because a publisher omitted a date.
    # Time-sensitive live acceptance independently requires explicit dates.
    freshness_unknown = bool(linked_sources) and (
        (bool(linked_freshness_statuses) and all(status == STATUS_UNKNOWN for status in linked_freshness_statuses))
        or (not linked_freshness_statuses and all(source.published_at is None for source in linked_sources))
    )

    source_ranking_score = (
        _source_ranking_for_knowledge(
            knowledge_id=knowledge.knowledge_id,
            evidence_items=linked_evidence,
            source_ranking_assessments=(
                source_ranking_assessments
            ),
        )
    )

    if not source_ranking_assessments:
        source_ranking_score = 0.0

    status, explanation = _status_for_claim(
        knowledge=knowledge,
        source_count=len(linked_sources),
        evidence_count=len(linked_evidence),
        agreement_score=agreement_score,
        conflict_score=conflict_score,
        freshness_score=freshness_score,
        freshness_unknown=freshness_unknown,
        freshness_sensitive=freshness_sensitive,
        confidence_score=confidence_score,
        source_ranking_score=source_ranking_score,
        unresolved_conflict_count=len(
            unresolved_conflicts
        ),
    )

    supported = status in {
        SUPPORTED,
        MULTI_SOURCE_SUPPORTED,
    }

    return AnswerClaimAssessment(
        knowledge_id=knowledge.knowledge_id,
        statement=knowledge.statement,
        status=status,
        confidence_score=round(
            confidence_score,
            4,
        ),
        source_count=len(linked_sources),
        evidence_count=len(linked_evidence),
        agreement_score=round(
            agreement_score,
            4,
        ),
        conflict_score=round(
            conflict_score,
            4,
        ),
        freshness_score=round(
            freshness_score,
            4,
        ),
        source_ranking_score=round(
            source_ranking_score,
            4,
        ),
        verified=bool(
            knowledge.verified
        ),
        supported=supported,
        explanation=explanation,
    )


def _overall_status(
    claims: Sequence[AnswerClaimAssessment],
) -> str:
    if not claims:
        return UNCERTAIN

    if any(
        claim.status == CONFLICTED
        for claim in claims
    ):
        return CONFLICTED

    if any(
        claim.status == STALE
        for claim in claims
    ):
        return STALE

    if any(
        claim.status == UNCERTAIN
        for claim in claims
    ):
        return UNCERTAIN

    if any(
        claim.status == LOW_CONFIDENCE
        for claim in claims
    ):
        return LOW_CONFIDENCE

    if all(
        claim.status
        == MULTI_SOURCE_SUPPORTED
        for claim in claims
    ):
        return MULTI_SOURCE_SUPPORTED

    if any(
        claim.status
        == MULTI_SOURCE_SUPPORTED
        for claim in claims
    ):
        return MULTI_SOURCE_SUPPORTED

    if all(
        claim.status == SUPPORTED
        for claim in claims
    ):
        return SUPPORTED

    return UNVERIFIED


def synthesize_answer(
    *,
    knowledge_items: Sequence[KnowledgeCandidate],
    evidence_items: Sequence[Evidence],
    sources: Sequence[ResearchSource],
    confidence_assessments: Sequence[Any] = (),
    agreement_assessments: Sequence[Any] = (),
    conflict_assessments: Sequence[Any] = (),
    freshness_assessments: Sequence[Any] = (),
    source_ranking_assessments: Sequence[Any] = (),
    freshness_sensitive: bool = True,
) -> QualityAwareAnswer:

    claims = []

    for knowledge in knowledge_items:
        claims.append(
            assess_claim(
                knowledge=knowledge,
                evidence_items=evidence_items,
                sources=sources,
                confidence_assessments=(
                    confidence_assessments
                ),
                agreement_assessments=(
                    agreement_assessments
                ),
                conflict_assessments=(
                    conflict_assessments
                ),
                freshness_assessments=(
                    freshness_assessments
                ),
                source_ranking_assessments=(
                    source_ranking_assessments
                ),
                freshness_sensitive=freshness_sensitive,
            )
        )

    claims = tuple(claims)

    supported_claims = tuple(
        claim.statement
        for claim in claims
        if claim.supported
    )

    uncertain_claims = tuple(
        claim.statement
        for claim in claims
        if claim.status
        in {
            UNCERTAIN,
            UNVERIFIED,
            LOW_CONFIDENCE,
        }
    )

    conflicted_claims = tuple(
        claim.statement
        for claim in claims
        if claim.status == CONFLICTED
    )

    stale_claims = tuple(
        claim.statement
        for claim in claims
        if claim.status == STALE
    )

    overall_confidence = _average(
        claim.confidence_score
        for claim in claims
    )

    overall_status = _overall_status(
        claims
    )

    answer_lines = []

    for claim in claims:
        if claim.supported:
            answer_lines.append(
                claim.statement
            )
        elif claim.status == CONFLICTED:
            answer_lines.append(
                f"Unresolved conflict: "
                f"{claim.statement}"
            )
        elif claim.status == STALE:
            answer_lines.append(
                f"Stale/low-freshness information: "
                f"{claim.statement}"
            )
        else:
            answer_lines.append(
                f"Uncertain information: "
                f"{claim.statement}"
            )

    answer = "\n".join(
        answer_lines
    )

    return QualityAwareAnswer(
        answer=answer,
        claims=claims,
        supported_claims=supported_claims,
        uncertain_claims=uncertain_claims,
        conflicted_claims=conflicted_claims,
        stale_claims=stale_claims,
        overall_status=overall_status,
        overall_confidence=round(
            overall_confidence,
            4,
        ),
        metadata={
            "claim_count": len(claims),
            "supported_count": len(
                supported_claims
            ),
            "uncertain_count": len(
                uncertain_claims
            ),
            "conflicted_count": len(
                conflicted_claims
            ),
            "stale_count": len(
                stale_claims
            ),
        },
    )


class QualityAwareAnswerSynthesizer:
    """
    Stateless quality-aware answer synthesis engine.

    This component:
    - does not perform network access
    - does not mutate research objects
    - does not modify knowledge confidence
    - does not treat confidence as truth
    - does not silently resolve conflicts
    """

    def synthesize(
        self,
        *,
        knowledge_items: Sequence[KnowledgeCandidate],
        evidence_items: Sequence[Evidence],
        sources: Sequence[ResearchSource],
        confidence_assessments: Sequence[Any] = (),
        agreement_assessments: Sequence[Any] = (),
        conflict_assessments: Sequence[Any] = (),
        freshness_assessments: Sequence[Any] = (),
        source_ranking_assessments: Sequence[Any] = (),
        freshness_sensitive: bool = True,
    ) -> QualityAwareAnswer:

        return synthesize_answer(
            knowledge_items=knowledge_items,
            evidence_items=evidence_items,
            sources=sources,
            confidence_assessments=(
                confidence_assessments
            ),
            agreement_assessments=(
                agreement_assessments
            ),
            conflict_assessments=(
                conflict_assessments
            ),
            freshness_assessments=(
                freshness_assessments
            ),
            source_ranking_assessments=(
                source_ranking_assessments
            ),
            freshness_sensitive=freshness_sensitive,
        )
