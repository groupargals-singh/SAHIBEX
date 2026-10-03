from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core.research.agreement import (
    assess_multi_source_agreement,
)
from core.research.confidence import (
    STATUS_HIGH,
    STATUS_MEDIUM,
    STATUS_UNCERTAIN,
    ResearchConfidenceEngine,
)
from core.research.evidence_strength import (
    assess_evidence_strength,
)
from core.research.freshness import (
    assess_source_freshness,
)
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchFinding,
    ResearchSource,
)
from core.research.source_quality import (
    assess_source_quality,
)


REFERENCE_TIME = datetime(
    2026,
    1,
    1,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)


def make_source(
    source_id: str,
    *,
    published_at: datetime | None,
    reliability: float,
) -> ResearchSource:
    accessed_at = (
        published_at
        if published_at is not None
        else REFERENCE_TIME
    )

    return ResearchSource(
        source_id=source_id,
        title=f"Source {source_id}",
        source_type="document",
        locator=f"https://example.com/{source_id}",
        publisher="Example Publisher",
        author="Author",
        published_at=published_at,
        accessed_at=accessed_at,
        reliability=reliability,
        metadata={
            "provider": "test-provider",
            "provider_name": "Test Provider",
            "content_type": "document",
            "reliability_source": "provider",
            "reliability_version": "6G-1",
            "acquired_at": "2026-01-01T12:00:00+00:00",
            "content_hash": "abc123",
            "content_bytes": 1000,
            "discovery_only": False,
            "content_is_full_document": True,
        },
    )


def make_knowledge(
    knowledge_id: str,
    *,
    confidence: float = 0.9,
) -> KnowledgeCandidate:
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=f"Statement {knowledge_id}",
        confidence=confidence,
        verified=True,
    )


def make_finding(
    finding_id: str,
    *,
    confidence: float = 0.9,
) -> ResearchFinding:
    return ResearchFinding(
        finding_id=finding_id,
        document_id=f"document_{finding_id}",
        claim="The research claim is supported",
        evidence_text="The research claim is supported by evidence.",
        confidence=confidence,
    )


def make_evidence(
    evidence_id: str,
    *,
    finding_id: str,
    source_id: str,
    knowledge_id: str,
    supports: bool = True,
    strength: float = 0.9,
) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        finding_id=finding_id,
        source_id=source_id,
        evidence_text=(
            "The research claim is supported by "
            "strong documented evidence."
        ),
        supports=supports,
        strength=strength,
        metadata={
            "knowledge_id": knowledge_id,
        },
    )


def test_high_confidence_multi_source() -> None:
    knowledge = make_knowledge(
        "knowledge_high"
    )

    finding_a = make_finding(
        "finding_a",
        confidence=0.95,
    )

    finding_b = make_finding(
        "finding_b",
        confidence=0.95,
    )

    source_a = make_source(
        "source_a",
        published_at=REFERENCE_TIME - timedelta(hours=6),
        reliability=0.95,
    )

    source_b = make_source(
        "source_b",
        published_at=REFERENCE_TIME - timedelta(hours=12),
        reliability=0.90,
    )

    evidence_a = make_evidence(
        "evidence_a",
        finding_id=finding_a.finding_id,
        source_id=source_a.source_id,
        knowledge_id=knowledge.knowledge_id,
    )

    evidence_b = make_evidence(
        "evidence_b",
        finding_id=finding_b.finding_id,
        source_id=source_b.source_id,
        knowledge_id=knowledge.knowledge_id,
    )

    evidence_strength_a = assess_evidence_strength(
        evidence=evidence_a,
        finding=finding_a,
        source=source_a,
    )

    evidence_strength_b = assess_evidence_strength(
        evidence=evidence_b,
        finding=finding_b,
        source=source_b,
    )

    agreement = assess_multi_source_agreement(
        knowledge=knowledge,
        evidence_items=[
            evidence_a,
            evidence_b,
        ],
        sources=[
            source_a,
            source_b,
        ],
    )

    freshness_a = assess_source_freshness(
        source_a,
        reference_time=REFERENCE_TIME,
    )

    freshness_b = assess_source_freshness(
        source_b,
        reference_time=REFERENCE_TIME,
    )

    quality_a = assess_source_quality(
        source_a
    )

    quality_b = assess_source_quality(
        source_b
    )

    engine = ResearchConfidenceEngine()

    result = engine.assess(
        knowledge=knowledge,
        evidence_items=[
            evidence_a,
            evidence_b,
        ],
        sources=[
            source_a,
            source_b,
        ],
        evidence_assessments=[
            evidence_strength_a,
            evidence_strength_b,
        ],
        agreement_assessments=[
            agreement,
        ],
        freshness_assessments=[
            freshness_a,
            freshness_b,
        ],
        quality_assessments=[
            quality_a,
            quality_b,
        ],
    )

    assert result.knowledge_id == (
        knowledge.knowledge_id
    )

    assert result.confidence_score >= 0.80
    assert result.status == STATUS_HIGH

    assert (
        result.source_reliability_score
        > 0.90
    )

    assert (
        result.source_quality_score
        > 0.80
    )

    assert (
        result.evidence_strength_score
        > 0.80
    )

    assert result.agreement_score == 1.0

    assert result.conflict_count == 0
    assert result.unresolved_conflict_count == 0
    assert result.conflict_score == 1.0

    assert result.freshness_score == 1.0

    print("[PASS] high-confidence multi-source assessment")


def test_unresolved_conflict_reduces_confidence() -> None:
    knowledge = make_knowledge(
        "knowledge_conflict"
    )

    finding = make_finding(
        "finding_conflict",
        confidence=0.8,
    )

    source = make_source(
        "source_conflict",
        published_at=REFERENCE_TIME - timedelta(hours=6),
        reliability=0.8,
    )

    evidence = make_evidence(
        "evidence_conflict",
        finding_id=finding.finding_id,
        source_id=source.source_id,
        knowledge_id=knowledge.knowledge_id,
    )

    evidence_strength = assess_evidence_strength(
        evidence=evidence,
        finding=finding,
        source=source,
    )

    agreement = assess_multi_source_agreement(
        knowledge=knowledge,
        evidence_items=[evidence],
        sources=[source],
    )

    freshness = assess_source_freshness(
        source,
        reference_time=REFERENCE_TIME,
    )

    quality = assess_source_quality(
        source
    )

    unresolved_conflict = type(
        "ConflictAssessment",
        (),
        {
            "first_knowledge_id": knowledge.knowledge_id,
            "second_knowledge_id": "knowledge_other",
            "resolution_status": "UNRESOLVED",
        },
    )()

    resolved_conflict = type(
        "ConflictAssessment",
        (),
        {
            "first_knowledge_id": knowledge.knowledge_id,
            "second_knowledge_id": "knowledge_other_2",
            "resolution_status": "RESOLVED",
        },
    )()

    engine = ResearchConfidenceEngine()

    unresolved_result = engine.assess(
        knowledge=knowledge,
        evidence_items=[evidence],
        sources=[source],
        evidence_assessments=[
            evidence_strength
        ],
        agreement_assessments=[agreement],
        conflict_assessments=[
            unresolved_conflict,
        ],
        freshness_assessments=[freshness],
        quality_assessments=[quality],
    )

    resolved_result = engine.assess(
        knowledge=knowledge,
        evidence_items=[evidence],
        sources=[source],
        evidence_assessments=[
            evidence_strength
        ],
        agreement_assessments=[agreement],
        conflict_assessments=[
            resolved_conflict,
        ],
        freshness_assessments=[freshness],
        quality_assessments=[quality],
    )

    assert (
        unresolved_result.unresolved_conflict_count
        == 1
    )

    assert (
        unresolved_result.conflict_count
        == 1
    )

    assert (
        unresolved_result.conflict_score
        == 0.0
    )

    assert (
        unresolved_result.confidence_score
        < resolved_result.confidence_score
    )

    assert unresolved_result.status in {
        STATUS_MEDIUM,
        STATUS_UNCERTAIN,
    }

    print(
        "[PASS] unresolved conflict reduces confidence"
    )


def test_unknown_freshness_gets_no_positive_credit() -> None:
    knowledge = make_knowledge(
        "knowledge_unknown_freshness"
    )

    finding = make_finding(
        "finding_unknown_freshness"
    )

    source = make_source(
        "source_unknown_freshness",
        published_at=None,
        reliability=0.9,
    )

    evidence = make_evidence(
        "evidence_unknown_freshness",
        finding_id=finding.finding_id,
        source_id=source.source_id,
        knowledge_id=knowledge.knowledge_id,
    )

    evidence_strength = assess_evidence_strength(
        evidence=evidence,
        finding=finding,
        source=source,
    )

    agreement = assess_multi_source_agreement(
        knowledge=knowledge,
        evidence_items=[evidence],
        sources=[source],
    )

    freshness = assess_source_freshness(
        source,
        reference_time=REFERENCE_TIME,
    )

    quality = assess_source_quality(
        source
    )

    engine = ResearchConfidenceEngine()

    result = engine.assess(
        knowledge=knowledge,
        evidence_items=[evidence],
        sources=[source],
        evidence_assessments=[
            evidence_strength
        ],
        agreement_assessments=[agreement],
        freshness_assessments=[freshness],
        quality_assessments=[quality],
    )

    assert result.freshness_score == 0.0
    assert result.confidence_score < 1.0

    print(
        "[PASS] unknown freshness gets no positive credit"
    )


def test_missing_quality_assessment_uses_canonical_fallback() -> None:
    knowledge = make_knowledge(
        "knowledge_quality_fallback"
    )

    finding = make_finding(
        "finding_quality_fallback"
    )

    source = make_source(
        "source_quality_fallback",
        published_at=REFERENCE_TIME - timedelta(hours=3),
        reliability=0.9,
    )

    evidence = make_evidence(
        "evidence_quality_fallback",
        finding_id=finding.finding_id,
        source_id=source.source_id,
        knowledge_id=knowledge.knowledge_id,
    )

    evidence_strength = assess_evidence_strength(
        evidence=evidence,
        finding=finding,
        source=source,
    )

    agreement = assess_multi_source_agreement(
        knowledge=knowledge,
        evidence_items=[evidence],
        sources=[source],
    )

    freshness = assess_source_freshness(
        source,
        reference_time=REFERENCE_TIME,
    )

    expected_quality = assess_source_quality(
        source
    )

    engine = ResearchConfidenceEngine()

    result = engine.assess(
        knowledge=knowledge,
        evidence_items=[evidence],
        sources=[source],
        evidence_assessments=[
            evidence_strength
        ],
        agreement_assessments=[agreement],
        freshness_assessments=[freshness],
        quality_assessments=[],
    )

    assert (
        result.source_quality_score
        == expected_quality.quality_score
    )

    print(
        "[PASS] source quality fallback"
    )


def test_input_objects_are_not_mutated() -> None:
    knowledge = make_knowledge(
        "knowledge_immutable"
    )

    finding = make_finding(
        "finding_immutable"
    )

    source = make_source(
        "source_immutable",
        published_at=REFERENCE_TIME - timedelta(hours=2),
        reliability=0.8,
    )

    evidence = make_evidence(
        "evidence_immutable",
        finding_id=finding.finding_id,
        source_id=source.source_id,
        knowledge_id=knowledge.knowledge_id,
    )

    original_confidence = knowledge.confidence
    original_reliability = source.reliability
    original_metadata = dict(evidence.metadata)

    evidence_strength = assess_evidence_strength(
        evidence=evidence,
        finding=finding,
        source=source,
    )

    agreement = assess_multi_source_agreement(
        knowledge=knowledge,
        evidence_items=[evidence],
        sources=[source],
    )

    freshness = assess_source_freshness(
        source,
        reference_time=REFERENCE_TIME,
    )

    quality = assess_source_quality(
        source
    )

    engine = ResearchConfidenceEngine()

    engine.assess(
        knowledge=knowledge,
        evidence_items=[evidence],
        sources=[source],
        evidence_assessments=[
            evidence_strength
        ],
        agreement_assessments=[agreement],
        freshness_assessments=[freshness],
        quality_assessments=[quality],
    )

    assert knowledge.confidence == (
        original_confidence
    )

    assert source.reliability == (
        original_reliability
    )

    assert evidence.metadata == (
        original_metadata
    )

    print("[PASS] input immutability")


def test_engine_is_deterministic() -> None:
    knowledge = make_knowledge(
        "knowledge_deterministic"
    )

    finding = make_finding(
        "finding_deterministic"
    )

    source = make_source(
        "source_deterministic",
        published_at=REFERENCE_TIME - timedelta(hours=4),
        reliability=0.85,
    )

    evidence = make_evidence(
        "evidence_deterministic",
        finding_id=finding.finding_id,
        source_id=source.source_id,
        knowledge_id=knowledge.knowledge_id,
    )

    evidence_strength = assess_evidence_strength(
        evidence=evidence,
        finding=finding,
        source=source,
    )

    agreement = assess_multi_source_agreement(
        knowledge=knowledge,
        evidence_items=[evidence],
        sources=[source],
    )

    freshness = assess_source_freshness(
        source,
        reference_time=REFERENCE_TIME,
    )

    quality = assess_source_quality(
        source
    )

    engine = ResearchConfidenceEngine()

    first = engine.assess(
        knowledge=knowledge,
        evidence_items=[evidence],
        sources=[source],
        evidence_assessments=[
            evidence_strength
        ],
        agreement_assessments=[agreement],
        freshness_assessments=[freshness],
        quality_assessments=[quality],
    )

    second = engine.assess(
        knowledge=knowledge,
        evidence_items=[evidence],
        sources=[source],
        evidence_assessments=[
            evidence_strength
        ],
        agreement_assessments=[agreement],
        freshness_assessments=[freshness],
        quality_assessments=[quality],
    )

    assert first == second

    print("[PASS] deterministic confidence")


def run_all_tests() -> None:
    print(
        "SAHIBEX 6G-7 RESEARCH CONFIDENCE "
        "ENGINE TEST"
    )

    test_high_confidence_multi_source()
    test_unresolved_conflict_reduces_confidence()
    test_unknown_freshness_gets_no_positive_credit()
    test_missing_quality_assessment_uses_canonical_fallback()
    test_input_objects_are_not_mutated()
    test_engine_is_deterministic()

    print(
        "SAHIBEX 6G-7 RESEARCH CONFIDENCE "
        "ENGINE TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
