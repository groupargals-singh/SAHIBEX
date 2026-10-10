from core.brain.mother_learning_integration import (
    MotherLearningIntegration,
    MotherLearningResult,
)
from core.brain.mother_research_integration import (
    MotherResearchIntegration,
    MotherResearchResult,
)
from core.brain.research_learning_brain import ResearchLearningBrain
from core.brain.master_brain import MasterBrain


def test_research_learning_brain_capability_boundary() -> None:
    brain = MasterBrain()
    facade = brain.research_learning_brain

    assert isinstance(facade, ResearchLearningBrain)
    contract = facade.capability_contract()

    assert contract["research"] is True
    assert contract["learning"] is True
    assert contract["evidence_pipeline"] is True
    assert contract["knowledge_persistence"] is True
    assert contract["permission_authority"] is False
    assert contract["execution_authority"] is False
    assert contract["constitution_mutation"] is False


def test_research_learning_brain_delegates_research_without_bypassing_confirmation() -> None:
    research = MotherResearchIntegration()
    captured: dict[str, object] = {}

    def fake_research(*, query: str, confirmation: bool = False):
        captured["query"] = query
        captured["confirmation"] = confirmation
        return MotherResearchResult(
            success=True,
            query=query,
            status="completed",
            answer="verified research",
            job_id="job-1",
            execution_id="execution-1",
            verification_status="VERIFIED",
        )

    research.research = fake_research  # type: ignore[method-assign]
    facade = ResearchLearningBrain(research=research)

    result = facade.research_topic("test research", confirmation=True)

    assert result.success is True
    assert result.verified is True
    assert captured == {
        "query": "test research",
        "confirmation": True,
    }


def test_research_learning_brain_delegates_learning() -> None:
    research = MotherResearchIntegration()
    learning = MotherLearningIntegration(research=research)

    def fake_learning(*, topic: str, confirmation: bool = False):
        return MotherLearningResult(
            success=True,
            topic=topic,
            status="completed",
            answer="learned",
            knowledge_count=2,
            verified_knowledge_count=2,
            research_job_id="job-2",
            research_execution_id="execution-2",
            verification_status="VERIFIED",
            learned_knowledge_ids=("k-1", "k-2"),
            verified_knowledge_ids=("k-1", "k-2"),
        )

    learning.learn = fake_learning  # type: ignore[method-assign]
    facade = ResearchLearningBrain(
        research=research,
        learning=learning,
    )

    result = facade.learn_topic("test learning", confirmation=True)

    assert result.success is True
    assert result.verified is True
    assert result.result.verified_knowledge_count == 2


def test_research_learning_brain_does_not_mark_unverified_research_persisted() -> None:
    research = MotherResearchIntegration()
    research.research = lambda *, query, confirmation=False: MotherResearchResult(
        success=True, query=query, status="completed", answer="unverified",
        job_id="job-unverified", execution_id="exec-unverified",
        verification_status="PENDING",
    )  # type: ignore[method-assign]
    result = ResearchLearningBrain(research=research).research_topic("latest claims")
    assert result.success is False
    assert result.verified is False
    assert result.persisted is False


def test_research_learning_brain_does_not_mark_zero_verified_learning_persisted() -> None:
    research = MotherResearchIntegration()
    learning = MotherLearningIntegration(research=research)
    learning.learn = lambda *, topic, confirmation=False: MotherLearningResult(
        success=True, topic=topic, status="completed", answer="unverified",
        knowledge_count=0, verified_knowledge_count=0,
        research_job_id="job-empty", research_execution_id="exec-empty",
        verification_status="VERIFIED", learned_knowledge_ids=(),
        verified_knowledge_ids=(),
    )  # type: ignore[method-assign]
    result = ResearchLearningBrain(research=research, learning=learning).learn_topic("topic")
    assert result.success is False
    assert result.verified is False
    assert result.persisted is False
