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
    # The research plan routes generic learning queries through the
    # direct_web source type. This deterministic test provider replaces
    # that provider without enabling real network access.
    provider_name = "direct_web"
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
                confidence=0.95,
                evidence_text=document.content,
            )
        ]


def main() -> None:
    research = MotherResearchIntegration()

    # Explicit replacement keeps provider override intentional and test-local.
    research.acquisition_pipeline.acquisition_engine.register_provider(
        FakeResearchProvider(),
        replace=True,
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


    # A completed research pipeline is not a verified learning result.
    # This one-source fixture must fail closed rather than promote claims.
    assert result.success is False
    assert result.status == "insufficient_evidence"
    assert "couldn't verify" in result.answer.casefold()
    assert result.job_id
    assert result.execution_id
    assert result.verification_status == "NOT_VERIFIED"
    assert result.learned_knowledge_ids == ()
    assert result.verified_knowledge_ids == ()

    print("Learning success:", result.success)
    print("Learning status:", result.status)
    print("Verification:", result.verification_status)
    print("SAHIBEX MOTHER LEARNING INTEGRITY TEST: PASS")


if __name__ == "__main__":
    main()
