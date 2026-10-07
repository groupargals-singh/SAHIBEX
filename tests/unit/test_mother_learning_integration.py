from __future__ import annotations

from core.brain.mother_learning_integration import (
    MotherLearningIntegration,
)
from core.brain.mother_research_integration import (
    MotherResearchIntegration,
)
from core.research.acquisition import (
    AcquisitionRequest,
    AcquisitionResult,
    AcquiredSource,
    ResearchAcquisitionProvider,
)
from core.research.extractor import ExtractedFinding


class FakeResearchProvider(ResearchAcquisitionProvider):
    provider_name = "learning-test-provider"
    requires_network = False

    def acquire(
        self,
        request: AcquisitionRequest,
    ) -> AcquisitionResult:
        source = AcquiredSource(
            source_id="learning-source-1",
            title="SAHIBEX Learning Test",
            source_type="test",
            locator="memory://learning-test",
            publisher="SAHIBEX Test",
            content=(
                "SAHIBEX is a controlled personal AI architecture."
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
                    "SAHIBEX is a controlled personal AI "
                    "architecture."
                ),
                source_id=document.source_id,
                confidence=0.95,
                evidence_text=document.content,
            )
        ]


def main() -> None:
    research = MotherResearchIntegration()

    research.acquisition_pipeline.acquisition_engine.register_provider(
        FakeResearchProvider()
    )

    research.extraction_pipeline.extractor = (
        HighConfidenceTestExtractor()
    )

    learning = MotherLearningIntegration(
        research_integration=research,
    )

    result = learning.learn(
        topic="Learn about SAHIBEX architecture",
    )
    print("DEBUG success:", result.success)
    print("DEBUG status:", result.status)
    print("DEBUG answer:", result.answer)
    print("DEBUG job_id:", result.job_id)
    print("DEBUG execution_id:", result.execution_id)
    print("DEBUG verification:", result.verification_status)
    print("DEBUG error:", result.error)


    assert result.success is True
    assert result.status == "completed"
    assert result.answer
    assert result.job_id
    assert result.execution_id
    assert result.verification_status

    print("Learning success:", result.success)
    print("Learning status:", result.status)
    print(
        "Knowledge IDs:",
        result.learned_knowledge_ids,
    )
    print(
        "Verified IDs:",
        result.verified_knowledge_ids,
    )
    print(
        "Verification:",
        result.verification_status,
    )

    assert result.learned_knowledge_ids
    assert result.verified_knowledge_ids

    for knowledge_id in result.verified_knowledge_ids:
        knowledge = research.storage.get_knowledge(
            knowledge_id,
        )

        assert knowledge is not None
        assert knowledge.verified is True

    print(
        "SAHIBEX MOTHER LEARNING INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
