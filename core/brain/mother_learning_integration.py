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
    error: str = ""


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
    ) -> None:
        self.research = (
            research
            if research is not None
            else MotherResearchIntegration()
        )

    def learn(
        self,
        *,
        topic: str,
    ) -> MotherLearningResult:
        if not isinstance(topic, str):
            raise TypeError("topic must be str")

        topic = topic.strip()

        if not topic:
            raise ValueError("topic must not be empty")

        result = self.research.research(
            query=topic,
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
                error=result.error,
            )

        knowledge_count = 0
        verified_knowledge_count = 0

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
                    knowledge_count = len(knowledge_contexts)

                    verified_knowledge_count = sum(
                        1
                        for item in knowledge_contexts.values()
                        if isinstance(item, dict)
                        and bool(item.get("verified", False))
                    )

        except Exception:
            knowledge_count = 0
            verified_knowledge_count = 0

        return MotherLearningResult(
            success=True,
            topic=topic,
            status=result.status,
            answer=result.answer,
            knowledge_count=knowledge_count,
            verified_knowledge_count=verified_knowledge_count,
            research_job_id=result.job_id,
            verification_status=result.verification_status,
        )
