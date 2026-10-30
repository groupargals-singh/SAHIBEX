from __future__ import annotations

import hashlib
import time

import tempfile
from pathlib import Path

from core.research.acquisition import (
    AcquiredSource,
    AcquisitionRequest,
    AcquisitionResult,
    ResearchAcquisitionEngine,
    ResearchAcquisitionProvider,
)
from core.research.acquisition_pipeline import (
    ResearchAcquisitionPipeline,
)
from core.research.answer_pipeline import ResearchAnswerPipeline
from core.research.extraction_pipeline import (
    ResearchExtractionPipeline,
)
from core.research.extractor import (
    ExtractedFinding,
    ResearchExtractor,
)
from core.research.models import (
    Evidence,
    ResearchDocument,
    ResearchFinding,
    ResearchSource,
)
from core.research.pipeline import ResearchIngestionPipeline
from core.research.query import ResearchQueryEngine
from core.research.research_executor import ResearchExecutor
from core.research.research_pipeline_integration import (
    ResearchPipelineIntegration,
)
from core.research.research_plan import (
    ResearchPlan,
    ResearchStep,
)
from core.research.research_execution import (
    ResearchExecutionRequest,
)
from core.research.job import ResearchJob
from core.research.storage import ResearchStorage


class FakeProvider(ResearchAcquisitionProvider):
    provider_name = "direct_web"
    requires_network = False

    def acquire(
        self,
        request: AcquisitionRequest,
    ) -> AcquisitionResult:
        source = AcquiredSource(
            source_id="source-test-001",
            title="Test Research Source",
            source_type="web",
            locator="https://example.com/source-001",
            publisher="SAHIBEX Test",
            content=(
                "SAHIBEX integration testing confirms "
                "that the research pipeline can store "
                "and retrieve evidence."
            ),
        )

        return AcquisitionResult(
            query=request.query,
            sources=[source],
            completed=True,
            status="completed",
        )


class HighConfidenceTestExtractor(ResearchExtractor):
    """
    Test-only extractor.

    Production ResearchExtractor deliberately uses a conservative
    0.50 extraction confidence.

    This test extractor supplies strong deterministic evidence so
    that the existing ResearchEngine verification threshold can be
    exercised without weakening production verification rules.
    """

    def extract(
        self,
        document: ResearchDocument,
    ):
        return [
            ExtractedFinding(
                claim=(
                    "SAHIBEX integration testing confirms "
                    "that the research pipeline can store "
                    "and retrieve evidence."
                ),
                evidence_text=(
                    "SAHIBEX integration testing confirms "
                    "that the research pipeline can store "
                    "and retrieve evidence."
                ),
                confidence=0.95,
            ),
        ]


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "integration.db"

        storage = ResearchStorage(database_path)

        acquisition_engine = ResearchAcquisitionEngine(
            providers=[FakeProvider()]
        )

        acquisition_pipeline = ResearchAcquisitionPipeline(
            database_path,
            acquisition_engine,
        )

        ingestion_pipeline = (
            acquisition_pipeline.ingestion_pipeline
        )

        # IMPORTANT:
        # Use the same ResearchEngine owned by the ingestion
        # pipeline for extraction, knowledge creation,
        # verification, query, and answer synthesis.
        research_engine = ingestion_pipeline.engine

        # Test-only high-confidence extractor.
        # Production extractor and verification thresholds remain
        # unchanged.
        extraction_pipeline = ResearchExtractionPipeline(
            ingestion_pipeline,
            extractor=HighConfidenceTestExtractor(),
        )

        query_engine = ResearchQueryEngine(
            research_engine,
            storage,
        )

        answer_pipeline = ResearchAnswerPipeline(
            query_engine
        )

        integration = ResearchPipelineIntegration(
            acquisition_pipeline=acquisition_pipeline,
            extraction_pipeline=extraction_pipeline,
            answer_pipeline=answer_pipeline,
            storage=storage,
        )

        executor = ResearchExecutor()

        integration.register_handlers(executor)

        assert executor.has_step_handler(
            "research-scope"
        )

        assert executor.has_step_handler(
            "source-acquisition"
        )

        assert executor.has_step_handler(
            "evidence-extraction"
        )

        assert executor.has_step_handler(
            "verification"
        )

        assert executor.has_step_handler(
            "answer-synthesis"
        )

        job_id = "integration-job-001"

        job = ResearchJob(
            job_id=job_id,
            query="SAHIBEX integration testing",
        )

        job.plan()
        job.start()

        plan = ResearchPlan(
            plan_id="plan-integration-job-001",
            job_id=job_id,
            objective=job.query,
            steps=[
                ResearchStep(
                    step_id="research-scope",
                    description="Define research scope",
                ),
                ResearchStep(
                    step_id="source-acquisition",
                    description="Acquire source material",
                    source_types=["web"],
                ),
                ResearchStep(
                    step_id="evidence-extraction",
                    description="Extract evidence",
                ),
                ResearchStep(
                    step_id="verification",
                    description="Verify extracted evidence",
                ),
                ResearchStep(
                    step_id="answer-synthesis",
                    description="Synthesize answer",
                ),
            ],
        )

        request = ResearchExecutionRequest(
            execution_id="execution-integration-001",
            job_id=job_id,
            plan_id=plan.plan_id,
        )

        result = executor.execute(
            job,
            plan,
            request,
        )

        print("\n=== EXECUTION DIAGNOSTIC ===")
        print("status:", result.status)
        print(
            "completed_steps:",
            result.completed_steps,
        )
        print("failed_step:", result.failed_step)
        print("error:", result.error)
        print("output:", result.output)
        print("============================\n")

        assert result.status == "completed"
        assert result.failed_step is None
        assert result.error is None

        assert result.completed_steps == [
            "research-scope",
            "source-acquisition",
            "evidence-extraction",
            "verification",
            "answer-synthesis",
        ]

        context = integration.context_for(job_id)

        assert context.acquisition is not None
        assert context.ingestion is not None
        assert context.extraction
        assert context.verification is not None
        assert context.answer is not None

        assert (
            context.extraction[0].extracted_count >= 1
        )

        # -------------------------------------------------
        # 6F-10 KNOWLEDGE -> VERIFIED ANSWER ASSERTIONS
        # -------------------------------------------------

        answer_result = context.answer

        assert (
            answer_result.query_result.total_matches >= 1
        )

        assert (
            answer_result.aggregation.verified_count >= 1
        )

        assert (
            answer_result.aggregation.status
            == "VERIFIED"
        )

        # The quality-aware synthesizer flags this synthetic source as stale
        # (it has no publication date or independent source history). The
        # simpler answer adapter must preserve that conservative status.
        assert answer_result.answer.verified is False

        assert answer_result.answer.status == "STALE"

        assert answer_result.answer.confidence > 0.0

        assert answer_result.answer.knowledge_ids

        assert (
            answer_result.traceability.knowledge_count
            >= 1
        )

        assert (
            answer_result.traceability.evidence_count
            >= 1
        )

        assert (
            answer_result.traceability.source_count
            >= 1
        )

        assert (
            answer_result.traceability.status
            != "NO_KNOWLEDGE"
        )

        # -------------------------------------------------
        # STORAGE ASSERTIONS
        # -------------------------------------------------

        assert storage.document_count() >= 1
        assert storage.finding_count() >= 1
        assert storage.evidence_count() >= 1
        assert storage.knowledge_count() >= 1

        # -------------------------------------------------
        # ENGINE ASSERTIONS
        # -------------------------------------------------

        assert len(research_engine.knowledge) >= 1

        verified_knowledge = [
            item
            for item in research_engine.knowledge.values()
            if item.verified
        ]

        assert verified_knowledge

        print(
            "SAHIBEX RESEARCH PIPELINE "
            "KNOWLEDGE-TO-ANSWER TEST: PASS"
        )

        storage.close()


if __name__ == "__main__":
    main()


def test_verification_reports_insufficient_evidence_when_none_persisted():
    from types import SimpleNamespace

    from core.research.research_pipeline_integration import (
        ResearchPipelineContext,
        ResearchPipelineIntegration,
    )

    integration = ResearchPipelineIntegration.__new__(
        ResearchPipelineIntegration
    )
    integration._contexts = {
        "job-no-evidence": ResearchPipelineContext(
            query="test query",
            extraction=[
                SimpleNamespace(extracted_count=0, findings=[])
            ],
        )
    }

    result = integration.handle_verification(
        SimpleNamespace(step_id="verification"),
        SimpleNamespace(job_id="job-no-evidence"),
        SimpleNamespace(plan_id="test-plan"),
    )

    assert result["evidence_count"] == 0
    assert result["status"] == "insufficient_evidence"
    assert result["truth_status"] == "not_evaluated"


def test_answer_synthesis_is_blocked_without_verified_evidence():
    from types import SimpleNamespace
    import pytest

    from core.research.research_pipeline_integration import (
        ResearchPipelineContext,
        ResearchPipelineIntegration,
    )

    integration = ResearchPipelineIntegration.__new__(
        ResearchPipelineIntegration
    )
    integration._contexts = {
        "job-no-evidence-answer": ResearchPipelineContext(
            query="unrelated query",
            extraction=[SimpleNamespace(findings=[])],
            verification={
                "status": "insufficient_evidence",
                "evidence_count": 0,
            },
        )
    }

    with pytest.raises(RuntimeError, match="insufficient persisted evidence"):
        integration.handle_answer(
            SimpleNamespace(step_id="answer-synthesis"),
            SimpleNamespace(job_id="job-no-evidence-answer", query="unrelated query"),
            SimpleNamespace(plan_id="test-plan"),
        )


def test_answer_synthesis_is_blocked_when_evidence_has_no_retrievable_source():
    from types import SimpleNamespace
    import pytest

    from core.research.research_pipeline_integration import (
        ResearchPipelineContext,
        ResearchPipelineIntegration,
    )

    integration = ResearchPipelineIntegration.__new__(
        ResearchPipelineIntegration
    )
    integration._contexts = {
        "job-evidence-without-source": ResearchPipelineContext(
            query="source-grounded query",
            extraction=[
                SimpleNamespace(
                    findings=[
                        SimpleNamespace(
                            evidence_id="evidence-1",
                            source_id="missing-source-1",
                        )
                    ]
                )
            ],
            verification={"status": "evidence_available", "truth_status": "not_evaluated", "evidence_count": 1},
        )
    }
    integration.storage = SimpleNamespace(
        get_evidence=lambda evidence_id: SimpleNamespace(
            evidence_id=evidence_id,
            metadata={},
        ),
        get_source=lambda source_id: None,
    )

    with pytest.raises(RuntimeError, match="source traceability is unavailable"):
        integration.handle_answer(
            SimpleNamespace(step_id="answer-synthesis"),
            SimpleNamespace(job_id="job-evidence-without-source", query="source-grounded query"),
            SimpleNamespace(plan_id="test-plan"),
        )


def test_current_research_headline_followup_query_removes_publisher_suffix():
    query = ResearchPipelineIntegration._headline_corroboration_query(
        "OpenAI defends firing of 3 AI safety researchers | Technology News - The Indian Express"
    )
    assert query == "OpenAI defends firing 3 AI safety researchers latest"


def test_current_research_prioritizes_interleaved_headline_followups():
    ordered = ResearchPipelineIntegration._order_current_research_urls(
        discovered_urls=["https://broad.example/unrelated", "https://broad2.example/lead"],
        expansion_urls=["https://expanded.example/safety", "https://expanded2.example/security"],
        corroboration_urls=["https://publisher-a.example/same-story", "https://publisher-b.example/same-story"],
    )
    assert ordered == [
        "https://publisher-a.example/same-story",
        "https://publisher-b.example/same-story",
        "https://expanded.example/safety",
        "https://expanded2.example/security",
        "https://broad.example/unrelated",
        "https://broad2.example/lead",
    ]


def test_query_result_batches_are_interleaved_without_duplicate_urls():
    assert ResearchPipelineIntegration._interleave_url_batches([
        ["a1", "a2", "shared"],
        ["b1", "b2", "shared", "b4"],
    ]) == ["a1", "b1", "a2", "b2", "shared", "b4"]


def test_current_research_url_selection_prioritizes_distinct_publisher_hosts():
    urls = [
        "https://www.publisher-a.example/story",
        "https://publisher-a.example/another-story",
        "https://publisher-b.example/report",
        "https://publisher-c.example/news",
    ]
    selected = ResearchPipelineIntegration._prioritize_diverse_public_urls(urls, limit=3)
    assert selected == [
        "https://www.publisher-a.example/story",
        "https://publisher-b.example/report",
        "https://publisher-c.example/news",
    ]


def test_google_news_redirect_resolution_has_a_hard_deadline(monkeypatch):
    monkeypatch.setattr(
        "core.research.research_pipeline_integration._REDIRECT_RESOLUTION_DEADLINE_SECONDS",
        0.02,
    )

    def stalled_resolver(url, *, max_hops):
        time.sleep(0.2)
        return "https://publisher.example/story"

    started = time.monotonic()
    selected, resolved_sources = ResearchPipelineIntegration._resolve_and_prioritize_public_urls(
        ["https://news.google.com/rss/articles/slow"],
        source_by_url={},
        resolver=stalled_resolver,
        limit=5,
        max_candidates=5,
    )

    assert time.monotonic() - started < 0.15
    assert selected == []
    assert resolved_sources == {}


def test_discovery_expansion_for_hindi_ai_safety_query():
    assert ResearchPipelineIntegration._discovery_query_expansions(
        "आज AI सुरक्षा में क्या नया है?"
    ) == ["latest AI safety news", "latest AI security news"]


def test_discovery_expansion_skips_english_queries():
    assert ResearchPipelineIntegration._discovery_query_expansions(
        "latest AI safety news"
    ) == []


def test_discovery_expansion_for_hindi_capital_question():
    assert ResearchPipelineIntegration._discovery_query_expansions(
        "भारत की राजधानी क्या है?"
    ) == ["capital of India", "New Delhi capital of India"]


def test_discovery_expansion_does_not_guess_for_unmapped_hindi_queries():
    assert ResearchPipelineIntegration._discovery_query_expansions(
        "आज मौसम कैसा है?"
    ) == []


def test_verification_marks_evidence_available_without_claiming_truth_verified():
    from types import SimpleNamespace

    from core.research.research_pipeline_integration import (
        ResearchPipelineContext,
        ResearchPipelineIntegration,
    )

    integration = ResearchPipelineIntegration.__new__(ResearchPipelineIntegration)
    integration._contexts = {
        "job-evidence-available": ResearchPipelineContext(
            query="current research",
            extraction=[
                SimpleNamespace(
                    extracted_count=1,
                    findings=[SimpleNamespace(evidence_stored=True)],
                )
            ],
        )
    }

    result = integration.handle_verification(
        SimpleNamespace(step_id="verification"),
        SimpleNamespace(job_id="job-evidence-available"),
        SimpleNamespace(plan_id="test-plan"),
    )

    assert result["evidence_count"] == 1
    assert result["status"] == "evidence_available"
    assert result["truth_status"] == "not_evaluated"


def test_google_news_wrappers_are_resolved_before_publisher_diversity_selection():
    from types import SimpleNamespace

    wrappers = [
        "https://news.google.com/rss/articles/wrapper-a1",
        "https://news.google.com/rss/articles/wrapper-a2",
        "https://news.google.com/rss/articles/wrapper-b",
        "https://news.google.com/rss/articles/wrapper-c",
    ]
    resolved = {
        wrappers[0]: "https://publisher-a.example/story-one",
        wrappers[1]: "https://publisher-a.example/story-two",
        wrappers[2]: "https://publisher-b.example/story",
        wrappers[3]: "https://publisher-c.example/story",
    }
    source_by_url = {
        url: SimpleNamespace(locator=url, published_at=None)
        for url in wrappers
    }

    selected, resolved_sources = ResearchPipelineIntegration._resolve_and_prioritize_public_urls(
        wrappers,
        source_by_url=source_by_url,
        resolver=lambda url, max_hops: resolved[url],
        limit=3,
    )

    assert selected == [
        "https://publisher-a.example/story-one",
        "https://publisher-b.example/story",
        "https://publisher-c.example/story",
    ]
    assert set(resolved_sources) == set(resolved.values())


def test_headline_corroboration_source_selection_is_bounded_and_deduplicated():
    from types import SimpleNamespace

    sources = [
        SimpleNamespace(title=f"Anthropic AI safety incident report number {index}")
        for index in range(7)
    ]
    selected = ResearchPipelineIntegration._select_headline_corroboration_sources(
        sources,
        limit=5,
    )
    assert len(selected) == 5
    assert len({
        ResearchPipelineIntegration._headline_corroboration_query(source.title).casefold()
        for source in selected
    }) == 5


def test_ai_safety_followups_skip_unrelated_gpu_headlines():
    from types import SimpleNamespace

    sources = [
        SimpleNamespace(title="OpenAI fires three AI safety researchers after breach of trust"),
        SimpleNamespace(title="Anthropic AI misinformation incident report"),
        SimpleNamespace(title="Lava reveals exposed GPU servers and NVIDIA monitoring"),
    ]
    selected = ResearchPipelineIntegration._select_headline_corroboration_sources(
        sources, limit=5, query="आज AI सुरक्षा में क्या नया है?"
    )
    assert [item.title for item in selected] == [
        sources[0].title, sources[1].title
    ]


def test_unresolved_google_news_wrapper_is_not_promoted_to_publisher_url():
    wrapper = "https://news.google.com/rss/articles/unresolved-wrapper"
    selected, resolved_sources = ResearchPipelineIntegration._resolve_and_prioritize_public_urls(
        [wrapper],
        source_by_url={wrapper: object()},
        resolver=lambda url, max_hops: url,
        limit=10,
    )
    assert selected == []
    assert resolved_sources == {}


def test_ingestion_persists_unverified_outcome_without_evidence():
    with tempfile.TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "ingestion-history.db"
        pipeline = ResearchIngestionPipeline(database_path)

        source = ResearchSource(
            source_id="history-source-unverified",
            title="Verification lifecycle test source",
            source_type="web",
            locator="https://example.com/unverified",
            publisher="Lifecycle Test Publisher",
        )
        document = ResearchDocument(
            document_id="history-document-unverified",
            source_id=source.source_id,
            title="Lifecycle test",
            content="A document used to test verification history persistence.",
            content_hash=hashlib.sha256(
                b"A document used to test verification history persistence."
            ).hexdigest(),
        )
        pipeline.ingest(source, document)

        finding = ResearchFinding(
            finding_id="history-finding-unverified",
            document_id=document.document_id,
            claim="The lifecycle test claim has insufficient evidence.",
            confidence=0.9,
        )
        pipeline.add_finding(finding)

        result = pipeline.create_knowledge(
            statement=finding.claim,
            finding_ids=[finding.finding_id],
            confidence=0.9,
        )

        history = pipeline.storage.knowledge_verification_history(
            result.knowledge_id
        )

        assert result.verified is False
        assert len(history) == 1
        assert history[0]["status"] == "UNVERIFIED"
        assert history[0]["reason"].strip()
        assert history[0]["metadata"]["candidate_verified"] is False

        pipeline.close()


def test_ingestion_persists_conflicted_outcome():
    with tempfile.TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "ingestion-conflict.db"
        pipeline = ResearchIngestionPipeline(database_path)

        source = ResearchSource(
            source_id="history-source-conflict",
            title="Conflict lifecycle test source",
            source_type="web",
            locator="https://example.com/conflict",
            publisher="Conflict Test Publisher",
        )
        document = ResearchDocument(
            document_id="history-document-conflict",
            source_id=source.source_id,
            title="Conflict lifecycle test",
            content="A document used to test conflicting evidence persistence.",
            content_hash=hashlib.sha256(
                b"A document used to test conflicting evidence persistence."
            ).hexdigest(),
        )
        pipeline.ingest(source, document)

        finding = ResearchFinding(
            finding_id="history-finding-conflict",
            document_id=document.document_id,
            claim="The lifecycle conflict test claim.",
            confidence=0.9,
        )
        pipeline.add_finding(finding)

        evidence = Evidence(
            evidence_id="history-evidence-conflict",
            finding_id=finding.finding_id,
            source_id=source.source_id,
            evidence_text="This source contradicts the candidate claim.",
            supports=False,
            strength=0.95,
        )
        pipeline.add_evidence(evidence)

        result = pipeline.create_knowledge(
            statement=finding.claim,
            finding_ids=[finding.finding_id],
            evidence_ids=[evidence.evidence_id],
            confidence=0.9,
        )

        history = pipeline.storage.knowledge_verification_history(
            result.knowledge_id
        )

        assert result.verified is False
        assert len(history) == 1
        assert history[0]["status"] == "CONFLICTED"
        assert history[0]["reason"].strip()
        assert history[0]["metadata"]["candidate_verified"] is False

        pipeline.close()


def test_ingestion_persists_verified_outcome_from_independent_sources():
    with tempfile.TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "ingestion-verified.db"
        pipeline = ResearchIngestionPipeline(database_path)

        claim = (
            "Independent source verification confirms the sample research claim."
        )
        source_specs = [
            (
                "verified-source-alpha",
                "Alpha Research Publisher",
                "https://alpha.example.com/report",
                "verified-document-alpha",
                "Alpha report: " + claim,
                "verified-finding-alpha",
                "verified-evidence-alpha",
            ),
            (
                "verified-source-beta",
                "Beta Research Publisher",
                "https://beta.example.org/report",
                "verified-document-beta",
                "Beta report independently states: " + claim,
                "verified-finding-beta",
                "verified-evidence-beta",
            ),
        ]

        finding_ids = []
        evidence_ids = []

        for (
            source_id,
            publisher,
            locator,
            document_id,
            content,
            finding_id,
            evidence_id,
        ) in source_specs:
            source = ResearchSource(
                source_id=source_id,
                title=f"{publisher} report",
                source_type="web",
                locator=locator,
                publisher=publisher,
                reliability=0.95,
            )
            document = ResearchDocument(
                document_id=document_id,
                source_id=source_id,
                title=f"{publisher} verification report",
                content=content,
                content_hash=hashlib.sha256(
                    content.encode("utf-8")
                ).hexdigest(),
            )
            pipeline.ingest(source, document)

            finding = ResearchFinding(
                finding_id=finding_id,
                document_id=document_id,
                claim=claim,
                evidence_text=content,
                confidence=0.95,
            )
            pipeline.add_finding(finding)
            finding_ids.append(finding_id)

            evidence = Evidence(
                evidence_id=evidence_id,
                finding_id=finding_id,
                source_id=source_id,
                evidence_text=content,
                supports=True,
                strength=0.95,
            )
            pipeline.add_evidence(evidence)
            evidence_ids.append(evidence_id)

        result = pipeline.create_knowledge(
            statement=claim,
            finding_ids=finding_ids,
            evidence_ids=evidence_ids,
            confidence=0.95,
        )

        history = pipeline.storage.knowledge_verification_history(
            result.knowledge_id
        )
        candidate = pipeline.engine.knowledge[result.knowledge_id]

        assert result.verified is True
        assert candidate.metadata["verification_status"] == "VERIFIED"
        assert candidate.metadata["independent_source_count"] == 2
        assert candidate.metadata["supporting_source_count"] == 2

        assert len(history) == 1
        assert history[0]["status"] == "VERIFIED"
        assert history[0]["metadata"]["candidate_verified"] is True
        assert history[0]["metadata"]["independent_source_count"] == 2
        assert history[0]["metadata"]["supporting_source_count"] == 2

        stored = pipeline.storage.retrieve_knowledge(
            claim,
            verified_only=True,
        )
        assert result.knowledge_id in {
            item.knowledge_id for item in stored
        }

        query_engine = ResearchQueryEngine(
            pipeline.engine,
            pipeline.storage,
        )
        answer_pipeline = ResearchAnswerPipeline(query_engine)
        answer = answer_pipeline.run(
            claim,
            verified_only=True,
            limit=10,
        )
        assert answer.answer is not None
        assert result.knowledge_id in answer.answer.knowledge_ids

        pipeline.close()


def test_corroboration_batch_prefers_one_event_with_direct_publisher_diversity():
    weak_batch = [
        "https://www.msn.com/en-us/news/other/story-a",
        "https://www.msn.com/en-gb/news/other/story-b",
    ]
    strong_batch = [
        "https://publisher-one.example/story",
        "https://publisher-two.example/story",
        "https://publisher-three.example/story",
        "https://www.msn.com/en-us/news/other/story-c",
    ]

    selected = ResearchPipelineIntegration._select_best_corroboration_batch(
        [weak_batch, strong_batch]
    )
    prioritized = ResearchPipelineIntegration._prioritize_diverse_public_urls(
        [weak_batch[0], strong_batch[0], strong_batch[1], weak_batch[1]],
        limit=3,
    )

    assert selected == strong_batch
    assert prioritized == [strong_batch[0], strong_batch[1], weak_batch[0]]
