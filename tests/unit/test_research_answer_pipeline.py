from datetime import datetime, timezone

from core.research.answer_pipeline import ResearchAnswerPipeline
from core.research.engine import ResearchEngine
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)
from core.research.query import ResearchQueryEngine
from core.research.storage import ResearchStorage


def now():
    return datetime.now(timezone.utc)


def check(condition, message):
    assert condition, message
    print(f"[PASS] {message}")


def build_verified_knowledge(
    engine,
    statement,
    confidence,
):
    source = ResearchSource(
        source_id=f"src-{len(engine.sources) + 1}",
        title="Test Source",
        source_type="test",
        locator=f"test://source/{len(engine.sources) + 1}",
        publisher="SAHIBEX TEST",
        reliability=0.9,
        accessed_at=now(),
    )

    engine.register_source(source)

    knowledge = KnowledgeCandidate(
        knowledge_id=f"k-{len(engine.knowledge) + 1}",
        statement=statement,
        findings=[],
        evidence=[],
        confidence=confidence,
        verified=True,
        created_at=now(),
        last_verified_at=now(),
        metadata={
            "source_id": source.source_id,
        },
    )

    engine.knowledge[knowledge.knowledge_id] = knowledge

    return knowledge


def test_basic_end_to_end():
    engine = ResearchEngine()

    knowledge = build_verified_knowledge(
        engine,
        "Python is widely used for software development.",
        0.92,
    )

    query_engine = ResearchQueryEngine(engine)

    pipeline = ResearchAnswerPipeline(
        query_engine=query_engine,
    )

    result = pipeline.run("Python software development")

    check(
        result.query_result is not None,
        "query retrieval completed",
    )

    check(
        len(result.query_result.matches) == 1,
        "matching knowledge retrieved",
    )

    check(
        result.aggregation is not None,
        "knowledge aggregation completed",
    )

    check(
        len(result.aggregation.results) == 1,
        "aggregated knowledge available",
    )

    check(
        result.answer is not None,
        "answer synthesis completed",
    )

    check(
        result.answer.knowledge_ids == [knowledge.knowledge_id],
        "knowledge ID preserved through pipeline",
    )

    quality_supports_answer = result.aggregation.answer.overall_status in {
        "SUPPORTED",
        "MULTI_SOURCE_SUPPORTED",
    }
    check(
        result.answer.verified is quality_supports_answer,
        "verified status follows quality-aware evidence assessment",
    )

    check(
        "Python is widely used for software development."
        in result.answer.answer,
        "knowledge statement reached final answer",
    )


def test_multiple_knowledge_end_to_end():
    engine = ResearchEngine()

    first = build_verified_knowledge(
        engine,
        "Python is widely used for software development.",
        0.90,
    )

    second = build_verified_knowledge(
        engine,
        "SQLite is commonly used as a lightweight database.",
        0.85,
    )

    query_engine = ResearchQueryEngine(engine)

    pipeline = ResearchAnswerPipeline(
        query_engine=query_engine,
    )

    result = pipeline.run(
        "Python SQLite software database",
        limit=10,
    )

    ids = result.answer.knowledge_ids

    check(
        first.knowledge_id in ids,
        "first knowledge item reached final answer",
    )

    check(
        second.knowledge_id in ids,
        "second knowledge item reached final answer",
    )

    check(
        len(result.answer.evidence) == 2,
        "multiple knowledge items synthesized",
    )


def test_verified_only_pipeline():
    engine = ResearchEngine()

    verified = build_verified_knowledge(
        engine,
        "Python is widely used for software development.",
        0.95,
    )

    unverified = KnowledgeCandidate(
        knowledge_id="unverified-1",
        statement="Rust is widely used for database administration.",
        findings=[],
        evidence=[],
        confidence=0.80,
        verified=False,
        created_at=now(),
        last_verified_at=None,
        metadata={},
    )

    engine.knowledge[unverified.knowledge_id] = unverified

    query_engine = ResearchQueryEngine(engine)

    pipeline = ResearchAnswerPipeline(
        query_engine=query_engine,
    )

    result = pipeline.run(
        "Python Rust software database",
        verified_only=True,
    )

    ids = result.answer.knowledge_ids

    check(
        verified.knowledge_id in ids,
        "verified knowledge included",
    )

    check(
        unverified.knowledge_id not in ids,
        "unverified knowledge excluded by default",
    )


def test_unverified_explicit_pipeline():
    engine = ResearchEngine()

    unverified = KnowledgeCandidate(
        knowledge_id="unverified-explicit",
        statement="SQLite is commonly used as a lightweight database.",
        findings=[],
        evidence=[],
        confidence=0.70,
        verified=False,
        created_at=now(),
        last_verified_at=None,
        metadata={},
    )

    engine.knowledge[unverified.knowledge_id] = unverified

    query_engine = ResearchQueryEngine(engine)

    pipeline = ResearchAnswerPipeline(
        query_engine=query_engine,
    )

    result = pipeline.run(
        "SQLite lightweight database",
        verified_only=False,
    )

    check(
        unverified.knowledge_id in result.answer.knowledge_ids,
        "explicit unverified retrieval reached final answer",
    )

    check(
        result.answer.verified is False,
        "unverified status preserved",
    )


def test_empty_query_protection():
    engine = ResearchEngine()
    query_engine = ResearchQueryEngine(engine)

    pipeline = ResearchAnswerPipeline(
        query_engine=query_engine,
    )

    try:
        pipeline.run("")
    except ValueError:
        print("[PASS] empty query protection")
    else:
        raise AssertionError("empty query was not rejected")


def test_invalid_limit_protection():
    engine = ResearchEngine()
    query_engine = ResearchQueryEngine(engine)

    pipeline = ResearchAnswerPipeline(
        query_engine=query_engine,
    )

    try:
        pipeline.run("Python", limit=0)
    except ValueError:
        print("[PASS] invalid limit protection")
    else:
        raise AssertionError("invalid limit was not rejected")


def main():
    print("SAHIBEX RESEARCH ANSWER PIPELINE TEST")

    test_basic_end_to_end()
    test_multiple_knowledge_end_to_end()
    test_verified_only_pipeline()
    test_unverified_explicit_pipeline()
    test_empty_query_protection()
    test_invalid_limit_protection()

    print("SAHIBEX RESEARCH ANSWER PIPELINE TEST: PASS")


if __name__ == "__main__":
    main()


def test_ai_safety_query_filters_unrelated_sidebar_claims():
    relevant = KnowledgeCandidate(
        knowledge_id="k-relevant",
        statement="OpenAI's AI agent incident exposed safety and security risks after it accessed a government portal without permission.",
        findings=[],
        evidence=[],
        confidence=0.9,
        verified=True,
        created_at=now(),
        last_verified_at=now(),
        metadata={},
    )
    unrelated = KnowledgeCandidate(
        knowledge_id="k-unrelated",
        statement="Mecka raised $60 million to scale robot data and deployment.",
        findings=[],
        evidence=[],
        confidence=0.9,
        verified=True,
        created_at=now(),
        last_verified_at=now(),
        metadata={},
    )
    items = [relevant, unrelated]
    filtered = ResearchAnswerPipeline._filter_query_relevant_knowledge(
        "आज AI सुरक्षा में क्या नया है?",
        items,
    )
    assert [item.knowledge_id for item in filtered] == ["k-relevant"]


def test_focused_evidence_preserves_knowledge_links_for_freshness_and_traceability():
    engine = ResearchEngine()
    source = ResearchSource(
        source_id="src-live-fresh",
        title="Current AI safety report",
        source_type="web",
        locator="https://publisher.example/current-ai-safety",
        publisher="Publisher Example",
        published_at=now(),
        reliability=0.9,
        accessed_at=now(),
    )
    engine.register_source(source)
    evidence = Evidence(
        evidence_id="ev-current-ai-safety",
        finding_id="finding-current-ai-safety",
        source_id=source.source_id,
        evidence_text="The report describes an AI security incident and mitigation.",
        strength=0.9,
        metadata={"knowledge_id": "k-current-ai-safety"},
    )
    knowledge = KnowledgeCandidate(
        knowledge_id="k-current-ai-safety",
        statement="The report describes an AI security incident and mitigation.",
        findings=[evidence.finding_id],
        evidence=[evidence.evidence_id],
        confidence=0.9,
        verified=True,
        created_at=now(),
        last_verified_at=now(),
        metadata={"source_id": source.source_id},
    )
    engine.knowledge[knowledge.knowledge_id] = knowledge
    pipeline = ResearchAnswerPipeline(ResearchQueryEngine(engine))

    result = pipeline.run(
        "AI security incident",
        verified_only=True,
        evidence_items=[evidence],
        sources=[source],
        focus_on_provided_evidence=True,
    )

    assert result.query_result.total_matches == 1
    assert result.aggregation.results
    # The evidence/source links must survive both focused retrieval and
    # candidate conversion. A single source may still fail the confidence
    # threshold, but it must not be falsely marked stale due to lost links.
    assert result.answer.status != "STALE"
    assert result.aggregation.answer.claims[0].evidence_count == 1
    assert result.aggregation.answer.claims[0].source_count == 1
    assert result.aggregation.answer.claims[0].freshness_score >= 0.4
    assert result.traceability.status == "TRACEABLE"
    assert result.traceability.evidence_count == 1
    assert result.traceability.source_count == 1


def test_non_ai_safety_query_does_not_apply_specialized_filter():
    unrelated = KnowledgeCandidate(
        knowledge_id="k-general",
        statement="Mecka raised $60 million to scale robot data and deployment.",
        findings=[],
        evidence=[],
        confidence=0.9,
        verified=True,
        created_at=now(),
        last_verified_at=now(),
        metadata={},
    )
    assert ResearchAnswerPipeline._filter_query_relevant_knowledge(
        "latest robotics funding news",
        [unrelated],
    ) == [unrelated]
