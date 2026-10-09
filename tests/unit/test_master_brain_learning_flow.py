from __future__ import annotations

from core.brain.master_brain import MasterBrain
from core.brain.mother_learning_integration import (
    MotherLearningIntegration,
)
from core.brain.mother_research_integration import (
    MotherResearchIntegration,
)
from core.research.acquisition import (
    AcquiredSource,
    AcquisitionRequest,
    AcquisitionResult,
    ResearchAcquisitionProvider,
)
from core.research.extractor import ExtractedFinding


class FakeLearningProvider(ResearchAcquisitionProvider):
    provider_name =  "direct_web"
    requires_network = False

    def acquire(
        self,
        request: AcquisitionRequest,
    ) -> AcquisitionResult:
        source = AcquiredSource(
            source_id="learning-source-1",
            title="SAHIBEX Learning Source",
            source_type="search",
            locator="memory://learning-source-1",
            content=(
                "SAHIBEX is a model-independent personal "
                "intelligence platform."
            ),
        )

        return AcquisitionResult(
            query=request.query,
            sources=[source],
            completed=True,
            status="completed",
        )


class LearningExtractor:
    def extract(self, document):
        return [
            ExtractedFinding(
                claim=(
                    "SAHIBEX is a model-independent "
                    "personal intelligence platform."
                ),
                evidence_text=(
                    "SAHIBEX is a model-independent "
                    "personal intelligence platform."
                ),
                confidence=0.95,
            )
        ]


def test_master_brain_learning_flow() -> None:
    research = MotherResearchIntegration()

    provider = FakeLearningProvider()

    research.acquisition_pipeline.acquisition_engine.register_provider(
        provider,
        replace=True,
    )

    research.extraction_pipeline.extractor = LearningExtractor()

    learning = MotherLearningIntegration(
        research=research,
    )

    brain = MasterBrain(
        mother_research=research,
        mother_learning=learning,
    )

    result = brain.process(
        "I want to learn about SAHIBEX architecture.",
        user_confirmation=True,
    )

    print("\n--- LEARNING RESULT DEBUG ---")
    print("success:", result.success)
    print("intent:", result.intent)
    print("action:", result.action)
    print("message:", result.message)
    print("error:", getattr(result, "error", "NO_ERROR_FIELD"))
    print("metadata:", result.metadata)
    print("--- END DEBUG ---\n")

    assert result.success is False
    assert result.intent == "learn"
    assert result.action == "respond"
    assert result.plan_created is True
    assert result.task_count == 3
    assert "couldn't verify" in result.message.casefold()
    dispatch_trace = result.metadata["internal_brain_dispatch"]
    assert dispatch_trace["reasoning"] == "DISPATCHED"
    assert dispatch_trace["orchestration"] == "DISPATCHED"
    assert dispatch_trace["learning"] == "DISPATCHED"

    learning_meta = result.metadata[
        "mother_learning_integration"
    ]

    assert learning_meta["success"] is False
    assert learning_meta["status"] == "insufficient_evidence"
    assert learning_meta["research_job_id"]
    assert learning_meta["verification_status"] == "NOT_VERIFIED"


if __name__ == "__main__":
    test_master_brain_learning_flow()
    print("SAHIBEX MASTER BRAIN LEARNING FLOW TEST: PASS")
