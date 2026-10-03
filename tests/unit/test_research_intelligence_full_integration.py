from datetime import datetime, timedelta, timezone

from core.research.aggregator import ResearchResultAggregator
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchFinding,
    ResearchSource,
)


def build_source(
    source_id: str,
    reliability: float,
    published_at: datetime,
) -> ResearchSource:
    now = datetime.now(timezone.utc)

    return ResearchSource(
        source_id=source_id,
        title=f"Source {source_id}",
        source_type="document",
        locator=f"test://{source_id}",
        publisher="SAHIBEX Integration Test",
        author=None,
        published_at=published_at,
        accessed_at=now,
        reliability=reliability,
        metadata={
            "provider": "integration-test",
            "content_type": "text",
            "reliability": reliability,
        },
    )


def build_finding(
    finding_id: str,
    claim: str,
) -> ResearchFinding:
    now = datetime.now(timezone.utc)

    return ResearchFinding(
        finding_id=finding_id,
        document_id=f"document_{finding_id}",
        claim=claim,
        evidence_text=claim,
        confidence=0.90,
        created_at=now,
        metadata={},
    )


def build_evidence(
    evidence_id: str,
    finding_id: str,
    source_id: str,
    knowledge_id: str,
) -> Evidence:
    now = datetime.now(timezone.utc)

    return Evidence(
        evidence_id=evidence_id,
        finding_id=finding_id,
        source_id=source_id,
        evidence_text="The system is safe.",
        supports=True,
        strength=0.90,
        created_at=now,
        metadata={
            "knowledge_id": knowledge_id,
        },
    )


def build_knowledge(
    knowledge_id: str,
    finding_id: str,
    evidence_ids: list[str],
) -> KnowledgeCandidate:
    now = datetime.now(timezone.utc)

    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement="The system is safe.",
        findings=[finding_id],
        evidence=list(evidence_ids),
        confidence=0.90,
        verified=True,
        created_at=now,
        last_verified_at=now,
        metadata={},
    )


def test_full_6g_pipeline() -> None:
    aggregator = ResearchResultAggregator()

    now = datetime.now(timezone.utc)

    sources = [
        build_source(
            "source_1",
            reliability=0.90,
            published_at=now - timedelta(hours=2),
        ),
        build_source(
            "source_2",
            reliability=0.85,
            published_at=now - timedelta(hours=3),
        ),
    ]

    findings = [
        build_finding(
            "finding_1",
            "The system is safe.",
        ),
    ]

    evidence_items = [
        build_evidence(
            "evidence_1",
            "finding_1",
            "source_1",
            "knowledge_1",
        ),
        build_evidence(
            "evidence_2",
            "finding_1",
            "source_2",
            "knowledge_1",
        ),
    ]

    knowledge_items = [
        build_knowledge(
            "knowledge_1",
            "finding_1",
            [
                "evidence_1",
                "evidence_2",
            ],
        ),
    ]

    result = aggregator.aggregate(
        knowledge_items,
        verified_only=True,
        limit=10,
        evidence_items=evidence_items,
        sources=sources,
        findings=findings,
        reference_time=now,
    )

    assert result.total_candidates == 1
    assert result.verified_count == 1
    assert result.unverified_count == 0

    assert len(result.results) == 1

    # 6G-9A
    assert result.answer is not None
    assert result.answer.version == "6G-9"

    # 6G-4 Multi-Source Agreement
    assert len(result.agreement_assessments) == 1

    agreement = result.agreement_assessments[0]

    assert agreement.total_source_count == 2
    assert agreement.supporting_source_count == 2
    assert agreement.contradicting_source_count == 0
    assert agreement.agreement_score == 1.0
    assert agreement.version == "6G-4"

    # 6G-5 Conflict Intelligence
    #
    # This fixture contains only supporting evidence
    # and no conflicting knowledge candidates.
    # Therefore no conflict intelligence assessment
    # is expected.

    assert result.conflict_intelligence == []

    # 6G-6 Freshness
    assert len(result.freshness_assessments) == 2

    for freshness in result.freshness_assessments:
        assert 0.0 <= freshness.freshness_score <= 1.0
        assert freshness.version == "6G-6"

    # 6G-7 Confidence
    assert len(result.confidence_assessments) == 1

    confidence = result.confidence_assessments[0]

    assert confidence.knowledge_id == "knowledge_1"
    assert 0.0 <= confidence.confidence_score <= 1.0
    assert confidence.version == "6G-7"

    # 6G-8 Source Ranking
    assert len(result.source_ranking_assessments) == 2

    ranking_scores = [
        item.ranking_score
        for item in result.source_ranking_assessments
    ]

    assert all(
        0.0 <= score <= 1.0
        for score in ranking_scores
    )

    for ranking in result.source_ranking_assessments:
        assert ranking.version == "6G-8"

    # 6G-9C Answer Traceability
    assert result.answer_traceability is not None

    traceability = result.answer_traceability

    assert traceability.version == "6G-9C"
    assert traceability.trace_complete is True
    assert traceability.traceable_claim_count == 1
    assert traceability.incomplete_claim_count == 0

    assert len(traceability.traces) == 1

    trace = traceability.traces[0]

    assert trace.knowledge_id == "knowledge_1"
    assert trace.finding_ids == ("finding_1",)

    assert trace.evidence_ids == (
        "evidence_1",
        "evidence_2",
    )

    assert trace.source_ids == (
        "source_1",
        "source_2",
    )

    assert trace.trace_complete is True
    assert trace.missing_links == ()


def test_full_6g_pipeline_is_deterministic() -> None:
    aggregator = ResearchResultAggregator()

    now = datetime.now(timezone.utc)

    sources = [
        build_source(
            "source_1",
            0.90,
            now - timedelta(hours=2),
        ),
        build_source(
            "source_2",
            0.85,
            now - timedelta(hours=3),
        ),
    ]

    findings = [
        build_finding(
            "finding_1",
            "The system is safe.",
        ),
    ]

    evidence_items = [
        build_evidence(
            "evidence_1",
            "finding_1",
            "source_1",
            "knowledge_1",
        ),
        build_evidence(
            "evidence_2",
            "finding_1",
            "source_2",
            "knowledge_1",
        ),
    ]

    knowledge_items = [
        build_knowledge(
            "knowledge_1",
            "finding_1",
            [
                "evidence_1",
                "evidence_2",
            ],
        ),
    ]

    result_a = aggregator.aggregate(
        knowledge_items,
        verified_only=True,
        evidence_items=evidence_items,
        sources=sources,
        findings=findings,
        reference_time=now,
    )

    result_b = aggregator.aggregate(
        knowledge_items,
        verified_only=True,
        evidence_items=evidence_items,
        sources=sources,
        findings=findings,
        reference_time=now,
    )

    assert result_a.status == result_b.status

    assert (
        result_a.overall_confidence
        == result_b.overall_confidence
    )

    assert (
        result_a.answer.answer
        == result_b.answer.answer
    )

    assert (
        result_a.answer_traceability.trace_complete
        == result_b.answer_traceability.trace_complete
    )

    assert (
        result_a.answer_traceability.traces
        == result_b.answer_traceability.traces
    )

    assert (
        result_a.agreement_assessments
        == result_b.agreement_assessments
    )

    assert (
        result_a.confidence_assessments
        == result_b.confidence_assessments
    )

    assert (
        result_a.source_ranking_assessments
        == result_b.source_ranking_assessments
    )


def main() -> None:
    print(
        "SAHIBEX 6G-10 FULL RESEARCH "
        "INTELLIGENCE INTEGRATION TEST"
    )

    test_full_6g_pipeline()
    print("[PASS] full 6G intelligence pipeline")

    test_full_6g_pipeline_is_deterministic()
    print("[PASS] full 6G pipeline determinism")

    print(
        "SAHIBEX 6G-10 FULL RESEARCH "
        "INTELLIGENCE INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
