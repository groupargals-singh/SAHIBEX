from dataclasses import dataclass
from typing import Iterable, List, Optional

from core.research.aggregator import (
    ResearchAggregationResult,
    ResearchResultAggregator,
)
from core.research.answer import (
    ResearchAnswer,
    ResearchAnswerSynthesizer,
)
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)
from core.research.query import (
    ResearchQueryEngine,
    ResearchQueryResult,
)
from core.research.traceability import (
    ResearchTraceabilityEngine,
    ResearchTraceabilityResult,
)


@dataclass(frozen=True)
class ResearchAnswerPipelineResult:
    query_result: ResearchQueryResult
    aggregation: ResearchAggregationResult
    answer: ResearchAnswer
    traceability: ResearchTraceabilityResult
    knowledge_verification_contexts: dict[str, dict]


class ResearchAnswerPipeline:
    """
    Complete auditable research-answer pipeline.

    Flow:

        Query
          -> Retrieval
          -> Aggregation
          -> Conflict Detection / Resolution
          -> Answer Synthesis
          -> Evidence / Source Traceability
          -> Knowledge Verification / Conflict Context

    Knowledge verification context is observational only.

    It does not:
    - mutate knowledge
    - change aggregation selection
    - replace conflict resolution
    - replace answer synthesis
    - replace traceability
    """

    def __init__(
        self,
        query_engine: ResearchQueryEngine,
        aggregator: Optional[ResearchResultAggregator] = None,
        synthesizer: Optional[ResearchAnswerSynthesizer] = None,
        traceability_engine: Optional[
            ResearchTraceabilityEngine
        ] = None,
    ) -> None:
        if query_engine is None:
            raise ValueError("query_engine is required")

        self.query_engine = query_engine

        self.aggregator = (
            aggregator
            or ResearchResultAggregator()
        )

        self.synthesizer = (
            synthesizer
            or ResearchAnswerSynthesizer()
        )

        self.traceability_engine = (
            traceability_engine
            or ResearchTraceabilityEngine()
        )

    @staticmethod
    def _extract_knowledge(
        query_result: ResearchQueryResult,
    ) -> List[KnowledgeCandidate]:
        """
        Convert query matches into KnowledgeCandidate objects.
        """
        candidates: List[KnowledgeCandidate] = []

        for match in query_result.matches:
            candidates.append(
                KnowledgeCandidate(
                    knowledge_id=match.knowledge_id,
                    statement=match.statement,
                    findings=[],
                    evidence=[],
                    confidence=match.confidence,
                    verified=match.verified,
                    created_at=None,
                    last_verified_at=None,
                    metadata={},
                )
            )

        return candidates

    @staticmethod
    def _selected_knowledge(
        knowledge_items: Iterable[KnowledgeCandidate],
        aggregation: ResearchAggregationResult,
    ) -> List[KnowledgeCandidate]:
        """
        Keep only knowledge candidates selected by the aggregator.
        """
        selected_ids = {
            item.knowledge_id
            for item in aggregation.results
        }

        return [
            item
            for item in knowledge_items
            if item.knowledge_id in selected_ids
        ]

    @staticmethod
    def _knowledge_verification_contexts(
        knowledge_items: Iterable[KnowledgeCandidate],
        storage,
    ) -> dict[str, dict]:
        """
        Build observational knowledge verification contexts.

        Combines:
        - verification lifecycle
        - conflict verification context

        This layer is observational only.
        It does not mutate knowledge or change answer selection.
        """
        if storage is None:
            return {}

        contexts: dict[str, dict] = {}

        for knowledge in knowledge_items:
            knowledge_id = knowledge.knowledge_id

            lifecycle = (
                storage.knowledge_verification_lifecycle(
                    knowledge_id
                )
            )

            conflict_context = (
                storage.knowledge_verification_context(
                    knowledge_id
                )
            )

            context: dict = {}

            if isinstance(lifecycle, dict):
                context.update(lifecycle)

            if isinstance(conflict_context, dict):
                context.update(conflict_context)

            contexts[knowledge_id] = context

        return contexts

    def run(
        self,
        query: str,
        *,
        verified_only: bool = True,
        limit: int = 10,
        evidence_items: Iterable[Evidence] = (),
        sources: Iterable[ResearchSource] = (),
    ) -> ResearchAnswerPipelineResult:
        """
        Execute the complete auditable research pipeline.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError(
                "query must be a non-empty string"
            )

        if not isinstance(limit, int) or isinstance(limit, bool):
            raise ValueError(
                "limit must be an integer"
            )

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero"
            )

        evidence_list = list(evidence_items)
        source_list = list(sources)

        # ---------------------------------------------------------
        # STEP 1: Query / Retrieval
        # ---------------------------------------------------------

        query_result = self.query_engine.search(
            query,
            verified_only=verified_only,
            limit=limit,
        )

        # ---------------------------------------------------------
        # STEP 2: Convert retrieval matches to knowledge objects
        # ---------------------------------------------------------

        knowledge_candidates = self._extract_knowledge(
            query_result
        )

        # ---------------------------------------------------------
        # STEP 3: Aggregation
        # ---------------------------------------------------------

        aggregation = self.aggregator.aggregate(
            knowledge_candidates,
            verified_only=verified_only,
            limit=limit,
            evidence_items=evidence_list,
            sources=source_list,
        )

        # ---------------------------------------------------------
        # STEP 4: Answer synthesis
        # ---------------------------------------------------------

        answer = self.synthesizer.synthesize(
            query,
            aggregation,
            evidence_items=evidence_list,
        )

        # ---------------------------------------------------------
        # STEP 5: Answer traceability
        # ---------------------------------------------------------

        selected_knowledge = self._selected_knowledge(
            knowledge_candidates,
            aggregation,
        )

        traceability = self.traceability_engine.trace(
            selected_knowledge,
            evidence_list,
            source_list,
        )

        # ---------------------------------------------------------
        # STEP 6: Knowledge verification / conflict context
        # ---------------------------------------------------------

        storage = getattr(
            self.query_engine,
            "storage",
            None,
        )

        knowledge_verification_contexts = (
            self._knowledge_verification_contexts(
                knowledge_candidates,
                storage,
            )
        )

        # ---------------------------------------------------------
        # FINAL RESULT
        # ---------------------------------------------------------

        return ResearchAnswerPipelineResult(
            query_result=query_result,
            aggregation=aggregation,
            answer=answer,
            traceability=traceability,
            knowledge_verification_contexts=(
                knowledge_verification_contexts
            ),
        )
