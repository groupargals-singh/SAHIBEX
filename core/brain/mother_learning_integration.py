from __future__ import annotations

from dataclasses import dataclass, replace

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

    def _finalize_learning_result(
        self,
        result: MotherLearningResult,
    ) -> MotherLearningResult:
        """Persist the outcome of a learning attempt when storage is available."""
        storage = getattr(self.research, "storage", None)
        if storage is None:
            # Lightweight test doubles may intentionally omit persistence.
            return result
        try:
            storage.record_learning_history(
                topic=result.topic,
                success=result.success,
                status=result.status,
                verification_status=result.verification_status,
                research_job_id=result.research_job_id,
                research_execution_id=result.research_execution_id,
                learned_knowledge_ids=result.learned_knowledge_ids,
                verified_knowledge_ids=result.verified_knowledge_ids,
                error=result.error,
                answer=result.answer,
            )
        except Exception as exc:
            return replace(
                result,
                success=False,
                status="learning_history_persistence_failed",
                verification_status="HISTORY_PERSISTENCE_FAILED",
                error=(
                    f"{result.error}; " if result.error else ""
                ) + f"learning history could not be persisted: {exc}",
            )
        return result

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

        try:
            result = self.research.research(
                query=topic,
                confirmation=confirmation,
            )
        except Exception as exc:
            return self._finalize_learning_result(
                MotherLearningResult(
                    success=False,
                    topic=topic,
                    status="research_execution_failed",
                    answer="Learning could not complete because research execution failed.",
                    knowledge_count=0,
                    verified_knowledge_count=0,
                    research_job_id="",
                    verification_status="FAILED",
                    research_execution_id="",
                    error=f"research execution failed: {exc}",
                )
            )

        if not result.success:
            return self._finalize_learning_result(
                MotherLearningResult(
                    success=False,
                    topic=topic,
                    status=result.status,
                    answer=result.answer,
                    knowledge_count=0,
                    verified_knowledge_count=0,
                    research_job_id=result.job_id,
                    verification_status=result.verification_status,
                    research_execution_id=getattr(
                        result,
                        "execution_id",
                        "",
                    ),
                    error=result.error,
                )
            )

        knowledge_count = 0
        verified_knowledge_count = 0
        learned_knowledge_ids: tuple[str, ...] = ()
        verified_knowledge_ids: tuple[str, ...] = ()
        arbitration_accepted = False

        try:
            context = self.research.research_pipeline.context_for(
                result.job_id
            )

            answer_context = context.answer

            arbitration = getattr(
                answer_context,
                "arbitration",
                None,
            )

            arbitration_accepted = (
                getattr(arbitration, "accepted", False) is True
            )

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
                        if str(knowledge_id).strip()
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
                            if str(knowledge_id).strip()
                        )
                    )

                answer_evidence = getattr(
                    answer_model,
                    "evidence",
                    (),
                )

                verified_ids = []

                if arbitration_accepted:
                    # Evidence must belong to a knowledge item actually
                    # returned by this answer and its persisted verification
                    # lifecycle must explicitly say VERIFIED. A bare
                    # evidence.verified flag is not sufficient provenance.
                    answer_knowledge_id_set = set(
                        learned_knowledge_ids
                    )
                    for item in answer_evidence or ():
                        if not bool(
                            getattr(item, "verified", False)
                        ):
                            continue

                        knowledge_id = getattr(
                            item,
                            "knowledge_id",
                            None,
                        )
                        if (
                            not isinstance(knowledge_id, str)
                            or not knowledge_id.strip()
                        ):
                            continue

                        knowledge_id = knowledge_id.strip()
                        if knowledge_id not in answer_knowledge_id_set:
                            continue

                        verification_context = (
                            knowledge_contexts.get(knowledge_id)
                            if isinstance(knowledge_contexts, dict)
                            else None
                        )
                        if not isinstance(verification_context, dict):
                            continue
                        if str(
                            verification_context.get(
                                "verification_status", ""
                            )
                        ).strip().upper() != "VERIFIED":
                            continue

                        verified_ids.append(knowledge_id)

                verified_knowledge_ids = tuple(
                    dict.fromkeys(verified_ids)
                )

                knowledge_count = len(learned_knowledge_ids)

                verified_knowledge_count = len(
                    verified_knowledge_ids
                )

        except Exception as exc:
            return self._finalize_learning_result(
                MotherLearningResult(
                    success=False,
                    topic=topic,
                    status="failed",
                    answer=result.answer,
                    knowledge_count=0,
                    verified_knowledge_count=0,
                    research_job_id=result.job_id,
                    verification_status="FAILED",
                    research_execution_id=getattr(
                        result,
                        "execution_id",
                        "",
                    ),
                    learned_knowledge_ids=(),
                    verified_knowledge_ids=(),
                    error=(
                        "learning knowledge extraction failed: "
                        f"{exc}"
                    ),
                )
            )

        verified_learning = bool(
            result.verification_status == "VERIFIED"
            and arbitration_accepted
            and verified_knowledge_count > 0
            and verified_knowledge_ids
        )

        return self._finalize_learning_result(
            MotherLearningResult(
                success=verified_learning,
                topic=topic,
                status=(
                    result.status
                    if verified_learning
                    else "insufficient_verified_knowledge"
                ),
                answer=(
                    result.answer
                    if verified_learning
                    else (
                        "Learning was not saved as trusted knowledge "
                        "because no verified knowledge items were "
                        "confirmed."
                    )
                ),
                knowledge_count=knowledge_count,
                verified_knowledge_count=verified_knowledge_count,
                research_job_id=result.job_id,
                verification_status=(
                    "VERIFIED"
                    if verified_learning
                    else "INSUFFICIENT_VERIFIED_KNOWLEDGE"
                ),
                research_execution_id=getattr(
                    result,
                    "execution_id",
                    "",
                ),
                learned_knowledge_ids=learned_knowledge_ids,
                verified_knowledge_ids=verified_knowledge_ids,
                error=(
                    ""
                    if verified_learning
                    else (
                        "no verified knowledge items available "
                        "to persist"
                    )
                ),
            )
        )
