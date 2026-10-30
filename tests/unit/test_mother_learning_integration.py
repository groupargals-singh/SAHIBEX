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
from types import SimpleNamespace


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

def _build_learning_for_arbitration_test(
    *,
    arbitration_present: bool,
    arbitration_accepted: bool = False,
):
    evidence = SimpleNamespace(
        knowledge_id="knowledge-test-1",
        verified=True,
    )

    answer_model = SimpleNamespace(
        knowledge_ids=("knowledge-test-1",),
        evidence=(evidence,),
    )

    answer_fields = {
        "answer": answer_model,
        "knowledge_verification_contexts": {
            "knowledge-test-1": {
                "knowledge_id": "knowledge-test-1",
                "verification_status": "VERIFIED",
            },
        },
    }

    if arbitration_present:
        answer_fields["arbitration"] = SimpleNamespace(
            accepted=arbitration_accepted,
        )

    answer_context = SimpleNamespace(**answer_fields)

    research_context = SimpleNamespace(
        answer=answer_context,
    )

    class FakeResearch:
        def __init__(self):
            self.research_pipeline = SimpleNamespace(
                context_for=lambda job_id: research_context,
            )

        def research(self, *, query, confirmation=False):
            return SimpleNamespace(
                success=True,
                topic=query,
                status="completed",
                answer="Test research answer",
                job_id="learning-job-test",
                execution_id="learning-execution-test",
                verification_status="VERIFIED",
                error="",
            )

    return MotherLearningIntegration(
        research=FakeResearch(),
    )


def test_learning_rejects_verified_evidence_when_arbitration_rejects():
    learning = _build_learning_for_arbitration_test(
        arbitration_present=True,
        arbitration_accepted=False,
    )

    result = learning.learn(topic="Test arbitration rejection")

    assert result.success is False
    assert result.verified_knowledge_count == 0
    assert result.verified_knowledge_ids == ()
    assert result.verification_status == (
        "INSUFFICIENT_VERIFIED_KNOWLEDGE"
    )


def test_learning_fails_closed_when_arbitration_is_missing():
    learning = _build_learning_for_arbitration_test(
        arbitration_present=False,
    )

    result = learning.learn(topic="Test missing arbitration")

    assert result.success is False
    assert result.verified_knowledge_count == 0
    assert result.verified_knowledge_ids == ()
    assert result.verification_status == (
        "INSUFFICIENT_VERIFIED_KNOWLEDGE"
    )


def test_learning_accepts_verified_evidence_when_arbitration_accepts():
    learning = _build_learning_for_arbitration_test(
        arbitration_present=True,
        arbitration_accepted=True,
    )

    result = learning.learn(topic="Test accepted arbitration")

    assert result.success is True
    assert result.verified_knowledge_count == 1
    assert result.verified_knowledge_ids == (
        "knowledge-test-1",
    )
    assert result.verification_status == "VERIFIED"


def test_learning_rejects_evidence_for_knowledge_not_in_answer():
    learning = _build_learning_for_arbitration_test(
        arbitration_present=True,
        arbitration_accepted=True,
    )
    original_research = learning.research
    context = original_research.research_pipeline.context_for("learning-job-test")
    context.answer.answer.evidence = (
        SimpleNamespace(knowledge_id="unrelated-knowledge", verified=True),
    )

    result = learning.learn(topic="Reject unrelated evidence")

    assert result.success is False
    assert result.verified_knowledge_count == 0
    assert result.verified_knowledge_ids == ()


def test_learning_rejects_evidence_without_persisted_verified_status():
    learning = _build_learning_for_arbitration_test(
        arbitration_present=True,
        arbitration_accepted=True,
    )
    context = learning.research.research_pipeline.context_for("learning-job-test")
    context.answer.knowledge_verification_contexts["knowledge-test-1"][
        "verification_status"
    ] = "UNVERIFIED"

    result = learning.learn(topic="Reject unverified lifecycle")

    assert result.success is False
    assert result.verified_knowledge_count == 0
    assert result.verified_knowledge_ids == ()
