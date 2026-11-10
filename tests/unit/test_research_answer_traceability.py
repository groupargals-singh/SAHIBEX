from datetime import datetime, timezone

from core.research.answer_pipeline import ResearchAnswerPipeline
from core.research.engine import ResearchEngine
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)
from core.research.query import ResearchQueryEngine


def now():
    return datetime.now(timezone.utc)


def check(condition, message):
    assert condition, message
    print(f"[PASS] {message}")


def make_source(source_id, title, reliability=0.95):
    return ResearchSource(
        source_id=source_id,
        title=title,
        source_type="test",
        locator=f"test://{source_id}",
        publisher="SAHIBEX TEST",
        reliability=reliability,
        accessed_at=now(),
    )


def make_knowledge(
    knowledge_id,
    statement,
    confidence=0.9,
    verified=True,
):
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        findings=[],
        evidence=[],
        confidence=confidence,
        verified=verified,
        created_at=now(),
        last_verified_at=now() if verified else None,
        metadata={"verification_status": "VERIFIED"} if verified else {},
    )


def make_evidence(
    evidence_id,
    finding_id,
    source_id,
    knowledge_id,
    text,
    strength=0.9,
):
    return Evidence(
        evidence_id=evidence_id,
        finding_id=finding_id,
        source_id=source_id,
        evidence_text=text,
        supports=True,
        strength=strength,
        created_at=now(),
        metadata={
            "knowledge_id": knowledge_id,
        },
    )


def test_answer_traceability_integration():
    engine = ResearchEngine()

    source = make_source(
        "src-python",
        "Python Documentation",
        reliability=0.95,
    )

    knowledge = make_knowledge(
        "k-python",
        "Python is widely used for software development.",
        confidence=0.92,
        verified=True,
    )

    evidence = make_evidence(
        "ev-python",
        "finding-python",
        "src-python",
        "k-python",
        "Python documentation describes Python as a programming language.",
        strength=0.93,
    )

    engine.register_source(source)
    engine.knowledge[knowledge.knowledge_id] = knowledge

    query_engine = ResearchQueryEngine(engine)

    pipeline = ResearchAnswerPipeline(
        query_engine=query_engine,
    )

    result = pipeline.run(
        "Python software development",
        evidence_items=[evidence],
        sources=[source],
    )

    # ---------------------------------------------------------
    # Final answer
    # ---------------------------------------------------------

    check(
        result.answer is not None,
        "final answer available",
    )

    check(
        result.answer.knowledge_ids == ["k-python"],
        "final answer knowledge ID preserved",
    )

    quality_supports_answer = result.aggregation.answer.overall_status in {
        "SUPPORTED",
        "MULTI_SOURCE_SUPPORTED",
    }
    check(
        result.answer.verified is quality_supports_answer,
        "final answer verification follows quality-aware assessment",
    )

    # ---------------------------------------------------------
    # Traceability
    # ---------------------------------------------------------

    check(
        result.traceability is not None,
        "traceability attached to final pipeline result",
    )

    check(
        result.traceability.status == "TRACEABLE",
        "final result is traceable",
    )

    check(
        result.traceability.knowledge_count == 1,
        "traceability knowledge count",
    )

    check(
        result.traceability.evidence_count == 1,
        "traceability evidence count",
    )

    check(
        result.traceability.source_count == 1,
        "traceability source count",
    )

    trace = result.traceability.traces[0]

    check(
        trace.knowledge_id == "k-python",
        "trace knowledge ID preserved",
    )

    check(
        trace.evidence[0].evidence_id == "ev-python",
        "trace evidence ID preserved",
    )

    check(
        trace.sources[0].source_id == "src-python",
        "trace source ID preserved",
    )

    check(
        trace.sources[0].reliability == 0.95,
        "source reliability preserved",
    )


def test_unmapped_evidence_does_not_enter_trace():
    engine = ResearchEngine()

    source = make_source(
        "src-test",
        "Test Source",
    )

    knowledge = make_knowledge(
        "k-test",
        "Python is used for software development.",
    )

    unmapped_evidence = Evidence(
        evidence_id="ev-unmapped",
        finding_id="finding-test",
        source_id="src-test",
        evidence_text="Evidence without knowledge mapping.",
        supports=True,
        strength=0.9,
        created_at=now(),
        metadata={},
    )

    engine.register_source(source)
    engine.knowledge[knowledge.knowledge_id] = knowledge

    query_engine = ResearchQueryEngine(engine)

    pipeline = ResearchAnswerPipeline(
        query_engine=query_engine,
    )

    result = pipeline.run(
        "Python software development",
        evidence_items=[unmapped_evidence],
        sources=[source],
    )

    check(
        result.traceability.status == "NO_TRACEABLE_EVIDENCE",
        "unmapped evidence excluded safely",
    )

    check(
        result.traceability.evidence_count == 0,
        "unmapped evidence not falsely attached",
    )


def test_missing_source_is_reported():
    engine = ResearchEngine()

    knowledge = make_knowledge(
        "k-missing-source",
        "Python is used for software development.",
    )

    evidence = make_evidence(
        "ev-missing-source",
        "finding-missing-source",
        "src-does-not-exist",
        "k-missing-source",
        "Evidence whose source is unavailable.",
    )

    engine.knowledge[knowledge.knowledge_id] = knowledge

    query_engine = ResearchQueryEngine(engine)

    pipeline = ResearchAnswerPipeline(
        query_engine=query_engine,
    )

    result = pipeline.run(
        "Python software development",
        evidence_items=[evidence],
        sources=[],
    )

    check(
        result.traceability.status == "EVIDENCE_WITHOUT_SOURCE",
        "missing source reported",
    )

    check(
        result.traceability.evidence_count == 1,
        "evidence retained despite missing source",
    )

    check(
        result.traceability.source_count == 0,
        "missing source not fabricated",
    )


def main():
    print("SAHIBEX RESEARCH ANSWER TRACEABILITY TEST")

    test_answer_traceability_integration()
    test_unmapped_evidence_does_not_enter_trace()
    test_missing_source_is_reported()

    print("SAHIBEX RESEARCH ANSWER TRACEABILITY TEST: PASS")


if __name__ == "__main__":
    main()
