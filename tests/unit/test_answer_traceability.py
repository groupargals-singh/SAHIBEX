from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from core.research.answer_synthesis import (
    AnswerClaimAssessment,
    QualityAwareAnswer,
)
from core.research.answer_traceability import (
    ANSWER_TRACEABILITY_VERSION,
    AnswerTraceabilityEngine,
)
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchDocument,
    ResearchFinding,
    ResearchSource,
)


def _build_fixture():
    published_at = datetime(
        2026,
        9,
        20,
        tzinfo=timezone.utc,
    )

    source = ResearchSource(
        source_id="source_1",
        title="Test Source",
        source_type="document",
        locator="test://source-1",
        publisher="Test Publisher",
        published_at=published_at,
        reliability=0.90,
        metadata={
            "provider": "test",
            "content_type": "text",
            "reliability_source": "provider",
            "reliability_version": "6G-1",
        },
    )

    document = ResearchDocument(
        document_id="document_1",
        source_id="source_1",
        title="Test Document",
        content="Test evidence content.",
    )

    finding = ResearchFinding(
        finding_id="finding_1",
        document_id="document_1",
        claim="Test claim",
        evidence_text="Test evidence content.",
        confidence=0.90,
    )

    evidence = Evidence(
        evidence_id="evidence_1",
        finding_id="finding_1",
        source_id="source_1",
        evidence_text="Test evidence content.",
        supports=True,
        strength=0.90,
    )

    knowledge = KnowledgeCandidate(
        knowledge_id="knowledge_1",
        statement="Test claim",
        findings=["finding_1"],
        evidence=["evidence_1"],
        confidence=0.90,
        verified=True,
    )

    assessment = AnswerClaimAssessment(
        knowledge_id="knowledge_1",
        statement="Test claim",
        status="SUPPORTED",
        confidence_score=0.90,
        source_count=1,
        evidence_count=1,
        agreement_score=0.0,
        conflict_score=1.0,
        freshness_score=1.0,
        source_ranking_score=0.90,
        verified=True,
        supported=True,
        explanation="Supported by linked evidence.",
    )

    answer = QualityAwareAnswer(
        answer="Test claim",
        claims=(assessment,),
        supported_claims=("Test claim",),
        uncertain_claims=(),
        conflicted_claims=(),
        stale_claims=(),
        overall_status="SUPPORTED",
        overall_confidence=0.90,
        metadata={},
    )

    return (
        answer,
        knowledge,
        finding,
        evidence,
        source,
        document,
    )


def test_empty_answer_is_not_reported_as_trace_complete():
    (answer, knowledge, finding, evidence, source, _document) = _build_fixture()
    empty_answer = replace(answer, claims=())

    result = AnswerTraceabilityEngine().trace_answer(
        answer=empty_answer,
        knowledge_items=[knowledge],
        findings=[finding],
        evidence_items=[evidence],
        sources=[source],
    )

    assert result.traces == ()
    assert result.traceable_claim_count == 0
    assert result.incomplete_claim_count == 0
    assert result.trace_complete is False


def test_complete_trace():
    (
        answer,
        knowledge,
        finding,
        evidence,
        source,
        _document,
    ) = _build_fixture()

    engine = AnswerTraceabilityEngine()

    result = engine.trace_answer(
        answer=answer,
        knowledge_items=[knowledge],
        findings=[finding],
        evidence_items=[evidence],
        sources=[source],
    )

    assert result.trace_complete is True
    assert result.traceable_claim_count == 1
    assert result.incomplete_claim_count == 0

    trace = result.traces[0]

    assert trace.statement == "Test claim"
    assert trace.knowledge_id == "knowledge_1"
    assert trace.finding_ids == ("finding_1",)
    assert trace.evidence_ids == ("evidence_1",)
    assert trace.source_ids == ("source_1",)
    assert trace.confidence_score == 0.90
    assert trace.answer_status == "SUPPORTED"
    assert trace.verified is True
    assert trace.supported is True
    assert trace.trace_complete is True
    assert trace.missing_links == ()


def test_missing_evidence_is_explicitly_reported():
    (
        answer,
        knowledge,
        finding,
        _evidence,
        source,
        _document,
    ) = _build_fixture()

    engine = AnswerTraceabilityEngine()

    result = engine.trace_answer(
        answer=answer,
        knowledge_items=[knowledge],
        findings=[finding],
        evidence_items=[],
        sources=[source],
    )

    assert result.trace_complete is False
    assert result.traceable_claim_count == 0
    assert result.incomplete_claim_count == 1

    trace = result.traces[0]

    assert trace.trace_complete is False
    assert "evidence:evidence_1" in (
        trace.missing_links
    )


def test_missing_source_is_explicitly_reported():
    (
        answer,
        knowledge,
        finding,
        evidence,
        _source,
        _document,
    ) = _build_fixture()

    engine = AnswerTraceabilityEngine()

    result = engine.trace_answer(
        answer=answer,
        knowledge_items=[knowledge],
        findings=[finding],
        evidence_items=[evidence],
        sources=[],
    )

    assert result.trace_complete is False
    assert result.incomplete_claim_count == 1

    trace = result.traces[0]

    assert trace.trace_complete is False
    assert "source:source_1" in (
        trace.missing_links
    )


def test_missing_knowledge_is_explicitly_reported():
    (
        answer,
        _knowledge,
        finding,
        evidence,
        source,
        _document,
    ) = _build_fixture()

    engine = AnswerTraceabilityEngine()

    result = engine.trace_answer(
        answer=answer,
        knowledge_items=[],
        findings=[finding],
        evidence_items=[evidence],
        sources=[source],
    )

    assert result.trace_complete is False
    assert result.incomplete_claim_count == 1

    trace = result.traces[0]

    assert trace.knowledge_id == "knowledge_1"
    assert trace.trace_complete is False
    assert "knowledge" in trace.missing_links


def test_missing_finding_is_explicitly_reported():
    (
        answer,
        knowledge,
        _finding,
        evidence,
        source,
        _document,
    ) = _build_fixture()

    engine = AnswerTraceabilityEngine()

    result = engine.trace_answer(
        answer=answer,
        knowledge_items=[knowledge],
        findings=[],
        evidence_items=[evidence],
        sources=[source],
    )

    assert result.trace_complete is False
    assert result.incomplete_claim_count == 1

    trace = result.traces[0]

    assert trace.trace_complete is False
    assert "finding:finding_1" in (
        trace.missing_links
    )


def test_duplicate_sources_are_deduplicated():
    (
        answer,
        knowledge,
        finding,
        evidence,
        source,
        _document,
    ) = _build_fixture()

    second_evidence = Evidence(
        evidence_id="evidence_2",
        finding_id="finding_1",
        source_id="source_1",
        evidence_text="Second evidence.",
        supports=True,
        strength=0.80,
    )

    knowledge_with_two_evidence = KnowledgeCandidate(
        knowledge_id="knowledge_1",
        statement="Test claim",
        findings=["finding_1"],
        evidence=[
            "evidence_1",
            "evidence_2",
        ],
        confidence=0.90,
        verified=True,
    )

    engine = AnswerTraceabilityEngine()

    result = engine.trace_answer(
        answer=answer,
        knowledge_items=[
            knowledge_with_two_evidence
        ],
        findings=[finding],
        evidence_items=[
            evidence,
            second_evidence,
        ],
        sources=[source],
    )

    trace = result.traces[0]

    assert trace.source_ids == ("source_1",)
    assert trace.evidence_ids == (
        "evidence_1",
        "evidence_2",
    )
    assert trace.trace_complete is True


def test_input_objects_are_not_mutated():
    (
        answer,
        knowledge,
        finding,
        evidence,
        source,
        _document,
    ) = _build_fixture()

    before_knowledge = (
        knowledge.findings[:],
        knowledge.evidence[:],
        knowledge.confidence,
        knowledge.verified,
    )

    before_evidence = (
        evidence.supports,
        evidence.strength,
        dict(evidence.metadata),
    )

    before_source = (
        source.reliability,
        dict(source.metadata),
    )

    engine = AnswerTraceabilityEngine()

    engine.trace_answer(
        answer=answer,
        knowledge_items=[knowledge],
        findings=[finding],
        evidence_items=[evidence],
        sources=[source],
    )

    assert (
        knowledge.findings,
        knowledge.evidence,
        knowledge.confidence,
        knowledge.verified,
    ) == before_knowledge

    assert (
        evidence.supports,
        evidence.strength,
        evidence.metadata,
    ) == before_evidence

    assert (
        source.reliability,
        source.metadata,
    ) == before_source


def test_deterministic_trace():
    (
        answer,
        knowledge,
        finding,
        evidence,
        source,
        _document,
    ) = _build_fixture()

    engine = AnswerTraceabilityEngine()

    first = engine.trace_answer(
        answer=answer,
        knowledge_items=[knowledge],
        findings=[finding],
        evidence_items=[evidence],
        sources=[source],
    )

    second = engine.trace_answer(
        answer=answer,
        knowledge_items=[knowledge],
        findings=[finding],
        evidence_items=[evidence],
        sources=[source],
    )

    assert first == second


def test_version():
    (
        answer,
        knowledge,
        finding,
        evidence,
        source,
        _document,
    ) = _build_fixture()

    engine = AnswerTraceabilityEngine()

    result = engine.trace_answer(
        answer=answer,
        knowledge_items=[knowledge],
        findings=[finding],
        evidence_items=[evidence],
        sources=[source],
    )

    assert result.version == (
        ANSWER_TRACEABILITY_VERSION
    )

    assert result.traces[0].version == (
        ANSWER_TRACEABILITY_VERSION
    )


if __name__ == "__main__":
    print(
        "SAHIBEX 6G-9C ANSWER TRACEABILITY TEST"
    )

    tests = (
        (
            "complete trace",
            test_complete_trace,
        ),
        (
            "missing evidence protection",
            test_missing_evidence_is_explicitly_reported,
        ),
        (
            "missing source protection",
            test_missing_source_is_explicitly_reported,
        ),
        (
            "missing knowledge protection",
            test_missing_knowledge_is_explicitly_reported,
        ),
        (
            "missing finding protection",
            test_missing_finding_is_explicitly_reported,
        ),
        (
            "duplicate source deduplication",
            test_duplicate_sources_are_deduplicated,
        ),
        (
            "input immutability",
            test_input_objects_are_not_mutated,
        ),
        (
            "deterministic trace",
            test_deterministic_trace,
        ),
        (
            "version",
            test_version,
        ),
    )

    for name, test in tests:
        try:
            test()
        except Exception as exc:
            print(
                f"[FAIL] {name}: "
                f"{type(exc).__name__}: {exc}"
            )
            raise
        else:
            print(f"[PASS] {name}")

    print(
        "SAHIBEX 6G-9C ANSWER TRACEABILITY TEST: PASS"
    )

def test_evidence_linked_to_unrelated_finding_is_rejected():
    (
        answer,
        knowledge,
        _finding,
        evidence,
        source,
        _document,
    ) = _build_fixture()

    unrelated_evidence = Evidence(
        evidence_id="evidence_unrelated",
        finding_id="finding_unrelated",
        source_id="source_1",
        evidence_text="Unrelated evidence.",
        supports=True,
        strength=0.90,
    )

    mismatched_knowledge = KnowledgeCandidate(
        knowledge_id="knowledge_1",
        statement="Test claim",
        findings=["finding_1"],
        evidence=["evidence_unrelated"],
        confidence=0.90,
        verified=True,
    )

    result = AnswerTraceabilityEngine().trace_answer(
        answer=answer,
        knowledge_items=[mismatched_knowledge],
        findings=[_finding],
        evidence_items=[evidence, unrelated_evidence],
        sources=[source],
    )

    trace = result.traces[0]
    assert trace.trace_complete is False
    assert trace.evidence_ids == ()
    assert "evidence_finding_mismatch:evidence_unrelated" in (
        trace.missing_links
    )


def test_evidence_linked_to_different_knowledge_is_rejected():
    (
        answer,
        _knowledge,
        finding,
        _evidence,
        source,
        _document,
    ) = _build_fixture()

    mismatched_evidence = Evidence(
        evidence_id="evidence_other_knowledge",
        finding_id="finding_1",
        source_id="source_1",
        evidence_text="Evidence owned by another knowledge record.",
        supports=True,
        strength=0.90,
        metadata={"knowledge_id": "knowledge_other"},
    )

    knowledge = KnowledgeCandidate(
        knowledge_id="knowledge_1",
        statement="Test claim",
        findings=["finding_1"],
        evidence=["evidence_other_knowledge"],
        confidence=0.90,
        verified=True,
    )

    result = AnswerTraceabilityEngine().trace_answer(
        answer=answer,
        knowledge_items=[knowledge],
        findings=[finding],
        evidence_items=[mismatched_evidence],
        sources=[source],
    )

    trace = result.traces[0]
    assert trace.trace_complete is False
    assert trace.evidence_ids == ()
    assert "evidence_knowledge_mismatch:evidence_other_knowledge" in (
        trace.missing_links
    )
