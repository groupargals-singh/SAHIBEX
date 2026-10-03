from datetime import datetime, timezone

from core.research.aggregator import ResearchResultAggregator
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchFinding,
    ResearchSource,
)


def source(source_id: str = "source_1") -> ResearchSource:
    now = datetime.now(timezone.utc)

    return ResearchSource(
        source_id=source_id,
        title="Test Source",
        source_type="document",
        locator=f"test://{source_id}",
        publisher="Test Publisher",
        author=None,
        published_at=now,
        accessed_at=now,
        reliability=0.90,
        metadata={
            "provider": "test",
            "content_type": "text",
            "reliability": 0.90,
        },
    )


def finding(
    finding_id: str = "finding_1",
) -> ResearchFinding:
    now = datetime.now(timezone.utc)

    return ResearchFinding(
        finding_id=finding_id,
        document_id="document_1",
        claim="The system is safe.",
        evidence_text="The system is safe.",
        confidence=0.90,
        created_at=now,
        metadata={},
    )


def evidence(
    evidence_id: str = "evidence_1",
) -> Evidence:
    now = datetime.now(timezone.utc)

    return Evidence(
        evidence_id=evidence_id,
        finding_id="finding_1",
        source_id="source_1",
        evidence_text="The system is safe.",
        supports=True,
        strength=0.90,
        created_at=now,
        metadata={
            "knowledge_id": "knowledge_1",
        },
    )


def knowledge(
    knowledge_id: str = "knowledge_1",
    verified: bool = True,
) -> KnowledgeCandidate:
    now = datetime.now(timezone.utc)

    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement="The system is safe.",
        findings=["finding_1"],
        evidence=["evidence_1"],
        confidence=0.90,
        verified=verified,
        created_at=now,
        last_verified_at=now if verified else None,
        metadata={},
    )


def test_complete_answer_trace() -> None:
    aggregator = ResearchResultAggregator()

    result = aggregator.aggregate(
        [knowledge()],
        verified_only=True,
        findings=[finding()],
        evidence_items=[evidence()],
        sources=[source()],
    )

    traceability = result.answer_traceability

    assert traceability.version == "6G-9C"
    assert traceability.trace_complete is True
    assert traceability.traceable_claim_count == 1
    assert traceability.incomplete_claim_count == 0

    assert len(traceability.traces) == 1

    trace = traceability.traces[0]

    assert trace.statement == "The system is safe."
    assert trace.knowledge_id == "knowledge_1"
    assert trace.finding_ids == ("finding_1",)
    assert trace.evidence_ids == ("evidence_1",)
    assert trace.source_ids == ("source_1",)

    assert trace.trace_complete is True
    assert trace.missing_links == ()


def test_missing_finding_protection() -> None:
    aggregator = ResearchResultAggregator()

    result = aggregator.aggregate(
        [knowledge()],
        verified_only=True,
        findings=[],
        evidence_items=[evidence()],
        sources=[source()],
    )

    traceability = result.answer_traceability

    assert traceability.trace_complete is False
    assert traceability.traceable_claim_count == 0
    assert traceability.incomplete_claim_count == 1

    trace = traceability.traces[0]

    assert trace.trace_complete is False
    assert "finding:finding_1" in trace.missing_links


def test_missing_evidence_protection() -> None:
    aggregator = ResearchResultAggregator()

    result = aggregator.aggregate(
        [knowledge()],
        verified_only=True,
        findings=[finding()],
        evidence_items=[],
        sources=[source()],
    )

    traceability = result.answer_traceability

    assert traceability.trace_complete is False
    assert traceability.incomplete_claim_count == 1

    trace = traceability.traces[0]

    assert trace.trace_complete is False
    assert "evidence:evidence_1" in trace.missing_links


def test_missing_source_protection() -> None:
    aggregator = ResearchResultAggregator()

    result = aggregator.aggregate(
        [knowledge()],
        verified_only=True,
        findings=[finding()],
        evidence_items=[evidence()],
        sources=[],
    )

    traceability = result.answer_traceability

    assert traceability.trace_complete is False
    assert traceability.incomplete_claim_count == 1

    trace = traceability.traces[0]

    assert trace.trace_complete is False
    assert "source:source_1" in trace.missing_links


def test_backward_compatibility_without_findings() -> None:
    aggregator = ResearchResultAggregator()

    result = aggregator.aggregate(
        [knowledge()],
        verified_only=True,
    )

    assert result.answer is not None
    assert result.answer_traceability is not None

    traceability = result.answer_traceability

    assert traceability.trace_complete is False
    assert traceability.incomplete_claim_count == 1


def main() -> None:
    print("SAHIBEX 6G-9C ANSWER TRACEABILITY AGGREGATOR INTEGRATION TEST")

    tests = [
        (
            "complete answer trace",
            test_complete_answer_trace,
        ),
        (
            "missing finding protection",
            test_missing_finding_protection,
        ),
        (
            "missing evidence protection",
            test_missing_evidence_protection,
        ),
        (
            "missing source protection",
            test_missing_source_protection,
        ),
        (
            "backward compatibility without findings",
            test_backward_compatibility_without_findings,
        ),
    ]

    for name, test in tests:
        test()
        print(f"[PASS] {name}")

    print(
        "SAHIBEX 6G-9C ANSWER TRACEABILITY "
        "AGGREGATOR INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
