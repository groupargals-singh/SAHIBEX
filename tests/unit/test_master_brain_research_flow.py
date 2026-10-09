from __future__ import annotations

from pathlib import Path
import tempfile
from types import SimpleNamespace

from core.brain.master_brain import MasterBrain
from core.brain.mother_research_integration import (
    MotherResearchIntegration,
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

        result = brain.process(
            "Search for SAHIBEX research integration."
        )

        assert result.success is True
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

        assert metadata["success"] is True

        assert metadata["status"] == (
            "completed"
        )

        # The fixture's quality-aware answer is not independently supported;
        # stored-knowledge verification alone must not upgrade it.
        assert metadata[
            "verification_status"
        ] == "NOT_VERIFIED"

        assert result.message

        print(
            "[PASS] Master Brain research flow"
        )


def main():
    test_conflict_metadata_no_conflict()
    test_conflict_metadata_resolved()
    test_conflict_metadata_unresolved()
    test_unresolved_conflict_is_not_verified_fact()
    test_master_brain_research_flow()

    print(
        "SAHIBEX MASTER BRAIN RESEARCH "
        "CONFLICT TEST: PASS"
    )


if __name__ == "__main__":
    main()
