from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile

from core.brain.master_brain import MasterBrain
from core.brain.mother_learning_integration import MotherLearningIntegration
from core.brain.mother_operational_integration import MotherOperationalIntegration
from core.brain.mother_research_integration import MotherResearchIntegration
from core.research.acquisition import (
    AcquisitionRequest,
    AcquisitionResult,
    AcquiredSource,
    ResearchAcquisitionEngine,
    ResearchAcquisitionProvider,
)
from core.research.acquisition_pipeline import ResearchAcquisitionPipeline
from core.research.answer_pipeline import ResearchAnswerPipeline
from core.research.extractor import ExtractedFinding
from core.research.extraction_pipeline import ResearchExtractionPipeline
from core.research.query import ResearchQueryEngine
from core.research.research_execution_manager import ResearchExecutionManager
from core.research.research_pipeline_integration import ResearchPipelineIntegration
from core.research.storage import ResearchStorage
from core.policies.constitution import ActionDecision


CLAIM = "Python is a high-level, general-purpose programming language."


class IndependentPublisherProvider(ResearchAcquisitionProvider):
    provider_name = "direct_web"
    requires_network = False

    def acquire(self, request: AcquisitionRequest) -> AcquisitionResult:
        published = datetime.now(timezone.utc)
        sources = [
            AcquiredSource(
                source_id="task37-python-org",
                title="Python overview",
                source_type="web",
                locator="https://www.python.org/about/",
                publisher="Python Software Foundation",
                published_at=published,
                content=CLAIM + " The Python Software Foundation maintains the official language website.",
                metadata={"test_fixture": True},
            ),
            AcquiredSource(
                source_id="task37-wikipedia",
                title="Python programming language overview",
                source_type="web",
                locator="https://en.wikipedia.org/wiki/Python_(programming_language)",
                publisher="Wikipedia contributors",
                published_at=published,
                content=CLAIM + " The encyclopedia article summarizes its history and language design.",
                metadata={"test_fixture": True},
            ),
        ]
        return AcquisitionResult(
            query=request.query,
            sources=sources,
            completed=True,
            status="completed",
            metadata={"test_fixture": True},
        )


class HighConfidenceAcceptanceExtractor:
    def extract(self, document):
        return [
            ExtractedFinding(
                claim=CLAIM,
                evidence_text=CLAIM,
                confidence=0.99,
            )
        ]


def _build_brain(database_path: Path) -> tuple[MasterBrain, ResearchStorage]:
    storage = ResearchStorage(database_path)
    acquisition_engine = ResearchAcquisitionEngine([IndependentPublisherProvider()])
    acquisition = ResearchAcquisitionPipeline(database_path, acquisition_engine)
    ingestion = acquisition.ingestion_pipeline
    extraction = ResearchExtractionPipeline(
        ingestion,
        extractor=HighConfidenceAcceptanceExtractor(),
    )
    query_engine = ResearchQueryEngine(ingestion.engine, storage)
    answer = ResearchAnswerPipeline(query_engine)
    pipeline = ResearchPipelineIntegration(
        acquisition_pipeline=acquisition,
        extraction_pipeline=extraction,
        answer_pipeline=answer,
        storage=storage,
    )
    research = MotherResearchIntegration(
        storage=storage,
        acquisition_pipeline=acquisition,
        extraction_pipeline=extraction,
        answer_pipeline=answer,
        research_pipeline=pipeline,
        execution_manager=ResearchExecutionManager(),
    )
    operational = MotherOperationalIntegration(storage=storage)
    brain = MasterBrain(
        mother_operational=operational,
        mother_research=research,
        mother_learning=MotherLearningIntegration(research=research),
    )
    return brain, storage


def test_full_main_brain_research_route_fails_closed_when_evidence_is_insufficient():
    with tempfile.TemporaryDirectory(prefix="sahibex_task37_test_") as directory:
        path = Path(directory) / "task37.db"
        brain, storage = _build_brain(path)
        try:
            result = brain.process("Search for Python programming language.")
            research_meta = result.metadata["mother_research_integration"]
            assert result.intent == "search"
            assert result.action == "research"
            assert result.permission_allowed is True
            assert result.plan_created is True
            assert result.metadata["internal_brain_dispatch"]["reasoning"] == "DISPATCHED"
            assert result.metadata["internal_brain_dispatch"]["orchestration"] == "DISPATCHED"
            assert result.metadata["internal_brain_dispatch"]["research"] == "DISPATCHED"
            # The fixture pages are intentionally not trusted as independent
            # corroboration once content/source identity checks are applied.
            # The Main Brain must not surface a claim when the final answer
            # gate rejects it.
            assert result.success is False
            assert research_meta["success"] is False
            assert research_meta["status"] == "insufficient_evidence"
            assert research_meta["verification_status"] == "NOT_VERIFIED"
            assert CLAIM not in result.message
            assert len(storage.list_knowledge(verified_only=True)) == 0
            assert brain.knowledge_brain.storage is storage
            assert brain.memory_brain.storage is storage
            assert brain.mother_operational.memory_knowledge.storage is storage
        finally:
            storage.close()


def test_main_brain_successfully_surfaces_only_verified_research_result(monkeypatch):
    from types import SimpleNamespace
    from core.research.models import ResearchFinding
    from core.brain.mother_research_integration import MotherResearchResult

    with tempfile.TemporaryDirectory(prefix="sahibex_task37_verified_") as directory:
        brain, storage = _build_brain(Path(directory) / "task37-verified.db")
        try:
            verified = MotherResearchResult(
                success=True,
                query="Search for a verified routing test.",
                status="completed",
                answer="The answer is supported by independent, verified evidence.",
                job_id="task37-verified-job",
                execution_id="task37-verified-execution",
                verification_status="VERIFIED",
            )
            monkeypatch.setattr(
                brain.research_learning_brain,
                "research_topic",
                lambda query, confirmation=False: SimpleNamespace(
                    success=True,
                    operation="research",
                    verified=True,
                    persisted=True,
                    result=verified,
                    error="",
                ),
            )
            result = brain.process("Search for a verified routing test.")
            assert result.success is True
            assert result.intent == "search"
            assert result.action == "research"
            assert result.verification_status == "VERIFIED"
            assert result.message == verified.answer
            assert result.metadata["mother_research_integration"]["success"] is True
            assert isinstance(result.metadata["mother_research_integration"]["diagnostics"], dict)
            assert result.metadata["mother_research_integration"]["prompt_injection_status"] == "SAFE"
            assert result.metadata["internal_brain_dispatch"]["research"] == "DISPATCHED"
        finally:
            storage.close()


def test_main_brain_protected_action_remains_blocked_end_to_end():
    with tempfile.TemporaryDirectory(prefix="sahibex_task37_security_") as directory:
        brain, storage = _build_brain(Path(directory) / "task37-security.db")
        try:
            result = brain.process("Delete the project files.")
            assert result.success is False
            assert result.permission_allowed is False
            assert result.confirmation_required is True
            assert result.authority_decision == ActionDecision.REQUIRE_CONFIRMATION.value
            assert result.plan_created is False
            assert brain.constitution.can_sahibex_modify_constitution() is False
        finally:
            storage.close()
