from __future__ import annotations

from pathlib import Path
import tempfile
from types import SimpleNamespace

import pytest

from core.brain.master_brain import MasterBrain
from core.brain.mother_operational_integration import (
    MotherOperationalIntegration,
)
from core.brain.mother_research_integration import (
    MotherResearchIntegration,
    MotherResearchResult,
)
from core.research.acquisition import (
    AcquisitionResult,
    AcquiredSource,
    ResearchAcquisitionEngine,
    ResearchAcquisitionProvider,
)
from core.research.acquisition_pipeline import (
    ResearchAcquisitionPipeline,
)
from core.research.answer_pipeline import (
    ResearchAnswerPipeline,
)
from core.research.extraction_pipeline import (
    ResearchExtractionPipeline,
)
from core.research.query import (
    ResearchQueryEngine,
)
from core.research.research_pipeline_integration import (
    ResearchPipelineIntegration,
)
from core.research.research_execution_manager import (
    ResearchExecutionManager,
)
from core.research.storage import ResearchStorage
from core.research.extractor import ExtractedFinding


class FakeResearchProvider(
    ResearchAcquisitionProvider
):
    provider_name = "direct_web"
    requires_network = False

    def acquire(self, request):
        source = AcquiredSource(
            source_id="master-research-test-source-001",
            title=(
                "SAHIBEX Research Integration Test Source"
            ),
            source_type="web",
            locator=(
                "https://example.com/sahibex-test"
            ),
            publisher="SAHIBEX Test",
            content=(
                "SAHIBEX research integration test confirms "
                "that the Mother Brain research pipeline can "
                "acquire, store, extract, verify and answer."
            ),
        )

        return AcquisitionResult(
            query=request.query,
            sources=[source],
            completed=True,
            status="completed",
        )


class HighConfidenceTestExtractor:
    def extract(self, document):
        return [
            ExtractedFinding(
                claim=(
                    "SAHIBEX research integration test confirms "
                    "that the Mother Brain research pipeline "
                    "can acquire, store, extract, verify "
                    "and answer."
                ),
                evidence_text=(
                    "SAHIBEX research integration test confirms "
                    "that the Mother Brain research pipeline "
                    "can acquire, store, extract, verify "
                    "and answer."
                ),
                confidence=0.95,
            )
        ]


def build_research_integration(
    database_path: Path,
):
    storage = ResearchStorage(database_path)

    acquisition_engine = ResearchAcquisitionEngine(
        providers=[
            FakeResearchProvider()
        ]
    )

    acquisition_pipeline = (
        ResearchAcquisitionPipeline(
            database_path,
            acquisition_engine,
        )
    )

    ingestion_pipeline = (
        acquisition_pipeline.ingestion_pipeline
    )

    extraction_pipeline = (
        ResearchExtractionPipeline(
            ingestion_pipeline,
            extractor=HighConfidenceTestExtractor(),
        )
    )

    query_engine = ResearchQueryEngine(
        ingestion_pipeline.engine,
        storage,
    )

    answer_pipeline = ResearchAnswerPipeline(
        query_engine
    )

    research_pipeline = (
        ResearchPipelineIntegration(
            acquisition_pipeline=acquisition_pipeline,
            extraction_pipeline=extraction_pipeline,
            answer_pipeline=answer_pipeline,
            storage=storage,
        )
    )

    execution_manager = (
        ResearchExecutionManager()
    )

    return MotherResearchIntegration(
        storage=storage,
        acquisition_pipeline=acquisition_pipeline,
        extraction_pipeline=extraction_pipeline,
        answer_pipeline=answer_pipeline,
        research_pipeline=research_pipeline,
        execution_manager=execution_manager,
    )


def test_conflict_metadata_no_conflict():
    answer = SimpleNamespace(
        aggregation=SimpleNamespace(
            conflict_count=0,
            resolved_conflict_count=0,
            unresolved_conflict_count=0,
            conflict_ids=[],
            resolved_knowledge_ids=[],
        )
    )

    metadata = (
        MotherResearchIntegration._conflict_metadata(
            answer
        )
    )

    assert metadata["conflict_status"] == (
        "NO_CONFLICT"
    )
    assert metadata["conflict_count"] == 0
    assert metadata[
        "resolved_conflict_count"
    ] == 0
    assert metadata[
        "unresolved_conflict_count"
    ] == 0
    assert metadata["conflict_ids"] == ()
    assert metadata[
        "resolved_knowledge_ids"
    ] == ()

    print(
        "[PASS] no conflict metadata"
    )


def test_conflict_metadata_resolved():
    answer = SimpleNamespace(
        aggregation=SimpleNamespace(
            conflict_count=1,
            resolved_conflict_count=1,
            unresolved_conflict_count=0,
            conflict_ids=[
                "conflict-001"
            ],
            resolved_knowledge_ids=[
                "knowledge-001"
            ],
        )
    )

    metadata = (
        MotherResearchIntegration._conflict_metadata(
            answer
        )
    )

    assert metadata["conflict_status"] == (
        "CONFLICT_RESOLVED"
    )
    assert metadata["conflict_count"] == 1
    assert metadata[
        "resolved_conflict_count"
    ] == 1
    assert metadata[
        "unresolved_conflict_count"
    ] == 0
    assert metadata["conflict_ids"] == (
        "conflict-001",
    )
    assert metadata[
        "resolved_knowledge_ids"
    ] == (
        "knowledge-001",
    )

    print(
        "[PASS] resolved conflict metadata"
    )


def test_conflict_metadata_unresolved():
    answer = SimpleNamespace(
        aggregation=SimpleNamespace(
            conflict_count=1,
            resolved_conflict_count=0,
            unresolved_conflict_count=1,
            conflict_ids=[
                "conflict-unresolved-001"
            ],
            resolved_knowledge_ids=[],
        )
    )

    metadata = (
        MotherResearchIntegration._conflict_metadata(
            answer
        )
    )

    assert metadata["conflict_status"] == (
        "UNRESOLVED_CONFLICT"
    )
    assert metadata["conflict_count"] == 1
    assert metadata[
        "resolved_conflict_count"
    ] == 0
    assert metadata[
        "unresolved_conflict_count"
    ] == 1
    assert metadata["conflict_ids"] == (
        "conflict-unresolved-001",
    )
    assert metadata[
        "resolved_knowledge_ids"
    ] == ()

    print(
        "[PASS] unresolved conflict metadata"
    )


def test_unresolved_conflict_is_not_verified_fact():
    answer = SimpleNamespace(
        aggregation=SimpleNamespace(
            conflict_count=1,
            resolved_conflict_count=0,
            unresolved_conflict_count=1,
            conflict_ids=[
                "conflict-unresolved-002"
            ],
            resolved_knowledge_ids=[],
        )
    )

    metadata = (
        MotherResearchIntegration._conflict_metadata(
            answer
        )
    )

    assert metadata[
        "unresolved_conflict_count"
    ] > 0

    assert metadata[
        "conflict_status"
    ] == "UNRESOLVED_CONFLICT"

    assert not (
        metadata["conflict_status"]
        == "CONFLICT_RESOLVED"
    )

    assert metadata[
        "resolved_knowledge_ids"
    ] == ()

    print(
        "[PASS] unresolved conflict cannot "
        "be treated as resolved"
    )


def test_master_brain_research_flow():
    with tempfile.TemporaryDirectory() as temp_dir:
        database_path = (
            Path(temp_dir)
            / "master_brain_research.db"
        )

        mother_research = (
            build_research_integration(
                database_path
            )
        )

        brain = MasterBrain(
            mother_research=mother_research
        )

        # Injecting a custom research store must not split the Main Brain's
        # read/write path: research, operational retrieval, Memory Brain and
        # Knowledge Brain must all observe the same persistent database.
        assert brain.mother_research.storage is mother_research.storage
        assert brain.mother_operational.storage is mother_research.storage
        assert brain.mother_operational.memory_knowledge.storage is (
            mother_research.storage
        )
        assert brain.memory_brain.storage is mother_research.storage
        assert brain.knowledge_brain.storage is mother_research.storage

        result = brain.process(
            "Search for SAHIBEX research integration."
        )

        assert result.success is False
        assert result.intent == "search"
        assert result.action == "research"
        assert result.plan_created is True
        assert result.task_count == 3
        dispatch_trace = result.metadata["internal_brain_dispatch"]
        assert dispatch_trace["reasoning"] == "DISPATCHED"
        assert dispatch_trace["orchestration"] == "DISPATCHED"
        assert dispatch_trace["research"] == "DISPATCHED"

        metadata = result.metadata[
            "mother_research_integration"
        ]

        assert metadata["success"] is False
        assert metadata["status"] == "insufficient_evidence"

        # An unverified answer must not be surfaced as a successful research
        # result; the user receives a controlled evidence-insufficiency message.
        assert metadata["verification_status"] == "NOT_VERIFIED"
        assert "couldn't verify" in result.message.casefold()

        print(
            "[PASS] Master Brain research flow"
        )


def test_master_brain_preserves_research_verification_status(monkeypatch) -> None:
    research = MotherResearchIntegration()
    brain = MasterBrain(mother_research=research)
    verified_result = MotherResearchResult(
        success=True,
        query="Search for a verified routing test.",
        status="completed",
        answer="Verified research answer.",
        job_id="verified-job-1",
        execution_id="verified-execution-1",
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
            result=verified_result,
            error="",
        ),
    )

    result = brain.process("Search for a verified routing test.")

    assert result.success is True
    assert result.intent == "search"
    assert result.message == "Verified research answer."
    assert result.verification_status == "VERIFIED"
    assert (
        result.metadata["mother_research_integration"]["verification_status"]
        == "VERIFIED"
    )


def test_master_brain_preserves_learning_verification_status(monkeypatch) -> None:
    from core.brain.mother_learning_integration import MotherLearningResult

    research = MotherResearchIntegration()
    brain = MasterBrain(mother_research=research)
    verified_result = MotherLearningResult(
        success=True,
        topic="verified routing test",
        status="completed",
        answer="Verified learning answer.",
        knowledge_count=1,
        verified_knowledge_count=1,
        research_job_id="learning-job-1",
        verification_status="VERIFIED",
        research_execution_id="learning-execution-1",
        verified_knowledge_ids=("knowledge-verified-1",),
    )
    monkeypatch.setattr(
        brain.research_learning_brain,
        "learn_topic",
        lambda topic, confirmation=False: SimpleNamespace(
            success=True,
            operation="learn",
            verified=True,
            persisted=True,
            result=verified_result,
            error="",
        ),
    )

    result = brain.process(
        "I want to learn about a verified routing test.",
        user_confirmation=True,
    )

    assert result.success is True
    assert result.intent == "learn"
    assert result.message == "Verified learning answer."
    assert result.verification_status == "VERIFIED"
    assert (
        result.metadata["mother_learning_integration"]["verification_status"]
        == "VERIFIED"
    )


def test_master_brain_rejects_unverified_research_even_if_inner_success(monkeypatch) -> None:
    research = MotherResearchIntegration()
    brain = MasterBrain(mother_research=research)
    unverified_result = MotherResearchResult(
        success=True,
        query="Search for unverified routing test.",
        status="completed",
        answer="UNVERIFIED CLAIM MUST NOT BE SHOWN",
        job_id="unverified-job-1",
        execution_id="unverified-execution-1",
        verification_status="NOT_VERIFIED",
    )
    monkeypatch.setattr(
        brain.research_learning_brain,
        "research_topic",
        lambda query, confirmation=False: SimpleNamespace(
            success=False,
            operation="research",
            verified=False,
            persisted=False,
            result=unverified_result,
            error="",
        ),
    )

    result = brain.process("Search for unverified routing test.")

    assert result.success is False
    assert result.verification_status == "NOT_VERIFIED"
    assert "UNVERIFIED CLAIM MUST NOT BE SHOWN" not in result.message
    assert "couldn't verify" in result.message.casefold()
    assert result.metadata["mother_research_integration"]["success"] is False


def test_master_brain_rejects_unverified_learning_even_if_inner_success(monkeypatch) -> None:
    from core.brain.mother_learning_integration import MotherLearningResult

    research = MotherResearchIntegration()
    brain = MasterBrain(mother_research=research)
    unverified_result = MotherLearningResult(
        success=True,
        topic="unverified routing test",
        status="completed",
        answer="UNVERIFIED LEARNING CLAIM MUST NOT BE SHOWN",
        knowledge_count=1,
        verified_knowledge_count=0,
        research_job_id="unverified-learning-job-1",
        verification_status="NOT_VERIFIED",
        research_execution_id="unverified-learning-execution-1",
    )
    monkeypatch.setattr(
        brain.research_learning_brain,
        "learn_topic",
        lambda topic, confirmation=False: SimpleNamespace(
            success=False,
            operation="learn",
            verified=False,
            persisted=False,
            result=unverified_result,
            error="",
        ),
    )

    result = brain.process(
        "I want to learn about unverified routing test.",
        user_confirmation=True,
    )

    assert result.success is False
    assert result.verification_status == "NOT_VERIFIED"
    assert "UNVERIFIED LEARNING CLAIM MUST NOT BE SHOWN" not in result.message
    assert "couldn't verify" in result.message.casefold()
    assert result.metadata["mother_learning_integration"]["success"] is False


def test_master_brain_rejects_split_explicit_storage() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        research = build_research_integration(root / "research.db")
        operational = MotherOperationalIntegration(
            storage=ResearchStorage(root / "operational.db")
        )

        with pytest.raises(
            ValueError,
            match="share one persistent database",
        ):
            MasterBrain(
                mother_research=research,
                mother_operational=operational,
            )


def test_master_brain_rejects_learning_from_other_research_instance() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        research = build_research_integration(root / "research.db")
        other_research = build_research_integration(root / "other-research.db")
        from core.brain.mother_learning_integration import (
            MotherLearningIntegration,
        )

        learning = MotherLearningIntegration(research=other_research)
        with pytest.raises(
            ValueError,
            match="same mother_research integration instance",
        ):
            MasterBrain(
                mother_research=research,
                mother_learning=learning,
            )


def main():
    test_conflict_metadata_no_conflict()
    test_conflict_metadata_resolved()
    test_conflict_metadata_unresolved()
    test_unresolved_conflict_is_not_verified_fact()
    test_master_brain_research_flow()
    test_master_brain_rejects_split_explicit_storage()
    test_master_brain_rejects_learning_from_other_research_instance()

    print(
        "SAHIBEX MASTER BRAIN RESEARCH "
        "CONFLICT TEST: PASS"
    )


if __name__ == "__main__":
    main()
