from __future__ import annotations

from dataclasses import dataclass

from core.brain.mother_research_integration import (
    MotherResearchIntegration,
)


@dataclass(frozen=True)
class MotherLearningResult:
    success: bool
    topic: str
    status: str
    answer: str
    knowledge_count: int
    verified_knowledge_count: int
    research_job_id: str
    verification_status: str
    research_execution_id: str = ""
    learned_knowledge_ids: tuple[str, ...] = ()
    verified_knowledge_ids: tuple[str, ...] = ()
    error: str = ""

    @property
    def job_id(self) -> str:
        return self.research_job_id

    @property
    def execution_id(self) -> str:
        return self.research_execution_id


class MotherLearningIntegration:
    """
    Mother Brain learning bridge.

    Learning reuses the existing research system for:
    - evidence acquisition
    - extraction
    - knowledge creation
    - verification
    - persistence
    - answer synthesis

    This layer does not create a second knowledge or
    verification authority.
    """

    VERSION = "1.0"

    def __init__(
        self,
        *,
        research: MotherResearchIntegration | None = None,
        research_integration: MotherResearchIntegration | None = None,
    ) -> None:
        if research is not None and research_integration is not None:
            raise ValueError(
                "provide only one of research or research_integration"
            )

        selected_research = (
            research
            if research is not None
            else research_integration
        )

        self.research = (
            selected_research
            if selected_research is not None
            else MotherResearchIntegration()
        )

    def learn(
        self,
        *,
        topic: str,
        confirmation: bool = False,
    ) -> MotherLearningResult:
        if not isinstance(topic, str):
            raise TypeError("topic must be str")

        topic = topic.strip()

        if not topic:
            raise ValueError("topic must not be empty")

        result = self.research.research(
            query=topic,
            confirmation=confirmation,
        )

        if not result.success:
            return MotherLearningResult(
                success=False,
                topic=topic,
                status=result.status,
                answer=result.answer,
                knowledge_count=0,
                verified_knowledge_count=0,
                research_job_id=result.job_id,
                verification_status=result.verification_status,
                research_execution_id=getattr(result, "execution_id", ""),
                error=result.error,
            )

        knowledge_count = 0
        verified_knowledge_count = 0
        learned_knowledge_ids: tuple[str, ...] = ()
        verified_knowledge_ids: tuple[str, ...] = ()

        try:
            context = self.research.research_pipeline.context_for(
                result.job_id
            )

            answer_context = context.answer

            if answer_context is not None:
                knowledge_contexts = getattr(
                    answer_context,
                    "knowledge_verification_contexts",
                    {},
                )

                if isinstance(knowledge_contexts, dict):
                    learned_knowledge_ids = tuple(
                        str(knowledge_id)
                        for knowledge_id in knowledge_contexts
                    )

                answer_model = getattr(
                    answer_context,
                    "answer",
                    None,
                )
                answer_knowledge_ids = getattr(
                    answer_model,
                    "knowledge_ids",
                    (),
                )
                if answer_knowledge_ids:
                    learned_knowledge_ids = tuple(
                        dict.fromkeys(
                            str(knowledge_id)
                            for knowledge_id in answer_knowledge_ids
                        )
                    )

                answer_evidence = getattr(
                    answer_model,
                    "evidence",
                    (),
                )
                verified_knowledge_ids = tuple(
                    dict.fromkeys(
                        str(item.knowledge_id)
                        for item in answer_evidence
                        if bool(getattr(item, "verified", False))
                    )
                )
                knowledge_count = len(learned_knowledge_ids)
                verified_knowledge_count = len(
                    verified_knowledge_ids
                )

        except Exception:
            knowledge_count = 0
            verified_knowledge_count = 0
            learned_knowledge_ids = ()
            verified_knowledge_ids = ()

        return MotherLearningResult(
            success=True,
            topic=topic,
            status=result.status,
            answer=result.answer,
            knowledge_count=knowledge_count,
            verified_knowledge_count=verified_knowledge_count,
            research_job_id=result.job_id,
            verification_status=result.verification_status,
            research_execution_id=getattr(result, "execution_id", ""),
            learned_knowledge_ids=learned_knowledge_ids,
            verified_knowledge_ids=verified_knowledge_ids,
        )
