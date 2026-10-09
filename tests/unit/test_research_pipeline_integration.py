from __future__ import annotations

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
from core.research.models import ResearchDocument
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

    with pytest.raises(RuntimeError, match="insufficient verified evidence"):
        integration.handle_answer(
            SimpleNamespace(step_id="answer-synthesis"),
            SimpleNamespace(job_id="job-no-evidence-answer", query="unrelated query"),
            SimpleNamespace(plan_id="test-plan"),
        )
