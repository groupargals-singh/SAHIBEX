from dataclasses import dataclass
import re
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
                    findings=list(getattr(match, "findings", ()) or ()),
                    evidence=list(getattr(match, "evidence", ()) or ()),
                    confidence=match.confidence,
                    verified=match.verified,
                    created_at=getattr(match, "created_at", None),
                    last_verified_at=getattr(match, "last_verified_at", None),
                    metadata=dict(getattr(match, "metadata", {}) or {}),
                )
            )

        return candidates

    def _evidence_knowledge(
        self,
        evidence_items: Iterable[Evidence],
    ) -> List[KnowledgeCandidate]:
        """Return knowledge explicitly linked to the supplied evidence."""
        ids = []
        seen = set()
        for evidence in evidence_items:
            knowledge_id = (evidence.metadata or {}).get("knowledge_id")
            if isinstance(knowledge_id, str) and knowledge_id and knowledge_id not in seen:
                seen.add(knowledge_id)
                ids.append(knowledge_id)

        candidates: List[KnowledgeCandidate] = []
        storage = getattr(self.query_engine, "storage", None)
        for knowledge_id in ids:
            knowledge = self.query_engine.engine.knowledge.get(knowledge_id)
            if knowledge is None and storage is not None:
                knowledge = storage.get_knowledge(knowledge_id)
            if knowledge is None:
                continue
            # Preserve the canonical relationship graph. Reconstructing a
            # candidate with only its statement/score silently dropped the
            # finding/evidence IDs, so freshness and source assessments could
            # not attach to the selected claim and valid live research was
            # mislabeled STALE. Copy the stored links; do not infer links from
            # text or promote an unverified knowledge record.
            candidates.append(
                KnowledgeCandidate(
                    knowledge_id=knowledge.knowledge_id,
                    statement=knowledge.statement,
                    findings=list(getattr(knowledge, "findings", ()) or ()),
                    evidence=list(getattr(knowledge, "evidence", ()) or ()),
                    confidence=knowledge.confidence,
                    verified=knowledge.verified,
                    created_at=getattr(knowledge, "created_at", None),
                    last_verified_at=getattr(knowledge, "last_verified_at", None),
                    metadata=dict(getattr(knowledge, "metadata", {}) or {}),
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

    @staticmethod
    def _is_ai_safety_security_query(query: str) -> bool:
        text = query.casefold()
        has_ai = (
            bool(re.search(r"\bai\b", text))
            or "artificial intelligence" in text
            or "कृत्रिम बुद्धिमत्ता" in text
        )
        has_safety = any(term in text for term in (
            "safety", "security", "cyber", "risk", "threat", "सुरक्षा", "खतरा",
        ))
        return has_ai and has_safety

    @staticmethod
    def _ai_safety_claim_is_relevant(statement: str) -> bool:
        text = statement.casefold()
        has_ai = (
            bool(re.search(r"\bai\b", text))
            or any(term in text for term in (
                "artificial intelligence", "llm", "openai", "anthropic",
                "chatgpt", "nvidia", "ai agent", "ai model", "ai system",
            ))
        )
        has_safety = any(term in text for term in (
            "safety", "security", "cyber", "risk", "threat", "attack",
            "attacker", "hack", "hacked", "breach", "vulnerab", "guardrail",
            "alignment", "misalignment", "privacy", "permission",
            "unauthorized", "unauthorised", "incident", "safe", "secure",
            "सुरक्षा", "खतरा",
        ))
        return has_ai and has_safety

    @classmethod
    def _filter_query_relevant_knowledge(
        cls,
        query: str,
        knowledge_items: List[KnowledgeCandidate],
    ) -> List[KnowledgeCandidate]:
        """Keep AI-safety answers from mixing in unrelated page/sidebar claims."""
        if not cls._is_ai_safety_security_query(query):
            return knowledge_items
        return [
            item for item in knowledge_items
            if cls._ai_safety_claim_is_relevant(item.statement)
        ]

    def run(
        self,
        query: str,
        *,
        verified_only: bool = True,
        limit: int = 10,
        evidence_items: Iterable[Evidence] = (),
        sources: Iterable[ResearchSource] = (),
        focus_on_provided_evidence: bool = False,
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

        if focus_on_provided_evidence and evidence_list:
            focused = self._evidence_knowledge(evidence_list)
            focused = self._filter_query_relevant_knowledge(query, focused)
            query_result = ResearchQueryResult(
                query=query,
                matches=focused,
                verified_only=verified_only,
                total_matches=len(focused),
            )
        else:
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
