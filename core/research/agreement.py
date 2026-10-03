from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)


AGREEMENT_VERSION = "6G-4"


@dataclass(frozen=True)
class MultiSourceAgreementAssessment:
    """
    Measures agreement across distinct research sources.

    This is a source-agreement signal only.

    It does NOT represent:
        - truth
        - source reliability
        - source quality
        - evidence strength
        - conflict resolution
        - institutional independence
    """

    knowledge_id: str
    total_source_count: int
    supporting_source_count: int
    contradicting_source_count: int
    agreement_score: float
    version: str = AGREEMENT_VERSION

    def __post_init__(self) -> None:
        values = (
            self.agreement_score,
        )

        for value in values:
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    "agreement score must be between 0 and 1"
                )

        if self.total_source_count < 0:
            raise ValueError(
                "total_source_count cannot be negative"
            )

        if self.supporting_source_count < 0:
            raise ValueError(
                "supporting_source_count cannot be negative"
            )

        if self.contradicting_source_count < 0:
            raise ValueError(
                "contradicting_source_count cannot be negative"
            )


def _linked_evidence(
    knowledge: KnowledgeCandidate,
    evidence_items: Iterable[Evidence],
) -> list[Evidence]:
    """
    Return evidence explicitly linked to the knowledge candidate.
    """
    linked: list[Evidence] = []

    for evidence in evidence_items:
        metadata = evidence.metadata or {}

        if metadata.get("knowledge_id") != knowledge.knowledge_id:
            continue

        linked.append(evidence)

    return linked


def _source_ids(
    evidence_items: Iterable[Evidence],
) -> set[str]:
    """
    Count distinct source IDs only.

    Multiple evidence records from the same source count as
    one source.
    """
    return {
        evidence.source_id
        for evidence in evidence_items
        if isinstance(evidence.source_id, str)
        and evidence.source_id.strip()
    }


def _agreement_score(
    supporting_source_count: int,
    total_source_count: int,
) -> float:
    """
    Calculate agreement across distinct sources.

    A single source cannot establish multi-source agreement.

    For two or more sources:
        agreement =
            (supporting_sources - 1)
            / (total_sources - 1)

    Therefore:
        1 source  -> 0.0
        2/2       -> 1.0
        2/3       -> 0.5
        3/3       -> 1.0

    This deliberately measures source agreement rather than truth.
    """
    if total_source_count < 2:
        return 0.0

    score = (
        (supporting_source_count - 1)
        / (total_source_count - 1)
    )

    return max(0.0, min(1.0, score))


def assess_multi_source_agreement(
    *,
    knowledge: KnowledgeCandidate,
    evidence_items: Iterable[Evidence],
    sources: Iterable[ResearchSource] = (),
) -> MultiSourceAgreementAssessment:
    """
    Assess agreement among distinct sources linked to one
    knowledge candidate.

    The optional sources argument is accepted for future source
    validation and architectural symmetry. Source agreement is
    based on evidence source IDs and does not use reliability or
    quality scores.
    """
    if not isinstance(knowledge, KnowledgeCandidate):
        raise TypeError(
            "knowledge must be a KnowledgeCandidate"
        )

    evidence_list = _linked_evidence(
        knowledge,
        evidence_items,
    )

    # Materialize for deterministic processing and future validation.
    source_list = list(sources)

    valid_source_ids = {
        source.source_id
        for source in source_list
        if isinstance(source, ResearchSource)
    }

    if source_list:
        filtered_evidence = [
            evidence
            for evidence in evidence_list
            if (
                not valid_source_ids
                or evidence.source_id in valid_source_ids
            )
        ]
    else:
        filtered_evidence = evidence_list

    supporting_evidence = [
        evidence
        for evidence in filtered_evidence
        if evidence.supports
    ]

    contradicting_evidence = [
        evidence
        for evidence in filtered_evidence
        if not evidence.supports
    ]

    all_source_ids = _source_ids(
        filtered_evidence
    )

    supporting_source_ids = _source_ids(
        supporting_evidence
    )

    contradicting_source_ids = _source_ids(
        contradicting_evidence
    )

    total_source_count = len(all_source_ids)

    supporting_source_count = len(
        supporting_source_ids
    )

    contradicting_source_count = len(
        contradicting_source_ids
    )

    agreement_score = _agreement_score(
        supporting_source_count,
        total_source_count,
    )

    return MultiSourceAgreementAssessment(
        knowledge_id=knowledge.knowledge_id,
        total_source_count=total_source_count,
        supporting_source_count=supporting_source_count,
        contradicting_source_count=contradicting_source_count,
        agreement_score=round(
            agreement_score,
            4,
        ),
    )
