from datetime import datetime, timezone

from core.research.answer_pipeline import ResearchAnswerPipeline
from core.research.engine import ResearchEngine
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)
from core.research.query import ResearchQueryEngine, ResearchQueryResult
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
            "verification_status": "VERIFIED",
        },
    )

    engine.knowledge[knowledge.knowledge_id] = knowledge

    return knowledge


def test_exact_duplicate_claims_share_independent_evidence_in_memory():
    statement = "OpenAI published an AI safety report."
    first = KnowledgeCandidate(
        knowledge_id="k-first",
        statement=statement,
        findings=["f-first"],
        evidence=["e-first"],
        confidence=0.8,
        verified=True,
        created_at=now(),
        last_verified_at=now(),
    )
    second = KnowledgeCandidate(
        knowledge_id="k-second",
        statement=statement.lower(),
        findings=["f-second"],
        evidence=["e-second"],
        confidence=0.8,
        verified=True,
        created_at=now(),
        last_verified_at=now(),
    )
    evidence = [
        Evidence(
            evidence_id="e-first",
            finding_id="f-first",
            source_id="source-a",
            evidence_text=statement,
            strength=0.9,
            metadata={"knowledge_id": "k-first"},
        ),
        Evidence(
            evidence_id="e-second",
            finding_id="f-second",
            source_id="source-b",
            evidence_text=statement.lower(),
            strength=0.9,
            metadata={"knowledge_id": "k-second"},
        ),
    ]

    merged, remapped = ResearchAnswerPipeline._merge_exact_duplicate_claims(
        [first, second],
        evidence,
    )

    assert len(merged) == 1
    assert merged[0].knowledge_id == "k-first"
    assert set(merged[0].evidence) == {"e-first", "e-second"}
    assert {item.metadata["knowledge_id"] for item in remapped} == {"k-first"}
    assert {item.source_id for item in remapped} == {"source-a", "source-b"}
    # The caller's original evidence graph must remain untouched.
    assert evidence[1].metadata["knowledge_id"] == "k-second"


def test_current_research_keeps_only_claims_supported_by_distinct_publishers():
    claim = KnowledgeCandidate(
        knowledge_id="k-corroborated",
        statement="OpenAI published an AI safety report.",
        findings=["f-a", "f-b"],
        evidence=["e-a", "e-b"],
        confidence=0.8,
        verified=True,
        created_at=now(),
    )
    evidence = [
        Evidence(
            evidence_id="e-a", finding_id="f-a", source_id="source-a",
            evidence_text="OpenAI published an AI safety report.",
            strength=0.9, metadata={"knowledge_id": "k-corroborated"},
        ),
        Evidence(
            evidence_id="e-b", finding_id="f-b", source_id="source-b",
            evidence_text="OpenAI published an AI safety report.",
            strength=0.9, metadata={"knowledge_id": "k-corroborated"},
        ),
    ]
    sources = [
        ResearchSource(
            source_id="source-a", title="Publisher A", source_type="web",
            locator="https://publisher-a.example/report", publisher="Publisher A",
            reliability=0.9, accessed_at=now(), published_at=now(),
        ),
        ResearchSource(
            source_id="source-b", title="Publisher B", source_type="web",
            locator="https://publisher-b.example/report", publisher="Publisher B",
            reliability=0.9, accessed_at=now(), published_at=now(),
        ),
    ]

    selected, selected_evidence = ResearchAnswerPipeline._filter_current_claims_to_independent_sources(
        "latest AI safety news", [claim], evidence, sources,
    )

    assert [item.knowledge_id for item in selected] == ["k-corroborated"]
    assert {item.source_id for item in selected_evidence} == {"source-a", "source-b"}


def test_current_research_uses_publisher_identity_for_google_news_wrappers():
    claim = KnowledgeCandidate(
        knowledge_id="k-google-news",
        statement="OpenAI published an AI safety report.",
        findings=["f-a", "f-b"],
        evidence=["e-a", "e-b"],
        confidence=0.8,
        verified=True,
        created_at=now(),
    )
    evidence = [
        Evidence(
            evidence_id="e-a", finding_id="f-a", source_id="source-a",
            evidence_text="OpenAI published an AI safety report.",
            strength=0.9, metadata={"knowledge_id": "k-google-news"},
        ),
        Evidence(
            evidence_id="e-b", finding_id="f-b", source_id="source-b",
            evidence_text="OpenAI published an AI safety report.",
            strength=0.9, metadata={"knowledge_id": "k-google-news"},
        ),
    ]
    sources = [
        ResearchSource(
            source_id="source-a", title="Publisher A", source_type="web",
            locator="https://news.google.com/rss/articles/a", publisher="Publisher A",
            reliability=0.9, accessed_at=now(), published_at=now(),
        ),
        ResearchSource(
            source_id="source-b", title="Publisher B", source_type="web",
            locator="https://news.google.com/rss/articles/b", publisher="Publisher B",
            reliability=0.9, accessed_at=now(), published_at=now(),
        ),
    ]

    selected, selected_evidence = ResearchAnswerPipeline._filter_current_claims_to_independent_sources(
        "latest AI safety news", [claim], evidence, sources,
    )

    assert [item.knowledge_id for item in selected] == ["k-google-news"]
    assert {item.source_id for item in selected_evidence} == {"source-a", "source-b"}


def test_search_query_labels_do_not_collapse_distinct_publisher_domains():
    claim = KnowledgeCandidate(
        knowledge_id="k-search-labels",
        statement="The UK AI Security Institute will test the latest AI models.",
        findings=["f-a", "f-b"],
        evidence=["e-a", "e-b"],
        confidence=0.8,
        verified=False,
        created_at=now(),
    )
    evidence = [
        Evidence(
            evidence_id="e-a", finding_id="f-a", source_id="source-a",
            evidence_text=claim.statement, strength=0.9,
            metadata={"knowledge_id": claim.knowledge_id},
        ),
        Evidence(
            evidence_id="e-b", finding_id="f-b", source_id="source-b",
            evidence_text=claim.statement, strength=0.9,
            metadata={"knowledge_id": claim.knowledge_id},
        ),
    ]
    sources = [
        ResearchSource(
            source_id="source-a", title="UK AI testing story", source_type="web",
            locator="https://konsulteer.com/uk-ai-testing",
            publisher="latest AI security news - BingNews",
            reliability=0.8, accessed_at=now(), published_at=now(),
        ),
        ResearchSource(
            source_id="source-b", title="UK AI testing story", source_type="web",
            locator="https://news9live.com/uk-ai-testing",
            publisher='"latest AI security news when:7d" - Google News',
            reliability=0.8, accessed_at=now(), published_at=now(),
        ),
    ]

    selected, selected_evidence = ResearchAnswerPipeline._filter_current_claims_to_independent_sources(
        "latest AI safety news", [claim], evidence, sources,
    )

    assert [item.knowledge_id for item in selected] == ["k-search-labels"]
    assert {item.source_id for item in selected_evidence} == {"source-a", "source-b"}


def test_current_research_does_not_count_two_urls_from_same_publisher_twice():
    claim = KnowledgeCandidate(
        knowledge_id="k-one-publisher",
        statement="OpenAI published an AI safety report.",
        findings=["f-a", "f-b"],
        evidence=["e-a", "e-b"],
        confidence=0.8,
        verified=True,
        created_at=now(),
    )
    evidence = [
        Evidence(
            evidence_id="e-a", finding_id="f-a", source_id="source-a",
            evidence_text="OpenAI published an AI safety report.",
            strength=0.9, metadata={"knowledge_id": "k-one-publisher"},
        ),
        Evidence(
            evidence_id="e-b", finding_id="f-b", source_id="source-b",
            evidence_text="OpenAI published an AI safety report.",
            strength=0.9, metadata={"knowledge_id": "k-one-publisher"},
        ),
    ]
    sources = [
        ResearchSource(
            source_id="source-a", title="Publisher", source_type="web",
            locator="https://same-publisher.example/report-a", publisher="Same Publisher",
            reliability=0.9, accessed_at=now(), published_at=now(),
        ),
        ResearchSource(
            source_id="source-b", title="Publisher", source_type="web",
            locator="https://same-publisher.example/report-b", publisher="Same Publisher",
            reliability=0.9, accessed_at=now(), published_at=now(),
        ),
    ]

    selected, selected_evidence = ResearchAnswerPipeline._filter_current_claims_to_independent_sources(
        "latest AI safety news", [claim], evidence, sources,
    )

    assert selected == []
    assert selected_evidence == []


def test_near_duplicate_claims_are_not_auto_corroborated():
    first = KnowledgeCandidate(
        knowledge_id="k-first",
        statement="OpenAI fired three AI safety researchers.",
        confidence=0.8,
        verified=True,
        created_at=now(),
    )
    second = KnowledgeCandidate(
        knowledge_id="k-second",
        statement="OpenAI fired four AI safety researchers.",
        confidence=0.8,
        verified=True,
        created_at=now(),
    )

    merged, _ = ResearchAnswerPipeline._merge_exact_duplicate_claims(
        [first, second],
        [],
    )

    assert len(merged) == 2
    assert {item.knowledge_id for item in merged} == {"k-first", "k-second"}


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
    check(
        result.arbitration.accepted is False,
        "unverified synthesis rejected by arbitration",
    )
    check(
        result.answer.status == "ARBITRATION_REJECTED",
        "rejected answer status recorded",
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


def test_ai_safety_relevance_keeps_rogue_agent_claims_without_keyword_safety():
    rogue = KnowledgeCandidate(
        knowledge_id="k-rogue-agent",
        statement="Anthropic AI agents go rogue and submit a fake homicide tip to police.",
        findings=[],
        evidence=[],
        confidence=0.8,
        verified=False,
        created_at=now(),
        last_verified_at=None,
        metadata={},
    )
    unrelated = KnowledgeCandidate(
        knowledge_id="k-model-launch",
        statement="OpenAI announced a new model with faster image generation.",
        findings=[],
        evidence=[],
        confidence=0.8,
        verified=False,
        created_at=now(),
        last_verified_at=None,
        metadata={},
    )
    filtered = ResearchAnswerPipeline._filter_query_relevant_knowledge(
        "आज AI सुरक्षा में क्या नया है?", [rogue, unrelated]
    )
    assert [item.knowledge_id for item in filtered] == ["k-rogue-agent"]


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


def test_verified_paraphrases_merge_only_with_matching_numbers_and_independent_hosts():
    first = KnowledgeCandidate(
        knowledge_id="k-india-a",
        statement="India will release an AI regulation consultation paper within 30 days, said Vaishnaw.",
        findings=["f-a"], evidence=["e-a"], confidence=0.8, verified=True,
        created_at=now(), last_verified_at=now(),
    )
    second = KnowledgeCandidate(
        knowledge_id="k-india-b",
        statement="The Centre plans to publish an AI regulation consultation paper within 30 days, according to Vaishnaw.",
        findings=["f-b"], evidence=["e-b"], confidence=0.8, verified=True,
        created_at=now(), last_verified_at=now(),
    )
    evidence = [
        Evidence(evidence_id="e-a", finding_id="f-a", source_id="source-a",
                 evidence_text=first.statement, metadata={"knowledge_id": "k-india-a"}),
        Evidence(evidence_id="e-b", finding_id="f-b", source_id="source-b",
                 evidence_text=second.statement, metadata={"knowledge_id": "k-india-b"}),
    ]
    sources = [
        ResearchSource(source_id="source-a", title="Publisher A", source_type="web",
                       locator="https://publisher-a.example/report", reliability=0.9),
        ResearchSource(source_id="source-b", title="Publisher B", source_type="web",
                       locator="https://publisher-b.example/report", reliability=0.9),
    ]

    merged, remapped = ResearchAnswerPipeline._merge_verified_claim_paraphrases(
        [first, second], evidence, sources,
    )

    assert len(merged) == 1
    assert set(merged[0].evidence) == {"e-a", "e-b"}
    assert {item.metadata["knowledge_id"] for item in remapped} == {"k-india-a"}
    assert {item.source_id for item in remapped} == {"source-a", "source-b"}


def test_unverified_candidate_paraphrases_link_evidence_without_promoting_truth():
    first = KnowledgeCandidate(
        knowledge_id="k-candidate-a",
        statement="Anthropic AI agents may exploit unsafe tool permissions during autonomous tasks within 30 days.",
        findings=["f-candidate-a"], evidence=["e-candidate-a"], confidence=0.62,
        verified=False, created_at=now(),
    )
    second = KnowledgeCandidate(
        knowledge_id="k-candidate-b",
        statement="Anthropic AI agents may misuse unsafe tool permissions during autonomous tasks within 30 days.",
        findings=["f-candidate-b"], evidence=["e-candidate-b"], confidence=0.61,
        verified=False, created_at=now(),
    )
    evidence = [
        Evidence(evidence_id="e-candidate-a", finding_id="f-candidate-a", source_id="source-a",
                 evidence_text=first.statement, metadata={"knowledge_id": "k-candidate-a"}),
        Evidence(evidence_id="e-candidate-b", finding_id="f-candidate-b", source_id="source-b",
                 evidence_text=second.statement, metadata={"knowledge_id": "k-candidate-b"}),
    ]
    sources = [
        ResearchSource(source_id="source-a", title="Publisher A", source_type="web",
                       locator="https://publisher-a.example/report", reliability=0.9),
        ResearchSource(source_id="source-b", title="Publisher B", source_type="web",
                       locator="https://publisher-b.example/report", reliability=0.9),
    ]

    merged, remapped = ResearchAnswerPipeline._merge_verified_claim_paraphrases(
        [first, second], evidence, sources,
    )

    assert len(merged) == 1
    assert merged[0].verified is False
    assert set(merged[0].evidence) == {"e-candidate-a", "e-candidate-b"}
    assert {item.metadata["knowledge_id"] for item in remapped} == {"k-candidate-a"}
    assert {item.source_id for item in remapped} == {"source-a", "source-b"}


def test_independent_reports_link_same_cert_in_data_exposure_claim():
    first = KnowledgeCandidate(
        knowledge_id="k-firstpost-records",
        statement=(
            "The Indian Computer Emergency Response Team (CERT-In) said the "
            "unauthorised activity exposed business records containing personal "
            "information and confidential material."
        ),
        findings=["f-firstpost-records"],
        evidence=["e-firstpost-records"],
        confidence=0.7,
        verified=False,
        created_at=now(),
    )
    second = KnowledgeCandidate(
        knowledge_id="k-digit-records",
        statement=(
            "Not only that, but it also started reading sensitive business "
            "records, personal data and confidential information."
        ),
        findings=["f-digit-records"],
        evidence=["e-digit-records"],
        confidence=0.7,
        verified=False,
        created_at=now(),
    )
    evidence = [
        Evidence(
            evidence_id="e-firstpost-records",
            finding_id="f-firstpost-records",
            source_id="source-firstpost",
            evidence_text=first.statement,
            metadata={"knowledge_id": first.knowledge_id},
        ),
        Evidence(
            evidence_id="e-digit-records",
            finding_id="f-digit-records",
            source_id="source-digit",
            evidence_text=second.statement,
            metadata={"knowledge_id": second.knowledge_id},
        ),
        Evidence(
            evidence_id="e-digit-context",
            finding_id="f-digit-context",
            source_id="source-digit",
            evidence_text="CERT-In issued an advisory after AI agents accessed business records.",
            metadata={"knowledge_id": "k-digit-context"},
        ),
    ]
    sources = [
        ResearchSource(
            source_id="source-firstpost",
            title="CERT-In warns of AI agents accessing Indian organisations’ data without permission",
            source_type="web",
            locator="https://www.firstpost.com/tech/ai-agents-cert-in-report",
            publisher="latest AI security news - BingNews",
            reliability=0.85,
        ),
        ResearchSource(
            source_id="source-digit",
            title="After OpenAI and Hugging Face breach, rogue AI agents hack Indian firm servers",
            source_type="web",
            locator="https://www.digit.in/news/ai-agents-cert-in-report",
            publisher='"latest AI security news when:7d" - Google News',
            reliability=0.85,
        ),
    ]

    diagnostics = {}
    merged, remapped = ResearchAnswerPipeline._merge_verified_claim_paraphrases(
        [first, second],
        evidence,
        sources,
        diagnostics=diagnostics,
    )

    assert diagnostics["candidate_pairs_considered"] == 1
    assert diagnostics.get("linked_pairs", 0) == 1, diagnostics
    assert len(merged) == 1
    assert merged[0].verified is False
    assert set(merged[0].evidence) == {"e-firstpost-records", "e-digit-records"}
    assert {item.metadata.get("knowledge_id") for item in remapped} == {
        merged[0].knowledge_id,
        "k-digit-context",
    }


def test_verified_paraphrase_merger_rejects_conflicting_numbers():
    first = KnowledgeCandidate(
        knowledge_id="k-days-a",
        statement="India will release an AI regulation consultation paper within 30 days, said Vaishnaw.",
        findings=["f-a"], evidence=["e-a"], confidence=0.8, verified=True, created_at=now(),
    )
    second = KnowledgeCandidate(
        knowledge_id="k-days-b",
        statement="The Centre plans to publish an AI regulation consultation paper within 60 days, according to Vaishnaw.",
        findings=["f-b"], evidence=["e-b"], confidence=0.8, verified=True, created_at=now(),
    )
    evidence = [
        Evidence(evidence_id="e-a", finding_id="f-a", source_id="source-a",
                 evidence_text=first.statement, metadata={"knowledge_id": "k-days-a"}),
        Evidence(evidence_id="e-b", finding_id="f-b", source_id="source-b",
                 evidence_text=second.statement, metadata={"knowledge_id": "k-days-b"}),
    ]
    sources = [
        ResearchSource(source_id="source-a", title="Publisher A", source_type="web",
                       locator="https://publisher-a.example/report", reliability=0.9),
        ResearchSource(source_id="source-b", title="Publisher B", source_type="web",
                       locator="https://publisher-b.example/report", reliability=0.9),
    ]

    merged, remapped = ResearchAnswerPipeline._merge_verified_claim_paraphrases(
        [first, second], evidence, sources,
    )

    assert len(merged) == 2
    assert {item.metadata["knowledge_id"] for item in remapped} == {"k-days-a", "k-days-b"}


def test_ai_safety_relevance_uses_linked_source_title_for_context_without_admitting_sidebar_noise():
    relevant = KnowledgeCandidate(
        knowledge_id="k-contextual-safety",
        statement="The company said it encouraged employees raising safety concerns.",
        findings=["f-contextual"],
        evidence=["e-contextual"],
        confidence=0.7,
        verified=False,
        created_at=now(),
        last_verified_at=None,
        metadata={},
    )
    unrelated = KnowledgeCandidate(
        knowledge_id="k-contextual-sidebar",
        statement="Mecka raised $60 million to scale robot data and deployment.",
        findings=["f-sidebar"],
        evidence=["e-sidebar"],
        confidence=0.7,
        verified=False,
        created_at=now(),
        last_verified_at=None,
        metadata={},
    )
    source = ResearchSource(
        source_id="src-ai-safety-context",
        title="OpenAI defends firing of 3 AI safety researchers",
        source_type="web",
        locator="https://publisher.example/openai-safety-researchers",
        publisher="Publisher Example",
        reliability=0.9,
        accessed_at=now(),
        published_at=now(),
    )
    evidence = [
        Evidence(
            evidence_id="e-contextual",
            finding_id="f-contextual",
            source_id=source.source_id,
            evidence_text=relevant.statement,
            metadata={"knowledge_id": relevant.knowledge_id},
        ),
        Evidence(
            evidence_id="e-sidebar",
            finding_id="f-sidebar",
            source_id=source.source_id,
            evidence_text=unrelated.statement,
            metadata={"knowledge_id": unrelated.knowledge_id},
        ),
    ]

    filtered = ResearchAnswerPipeline._filter_query_relevant_knowledge(
        "आज AI सुरक्षा में क्या नया है?",
        [relevant, unrelated],
        evidence_items=evidence,
        sources=[source],
    )

    assert [item.knowledge_id for item in filtered] == ["k-contextual-safety"]


def test_current_research_diagnostics_distinguish_relevance_from_corroboration():
    engine = ResearchEngine()
    source = ResearchSource(
        source_id="src-current-single",
        title="OpenAI publishes AI safety incident update",
        source_type="web",
        locator="https://publisher-one.example/ai-safety-update",
        publisher="Publisher One",
        reliability=0.9,
        accessed_at=now(),
        published_at=now(),
    )
    engine.register_source(source)
    knowledge = KnowledgeCandidate(
        knowledge_id="k-current-single",
        statement="OpenAI disclosed an AI safety incident and its mitigation.",
        findings=["f-current-single"],
        evidence=["e-current-single"],
        confidence=0.8,
        verified=True,
        created_at=now(),
        last_verified_at=now(),
        metadata={},
    )
    engine.knowledge[knowledge.knowledge_id] = knowledge
    evidence = Evidence(
        evidence_id="e-current-single",
        finding_id="f-current-single",
        source_id=source.source_id,
        evidence_text=knowledge.statement,
        strength=0.9,
        metadata={"knowledge_id": knowledge.knowledge_id},
    )
    pipeline = ResearchAnswerPipeline(ResearchQueryEngine(engine))

    result = pipeline.run(
        "latest AI safety news",
        verified_only=True,
        evidence_items=[evidence],
        sources=[source],
        focus_on_provided_evidence=True,
    )

    assert result.relevance_candidate_count == 1
    assert result.corroborated_candidate_count == 0
    assert result.query_result.total_matches == 0
    assert result.answer.verified is False


def test_stable_query_terms_link_longer_paraphrases_with_shared_entities():
    first = KnowledgeCandidate(
        knowledge_id="k-capital-long-a",
        statement="New Delhi is a city and the capital city of India and part of the National Capital Territory of Delhi.",
        findings=["f-capital-long-a"],
        evidence=["e-capital-long-a"],
        confidence=0.8,
        verified=False,
        created_at=now(),
    )
    second = KnowledgeCandidate(
        knowledge_id="k-capital-long-b",
        statement="20°E New Delhi, capital of India; population and elevation details.",
        findings=["f-capital-long-b"],
        evidence=["e-capital-long-b"],
        confidence=0.8,
        verified=False,
        created_at=now(),
    )
    evidence = [
        Evidence(evidence_id="e-capital-long-a", finding_id="f-capital-long-a", source_id="source-capital-long-a", evidence_text=first.statement, metadata={"knowledge_id": first.knowledge_id}),
        Evidence(evidence_id="e-capital-long-b", finding_id="f-capital-long-b", source_id="source-capital-long-b", evidence_text=second.statement, metadata={"knowledge_id": second.knowledge_id}),
    ]
    sources = [
        ResearchSource(source_id="source-capital-long-a", title="India capital overview", source_type="web", locator="https://publisher-a.example/india-capital", reliability=0.9),
        ResearchSource(source_id="source-capital-long-b", title="New Delhi facts", source_type="web", locator="https://publisher-b.example/new-delhi", reliability=0.9),
    ]

    diagnostics = {}
    merged, remapped = ResearchAnswerPipeline._merge_verified_claim_paraphrases(
        [first, second], evidence, sources,
        diagnostics=diagnostics,
        query="What is the capital of India?",
    )

    assert diagnostics["linked_pairs"] == 1
    assert len(merged) == 1
    assert merged[0].verified is False
    assert set(merged[0].evidence) == {"e-capital-long-a", "e-capital-long-b"}
    assert {item.source_id for item in remapped} == {"source-capital-long-a", "source-capital-long-b"}


def test_concise_stable_fact_paraphrases_link_only_with_strong_entity_overlap():
    first = KnowledgeCandidate(
        knowledge_id="k-capital-a",
        statement="New Delhi is the capital of India.",
        findings=["f-capital-a"],
        evidence=["e-capital-a"],
        confidence=0.8,
        verified=False,
        created_at=now(),
    )
    second = KnowledgeCandidate(
        knowledge_id="k-capital-b",
        statement="Delhi is India's capital.",
        findings=["f-capital-b"],
        evidence=["e-capital-b"],
        confidence=0.8,
        verified=False,
        created_at=now(),
    )
    evidence = [
        Evidence(evidence_id="e-capital-a", finding_id="f-capital-a", source_id="source-capital-a", evidence_text=first.statement, metadata={"knowledge_id": first.knowledge_id}),
        Evidence(evidence_id="e-capital-b", finding_id="f-capital-b", source_id="source-capital-b", evidence_text=second.statement, metadata={"knowledge_id": second.knowledge_id}),
    ]
    sources = [
        ResearchSource(source_id="source-capital-a", title="India capital overview", source_type="web", locator="https://publisher-a.example/india-capital", reliability=0.9),
        ResearchSource(source_id="source-capital-b", title="New Delhi facts", source_type="web", locator="https://publisher-b.example/new-delhi", reliability=0.9),
    ]

    diagnostics = {}
    merged, remapped = ResearchAnswerPipeline._merge_verified_claim_paraphrases(
        [first, second], evidence, sources, diagnostics=diagnostics
    )

    assert diagnostics["linked_pairs"] == 1
    assert len(merged) == 1
    assert merged[0].verified is False
    assert set(merged[0].evidence) == {"e-capital-a", "e-capital-b"}
    assert {item.source_id for item in remapped} == {"source-capital-a", "source-capital-b"}


def test_contextual_paraphrase_links_same_ai_incident_across_publishers_without_truth_promotion():
    first = KnowledgeCandidate(
        knowledge_id="k-police-tip-a",
        statement="In one instance, its AI model sent a fake homicide tip to a Philadelphia police website, reportedly making it the first known case of an AI agent providing a false tip to authorities.",
        findings=["f-police-tip-a"],
        evidence=["e-police-tip-a"],
        confidence=0.78,
        verified=False,
        created_at=now(),
    )
    second = KnowledgeCandidate(
        knowledge_id="k-police-tip-b",
        statement="In other words, the AI sent incorrect information to a real police tip website during a test.",
        findings=["f-police-tip-b"],
        evidence=["e-police-tip-b"],
        confidence=0.75,
        verified=False,
        created_at=now(),
    )
    evidence = [
        Evidence(
            evidence_id="e-police-tip-a",
            finding_id="f-police-tip-a",
            source_id="source-livemint",
            evidence_text=first.statement,
            metadata={"knowledge_id": first.knowledge_id},
        ),
        Evidence(
            evidence_id="e-police-tip-b",
            finding_id="f-police-tip-b",
            source_id="source-note",
            evidence_text=second.statement,
            metadata={"knowledge_id": second.knowledge_id},
        ),
    ]
    sources = [
        ResearchSource(
            source_id="source-livemint",
            title="Anthropic's AI agents go rogue: From sending a fake homicide tip to police",
            source_type="web",
            locator="https://www.livemint.com/ai/artificial-intelligence/story",
            reliability=0.9,
        ),
        ResearchSource(
            source_id="source-note",
            title="October 10 AI News Flash: Anthropic AI Misinformation Incident",
            source_type="web",
            locator="https://note.com/publisher/story",
            reliability=0.7,
        ),
    ]

    diagnostics = {}
    merged, remapped = ResearchAnswerPipeline._merge_verified_claim_paraphrases(
        [first, second],
        evidence,
        sources,
        diagnostics=diagnostics,
    )

    assert diagnostics["candidate_pairs_considered"] == 1
    assert diagnostics["linked_pairs"] == 1
    assert len(merged) == 1
    assert merged[0].verified is False
    assert set(merged[0].evidence) == {"e-police-tip-a", "e-police-tip-b"}
    assert {item.metadata["knowledge_id"] for item in remapped} == {"k-police-tip-a"}
    assert {item.source_id for item in remapped} == {"source-livemint", "source-note"}


def test_contextual_paraphrase_does_not_merge_negated_counterclaim():
    first = KnowledgeCandidate(
        knowledge_id="k-police-negation-a",
        statement="The AI sent a fake police tip to a website during a test.",
        findings=["f-negation-a"],
        evidence=["e-negation-a"],
        confidence=0.8,
        verified=True,
        created_at=now(),
        last_verified_at=now(),
    )
    second = KnowledgeCandidate(
        knowledge_id="k-police-negation-b",
        statement="The AI did not send a fake police tip to a website during a test.",
        findings=["f-negation-b"],
        evidence=["e-negation-b"],
        confidence=0.8,
        verified=True,
        created_at=now(),
        last_verified_at=now(),
    )
    evidence = [
        Evidence(
            evidence_id="e-negation-a",
            finding_id="f-negation-a",
            source_id="source-negation-a",
            evidence_text=first.statement,
            metadata={"knowledge_id": first.knowledge_id},
        ),
        Evidence(
            evidence_id="e-negation-b",
            finding_id="f-negation-b",
            source_id="source-negation-b",
            evidence_text=second.statement,
            metadata={"knowledge_id": second.knowledge_id},
        ),
    ]
    sources = [
        ResearchSource(
            source_id="source-negation-a",
            title="Anthropic AI agent sent a false police tip",
            source_type="web",
            locator="https://publisher-a.example/incident",
            reliability=0.9,
        ),
        ResearchSource(
            source_id="source-negation-b",
            title="Anthropic AI agent police-tip incident report",
            source_type="web",
            locator="https://publisher-b.example/incident",
            reliability=0.9,
        ),
    ]

    merged, remapped = ResearchAnswerPipeline._merge_verified_claim_paraphrases(
        [first, second], evidence, sources
    )

    assert len(merged) == 2
    assert {item.metadata["knowledge_id"] for item in remapped} == {
        "k-police-negation-a",
        "k-police-negation-b",
    }


def test_current_research_does_not_count_same_publisher_across_domains_twice():
    claim = KnowledgeCandidate(
        knowledge_id="k-cross-domain-publisher",
        statement="OpenAI published an AI safety report.",
        findings=["f-cross-a", "f-cross-b"],
        evidence=["e-cross-a", "e-cross-b"],
        confidence=0.8,
        verified=True,
        created_at=now(),
    )
    evidence = [
        Evidence(
            evidence_id="e-cross-a",
            finding_id="f-cross-a",
            source_id="source-cross-a",
            evidence_text=claim.statement,
            strength=0.9,
            metadata={"knowledge_id": claim.knowledge_id},
        ),
        Evidence(
            evidence_id="e-cross-b",
            finding_id="f-cross-b",
            source_id="source-cross-b",
            evidence_text=claim.statement,
            strength=0.9,
            metadata={"knowledge_id": claim.knowledge_id},
        ),
    ]
    sources = [
        ResearchSource(
            source_id="source-cross-a",
            title="Publisher report",
            source_type="web",
            locator="https://publisher.example/report",
            publisher="Example News Group",
            reliability=0.9,
            accessed_at=now(),
            published_at=now(),
        ),
        ResearchSource(
            source_id="source-cross-b",
            title="Publisher report",
            source_type="web",
            locator="https://publisher-other.example/report",
            publisher="Example News Group",
            reliability=0.9,
            accessed_at=now(),
            published_at=now(),
        ),
    ]

    selected, selected_evidence = (
        ResearchAnswerPipeline._filter_current_claims_to_independent_sources(
            "latest AI safety news",
            [claim],
            evidence,
            sources,
        )
    )

    assert selected == []
    assert selected_evidence == []


def test_current_research_does_not_count_same_domain_with_different_publishers_twice():
    claim = KnowledgeCandidate(
        knowledge_id="k-same-domain",
        statement="OpenAI published an AI safety report.",
        findings=["f-domain-a", "f-domain-b"],
        evidence=["e-domain-a", "e-domain-b"],
        confidence=0.8,
        verified=True,
        created_at=now(),
    )
    evidence = [
        Evidence(
            evidence_id="e-domain-a",
            finding_id="f-domain-a",
            source_id="source-domain-a",
            evidence_text=claim.statement,
            strength=0.9,
            metadata={"knowledge_id": claim.knowledge_id},
        ),
        Evidence(
            evidence_id="e-domain-b",
            finding_id="f-domain-b",
            source_id="source-domain-b",
            evidence_text=claim.statement,
            strength=0.9,
            metadata={"knowledge_id": claim.knowledge_id},
        ),
    ]
    sources = [
        ResearchSource(
            source_id="source-domain-a",
            title="Report A",
            source_type="web",
            locator="https://same-publisher.example/report-a",
            publisher="Publisher A",
            reliability=0.9,
            accessed_at=now(),
            published_at=now(),
        ),
        ResearchSource(
            source_id="source-domain-b",
            title="Report B",
            source_type="web",
            locator="https://same-publisher.example/report-b",
            publisher="Publisher B",
            reliability=0.9,
            accessed_at=now(),
            published_at=now(),
        ),
    ]

    selected, selected_evidence = (
        ResearchAnswerPipeline._filter_current_claims_to_independent_sources(
            "latest AI safety news",
            [claim],
            evidence,
            sources,
        )
    )

    assert selected == []
    assert selected_evidence == []


def test_malformed_source_url_does_not_crash_independent_corroboration():
    claim = KnowledgeCandidate(
        knowledge_id="k-malformed-url",
        statement="A current research claim needs independent support.",
        findings=["f-malformed", "f-valid"],
        evidence=["e-malformed", "e-valid"],
        confidence=0.8,
        verified=True,
        created_at=now(),
    )
    evidence = [
        Evidence(
            evidence_id="e-malformed",
            finding_id="f-malformed",
            source_id="source-malformed",
            evidence_text=claim.statement,
            strength=0.9,
            metadata={"knowledge_id": claim.knowledge_id},
        ),
        Evidence(
            evidence_id="e-valid",
            finding_id="f-valid",
            source_id="source-valid",
            evidence_text=claim.statement,
            strength=0.9,
            metadata={"knowledge_id": claim.knowledge_id},
        ),
    ]
    sources = [
        ResearchSource(
            source_id="source-malformed",
            title="Malformed source",
            source_type="web",
            locator="https://[broken",
            publisher="",
            reliability=0.9,
            accessed_at=now(),
        ),
        ResearchSource(
            source_id="source-valid",
            title="Valid source",
            source_type="web",
            locator="https://valid-publisher.example/report",
            publisher="Valid Publisher",
            reliability=0.9,
            accessed_at=now(),
        ),
    ]

    selected, selected_evidence = (
        ResearchAnswerPipeline._filter_current_claims_to_independent_sources(
            "latest AI safety news",
            [claim],
            evidence,
            sources,
        )
    )

    assert selected == []
    assert selected_evidence == []


def test_paraphrase_linkers_do_not_count_one_publisher_on_two_domains_twice():
    first = KnowledgeCandidate(
        knowledge_id="k-shared-publisher-a",
        statement="India will release an AI regulation consultation paper within 30 days, said Vaishnaw.",
        findings=["f-shared-a"],
        evidence=["e-shared-a"],
        confidence=0.8,
        verified=True,
        created_at=now(),
        last_verified_at=now(),
    )
    second = KnowledgeCandidate(
        knowledge_id="k-shared-publisher-b",
        statement="The Centre plans to publish an AI regulation consultation paper within 30 days, according to Vaishnaw.",
        findings=["f-shared-b"],
        evidence=["e-shared-b"],
        confidence=0.8,
        verified=True,
        created_at=now(),
        last_verified_at=now(),
    )
    evidence = [
        Evidence(
            evidence_id="e-shared-a",
            finding_id="f-shared-a",
            source_id="source-shared-a",
            evidence_text=first.statement,
            metadata={"knowledge_id": first.knowledge_id},
        ),
        Evidence(
            evidence_id="e-shared-b",
            finding_id="f-shared-b",
            source_id="source-shared-b",
            evidence_text=second.statement,
            metadata={"knowledge_id": second.knowledge_id},
        ),
    ]
    sources = [
        ResearchSource(
            source_id="source-shared-a",
            title="Publisher report A",
            source_type="web",
            locator="https://publisher-one.example/report-a",
            publisher="Same Publisher Group",
            reliability=0.9,
        ),
        ResearchSource(
            source_id="source-shared-b",
            title="Publisher report B",
            source_type="web",
            locator="https://publisher-two.example/report-b",
            publisher="Same Publisher Group",
            reliability=0.9,
        ),
    ]

    verified_merged, verified_remapped = (
        ResearchAnswerPipeline._merge_verified_claim_paraphrases(
            [first, second], evidence, sources
        )
    )
    conservative_merged, conservative_remapped = (
        ResearchAnswerPipeline._merge_conservatively_paraphrased_claims(
            [first, second], evidence, sources
        )
    )

    assert len(verified_merged) == 2
    assert {
        item.metadata["knowledge_id"] for item in verified_remapped
    } == {first.knowledge_id, second.knowledge_id}
    assert len(conservative_merged) == 2
    assert {
        item.metadata["knowledge_id"] for item in conservative_remapped
    } == {first.knowledge_id, second.knowledge_id}


def test_paraphrase_linking_allows_overlapping_sets_with_two_independent_publishers():
    first = KnowledgeCandidate(
        knowledge_id="k-overlap-a",
        statement="Anthropic AI agent sent a fake homicide tip to a Philadelphia police website during testing.",
        findings=["f-overlap-a"],
        evidence=["e-overlap-a1", "e-overlap-a2"],
        confidence=0.8,
        verified=False,
        created_at=now(),
    )
    second = KnowledgeCandidate(
        knowledge_id="k-overlap-b",
        statement="Anthropic AI agent sent a fake homicide tip to a Philadelphia police website during a test.",
        findings=["f-overlap-b"],
        evidence=["e-overlap-b1", "e-overlap-b2"],
        confidence=0.8,
        verified=False,
        created_at=now(),
    )
    evidence = [
        Evidence(evidence_id="e-overlap-a1", finding_id="f-overlap-a", source_id="source-overlap-one", evidence_text=first.statement, metadata={"knowledge_id": first.knowledge_id}),
        Evidence(evidence_id="e-overlap-a2", finding_id="f-overlap-a", source_id="source-overlap-two", evidence_text=first.statement, metadata={"knowledge_id": first.knowledge_id}),
        Evidence(evidence_id="e-overlap-b1", finding_id="f-overlap-b", source_id="source-overlap-one", evidence_text=second.statement, metadata={"knowledge_id": second.knowledge_id}),
        Evidence(evidence_id="e-overlap-b2", finding_id="f-overlap-b", source_id="source-overlap-two", evidence_text=second.statement, metadata={"knowledge_id": second.knowledge_id}),
    ]
    sources = [
        ResearchSource(source_id="source-overlap-one", title="Anthropic safety incident report", source_type="web", locator="https://publisher-one.example/report", publisher="Publisher One", reliability=0.9),
        ResearchSource(source_id="source-overlap-two", title="Anthropic safety incident coverage", source_type="web", locator="https://publisher-two.example/report", publisher="Publisher Two", reliability=0.9),
    ]
    diagnostics = {}

    merged, remapped = ResearchAnswerPipeline._merge_verified_claim_paraphrases(
        [first, second], evidence, sources, diagnostics=diagnostics
    )

    assert diagnostics["source_identity_count"] == 2
    assert diagnostics["evidence_source_identity_count"] == 2
    assert diagnostics["candidate_pairs_considered"] == 1
    assert diagnostics["linked_pairs"] == 1
    assert len(merged) == 1
    assert merged[0].verified is False
    assert {item.metadata["knowledge_id"] for item in remapped} == {"k-overlap-a"}


def test_ai_safety_relevance_uses_headline_context_for_testing_event_claims_only():
    assert ResearchAnswerPipeline._ai_safety_claim_is_relevant(
        "The UK gained access to the latest AI models.",
        "UK AI Safety Institute testing latest AI models",
    )
    assert not ResearchAnswerPipeline._ai_safety_claim_is_relevant(
        "Mecka raised $60 million to scale robot data and deployment.",
        "UK AI Safety Institute testing latest AI models",
    )


def test_contextual_paraphrase_links_uk_aisi_model_testing_event_across_publishers():
    first = KnowledgeCandidate(
        knowledge_id="k-aisi-event-a",
        statement="UK AISI gained access to latest models for safety testing before release.",
        findings=["f-aisi-event-a"],
        evidence=["e-aisi-event-a"],
        confidence=0.7,
        verified=False,
        created_at=now(),
    )
    second = KnowledgeCandidate(
        knowledge_id="k-aisi-event-b",
        statement="Britain's AI Security Institute has access to latest models to evaluate safeguards before release.",
        findings=["f-aisi-event-b"],
        evidence=["e-aisi-event-b"],
        confidence=0.7,
        verified=False,
        created_at=now(),
    )
    evidence = [
        Evidence(
            evidence_id="e-aisi-event-a",
            finding_id="f-aisi-event-a",
            source_id="source-aisi-a",
            evidence_text=first.statement,
            metadata={"knowledge_id": first.knowledge_id},
        ),
        Evidence(
            evidence_id="e-aisi-event-b",
            finding_id="f-aisi-event-b",
            source_id="source-aisi-b",
            evidence_text=second.statement,
            metadata={"knowledge_id": second.knowledge_id},
        ),
    ]
    sources = [
        ResearchSource(
            source_id="source-aisi-a",
            title="UK AI Security Institute gains access to latest models for safety testing",
            source_type="web",
            locator="https://publisher-a.example/uk-aisi-testing",
            reliability=0.7,
        ),
        ResearchSource(
            source_id="source-aisi-b",
            title="AI Security Institute evaluates latest models and safeguards",
            source_type="web",
            locator="https://publisher-b.example/aisi-evaluations",
            reliability=0.7,
        ),
    ]
    diagnostics = {}
    merged, remapped = ResearchAnswerPipeline._merge_verified_claim_paraphrases(
        [first, second], evidence, sources, diagnostics=diagnostics
    )
    assert diagnostics["linked_pairs"] == 1, diagnostics
    assert len(merged) == 1
    assert merged[0].verified is False
    assert {item.source_id for item in remapped} == {"source-aisi-a", "source-aisi-b"}


def test_fresh_focused_evidence_can_reach_verification_without_history():
    class PendingLifecycleStorage:
        def knowledge_verification_lifecycle(self, knowledge_id):
            return {"verification_event_count": 0, "verification_status": "PENDING"}

        def knowledge_verification_context(self, knowledge_id):
            return {"conflict_status": "CLEAR", "unresolved_conflict_count": 0}

    engine = ResearchEngine()
    source = ResearchSource(
        source_id="src-new-evidence", title="AI security incident report",
        source_type="web", locator="https://publisher.example/ai-security-report",
        publisher="Publisher Example", reliability=0.9, published_at=now(), accessed_at=now(),
    )
    engine.register_source(source)
    evidence = Evidence(
        evidence_id="ev-new-evidence", finding_id="finding-new-evidence",
        source_id=source.source_id,
        evidence_text="The AI security report describes a newly identified incident and mitigation.",
        strength=0.9, metadata={"knowledge_id": "k-new-evidence"},
    )
    knowledge = KnowledgeCandidate(
        knowledge_id="k-new-evidence",
        statement="The AI security report describes a newly identified incident and mitigation.",
        findings=[evidence.finding_id], evidence=[evidence.evidence_id],
        confidence=0.9, verified=True, created_at=now(), last_verified_at=now(),
        metadata={"source_id": source.source_id},
    )
    engine.knowledge[knowledge.knowledge_id] = knowledge
    query_engine = ResearchQueryEngine(engine, storage=PendingLifecycleStorage())
    pipeline = ResearchAnswerPipeline(query_engine)

    result = pipeline.run(
        "AI security incident", verified_only=True, evidence_items=[evidence],
        sources=[source], focus_on_provided_evidence=True,
    )

    assert result.corroborated_candidate_count == 1
    assert result.query_result.total_matches == 1
    assert result.traceability.status == "TRACEABLE"


def test_current_research_runs_isolated_claim_verifier_after_independent_corroboration():
    engine = ResearchEngine()
    statement = "The AI security institute tested the latest models and found no critical vulnerabilities."
    sources = [
        ResearchSource(
            source_id="src-live-verify-a", title="AI security institute tests latest models",
            source_type="web", locator="https://publisher-a.example/ai-security-testing",
            publisher="Publisher A", reliability=0.9, published_at=now(), accessed_at=now(),
        ),
        ResearchSource(
            source_id="src-live-verify-b", title="Latest AI security model testing results",
            source_type="web", locator="https://publisher-b.example/model-testing",
            publisher="Publisher B", reliability=0.9, published_at=now(), accessed_at=now(),
        ),
    ]
    evidence_items = []
    for index, source in enumerate(sources):
        engine.register_source(source)
        kid = f"k-live-verify-{index}"
        fid = f"f-live-verify-{index}"
        eid = f"e-live-verify-{index}"
        evidence_items.append(Evidence(
            evidence_id=eid, finding_id=fid, source_id=source.source_id,
            evidence_text=statement, strength=0.9, supports=True,
            metadata={"knowledge_id": kid},
        ))
        engine.knowledge[kid] = KnowledgeCandidate(
            knowledge_id=kid, statement=statement, findings=[fid], evidence=[eid],
            confidence=0.9, verified=False, created_at=now(), metadata={"source_id": source.source_id},
        )
    pipeline = ResearchAnswerPipeline(ResearchQueryEngine(engine))
    result = pipeline.run(
        "latest AI security testing", verified_only=True,
        evidence_items=evidence_items, sources=sources, focus_on_provided_evidence=True,
    )
    assert result.claim_link_diagnostics["verification_engine_checked"] >= 1
    assert result.claim_link_diagnostics["verification_engine_passed"] == 1
    assert result.query_result.total_matches == 1
    assert result.query_result.matches[0].verified is True


def test_answer_pipeline_supplies_canonical_findings_to_final_traceability_gate():
    from core.research.models import ResearchFinding

    engine = ResearchEngine()
    source = ResearchSource(
        source_id="source-live-trace",
        title="Independent publisher article",
        source_type="web",
        locator="https://publisher.example/article",
        publisher="Publisher Example",
        reliability=0.9,
        accessed_at=now(),
    )
    finding = ResearchFinding(
        finding_id="finding-live-trace",
        document_id="document-live-trace",
        claim="Python is a programming language.",
        evidence_text="Python is a programming language.",
        confidence=0.95,
    )
    evidence = Evidence(
        evidence_id="evidence-live-trace",
        finding_id=finding.finding_id,
        source_id=source.source_id,
        evidence_text=finding.evidence_text,
        supports=True,
        strength=0.9,
        metadata={
            "knowledge_id": "knowledge-live-trace",
            "evidence_strength": {"strength_score": 0.9},
        },
    )
    knowledge = KnowledgeCandidate(
        knowledge_id="knowledge-live-trace",
        statement=finding.claim,
        findings=[finding.finding_id],
        evidence=[evidence.evidence_id],
        confidence=0.95,
        verified=True,
        created_at=now(),
        last_verified_at=now(),
        metadata={"verification_status": "VERIFIED"},
    )
    engine.register_source(source)
    engine.findings[finding.finding_id] = finding
    engine.evidence[evidence.evidence_id] = evidence
    engine.knowledge[knowledge.knowledge_id] = knowledge

    result = ResearchAnswerPipeline(
        query_engine=ResearchQueryEngine(engine),
    ).run(
        "Python programming language",
        verified_only=True,
        evidence_items=[evidence],
        sources=[source],
        focus_on_provided_evidence=True,
    )

    assert result.aggregation.answer_traceability.trace_complete is True
    assert result.aggregation.answer_traceability.traces[0].finding_ids == (
        finding.finding_id,
    )
    assert result.traceability.status == "TRACEABLE"
    # This fixture isolates the missing-findings regression; the source-quality
    # and arbitration checks may independently reject a one-source claim.
    assert result.answer.status != "TRACEABILITY_REJECTED"


def test_india_capital_query_excludes_unrelated_new_delhi_geography_claim():
    relevant = KnowledgeCandidate(
        knowledge_id="k-capital",
        statement="New Delhi is the capital of India.",
        findings=[], evidence=[], confidence=0.9, verified=True,
        created_at=now(), last_verified_at=now(), metadata={},
    )
    unrelated = KnowledgeCandidate(
        knowledge_id="k-geography",
        statement="New Delhi lies on the floodplains of the Yamuna River and is landlocked.",
        findings=[], evidence=[], confidence=0.9, verified=True,
        created_at=now(), last_verified_at=now(), metadata={},
    )
    filtered = ResearchAnswerPipeline._filter_query_relevant_knowledge(
        "What is the capital of India?", [unrelated, relevant]
    )
    assert [item.knowledge_id for item in filtered] == ["k-capital"]
    assert ResearchAnswerPipeline._india_capital_claim_is_relevant(
        "India's capital region; confused between Delhi, New Delhi and NCR"
    ) is False


def test_india_capital_query_can_filter_all_unrelated_claims_fail_closed():
    unrelated = KnowledgeCandidate(
        knowledge_id="k-geography",
        statement="New Delhi lies on the floodplains of the Yamuna River.",
        findings=[], evidence=[], confidence=0.9, verified=True,
        created_at=now(), last_verified_at=now(), metadata={},
    )
    assert ResearchAnswerPipeline._filter_query_relevant_knowledge(
        "What is the capital of India?", [unrelated]
    ) == []


def test_india_capital_claims_link_across_independent_publishers():
    first = KnowledgeCandidate(
        knowledge_id="k-capital-a",
        statement="in New Delhi [ a ] is a city and the capital city of India and a part of the National Capital Territory of Delhi (NCT).",
        findings=["f-a"], evidence=["e-a"], confidence=0.7, verified=False,
        created_at=now(), metadata={},
    )
    second = KnowledgeCandidate(
        knowledge_id="k-capital-b",
        statement="New Delhi is the capital of India .",
        findings=["f-b"], evidence=["e-b"], confidence=0.7, verified=False,
        created_at=now(), metadata={},
    )
    evidence = [
        Evidence(evidence_id="e-a", finding_id="f-a", source_id="source-a", evidence_text=first.statement, metadata={"knowledge_id": "k-capital-a"}),
        Evidence(evidence_id="e-b", finding_id="f-b", source_id="source-b", evidence_text=second.statement, metadata={"knowledge_id": "k-capital-b"}),
    ]
    sources = [
        ResearchSource(source_id="source-a", title="New Delhi - Wikipedia", source_type="web", locator="https://en.wikipedia.org/wiki/New_Delhi", reliability=0.8),
        ResearchSource(source_id="source-b", title="What is the Capital of India?", source_type="web", locator="https://www.mappr.co/capital-cities/india/", reliability=0.8),
    ]
    merged, remapped = ResearchAnswerPipeline._merge_verified_claim_paraphrases(
        [first, second], evidence, sources, query="What is the capital of India?"
    )
    assert len(merged) == 1
    assert set(merged[0].evidence) == {"e-a", "e-b"}
    assert {item.metadata["knowledge_id"] for item in remapped} == {merged[0].knowledge_id}


def _run_hindi_claim_link_pair(first_statement, second_statement):
    first = KnowledgeCandidate(
        knowledge_id="k-hindi-a",
        statement=first_statement,
        findings=["f-hindi-a"],
        evidence=["e-hindi-a"],
        confidence=0.7,
        verified=False,
        created_at=now(),
    )
    second = KnowledgeCandidate(
        knowledge_id="k-hindi-b",
        statement=second_statement,
        findings=["f-hindi-b"],
        evidence=["e-hindi-b"],
        confidence=0.7,
        verified=False,
        created_at=now(),
    )
    evidence = [
        Evidence(
            evidence_id="e-hindi-a",
            finding_id="f-hindi-a",
            source_id="source-hindi-a",
            evidence_text=first_statement,
            metadata={"knowledge_id": first.knowledge_id},
        ),
        Evidence(
            evidence_id="e-hindi-b",
            finding_id="f-hindi-b",
            source_id="source-hindi-b",
            evidence_text=second_statement,
            metadata={"knowledge_id": second.knowledge_id},
        ),
    ]
    sources = [
        ResearchSource(
            source_id="source-hindi-a",
            title="Publisher A Hindi report",
            source_type="web",
            locator="https://publisher-a.example/hindi-report",
            publisher="Publisher A",
            reliability=0.9,
        ),
        ResearchSource(
            source_id="source-hindi-b",
            title="Publisher B Hindi report",
            source_type="web",
            locator="https://publisher-b.example/hindi-report",
            publisher="Publisher B",
            reliability=0.9,
        ),
    ]
    diagnostics = {}
    merged, remapped = ResearchAnswerPipeline._merge_verified_claim_paraphrases(
        [first, second],
        evidence,
        sources,
        diagnostics=diagnostics,
        query="भारत की एआई सुरक्षा नीति की खबरें",
    )
    return merged, remapped, diagnostics


def test_devanagari_claim_paraphrases_link_across_independent_publishers():
    merged, remapped, diagnostics = _run_hindi_claim_link_pair(
        "भारत सरकार ने नई एआई सुरक्षा नीति जारी की।",
        "भारत सरकार ने नई एआई सुरक्षा नीति प्रकाशित की।",
    )

    assert diagnostics["linked_pairs"] == 1, diagnostics
    assert len(merged) == 1
    assert merged[0].verified is False
    assert set(merged[0].evidence) == {"e-hindi-a", "e-hindi-b"}
    assert {item.source_id for item in remapped} == {
        "source-hindi-a",
        "source-hindi-b",
    }
    assert {item.metadata["knowledge_id"] for item in remapped} == {
        merged[0].knowledge_id
    }


def test_devanagari_claim_linking_rejects_numeric_conflicts():
    merged, remapped, diagnostics = _run_hindi_claim_link_pair(
        "भारत सरकार 30 दिन में नई एआई सुरक्षा नीति जारी करेगी।",
        "भारत सरकार 60 दिन में नई एआई सुरक्षा नीति जारी करेगी।",
    )

    assert diagnostics["rejected_numeric_mismatch"] >= 1, diagnostics
    assert len(merged) == 2
    assert {item.metadata["knowledge_id"] for item in remapped} == {
        "k-hindi-a",
        "k-hindi-b",
    }


def test_devanagari_claim_linking_rejects_negation_conflicts():
    merged, remapped, diagnostics = _run_hindi_claim_link_pair(
        "भारत सरकार ने नई एआई सुरक्षा नीति जारी की।",
        "भारत सरकार ने नई एआई सुरक्षा नीति जारी नहीं की।",
    )

    assert diagnostics["rejected_negation_mismatch"] >= 1, diagnostics
    assert len(merged) == 2
    assert {item.metadata["knowledge_id"] for item in remapped} == {
        "k-hindi-a",
        "k-hindi-b",
    }
