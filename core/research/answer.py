from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from core.research.aggregator import (
    AggregatedKnowledge,
    ResearchAggregationResult,
)
from core.research.models import Evidence, ResearchSource


@dataclass(frozen=True)
class AnswerEvidence:
    knowledge_id: str
    statement: str
    confidence: float
    verified: bool
    evidence_texts: List[str] = field(default_factory=list)
    source_ids: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResearchAnswer:
    query: str
    answer: str
    confidence: float
    verified: bool
    status: str
    evidence: List[AnswerEvidence] = field(default_factory=list)
    knowledge_ids: List[str] = field(default_factory=list)


class ResearchAnswerSynthesizer:
    """
    Deterministic research answer synthesis.

    Rules:
    - Never invent knowledge.
    - Only supplied aggregated knowledge may enter the answer.
    - Verified knowledge is preferred.
    - Evidence is attached when available.
    - Conflicting/unresolved claims are not reintroduced.
    - Empty research results produce a safe no-result answer.
    """

    def synthesize(
        self,
        query: str,
        aggregation: ResearchAggregationResult,
        *,
        evidence_items: Iterable[Evidence] = (),
    ) -> ResearchAnswer:
        if not isinstance(query, str):
            raise TypeError("query must be a string")

        if not query.strip():
            raise ValueError("query cannot be empty")

        evidence_items = list(evidence_items)

        evidence_by_knowledge: dict[str, list[Evidence]] = {}

        for evidence in evidence_items:
            knowledge_id = self._resolve_knowledge_id(
                evidence,
                aggregation,
            )

            if knowledge_id is None:
                continue

            evidence_by_knowledge.setdefault(
                knowledge_id,
                [],
            ).append(evidence)

        selected = list(aggregation.results)

        if not selected:
            return ResearchAnswer(
                query=query,
                answer=(
                    "No sufficiently supported knowledge was "
                    "available for this research query."
                ),
                confidence=0.0,
                verified=False,
                status="NO_RESULT",
                evidence=[],
                knowledge_ids=[],
            )

        answer_lines: list[str] = []

        answer_evidence: list[AnswerEvidence] = []

        for knowledge in selected:
            answer_lines.append(
                self._format_statement(knowledge)
            )

            matching_evidence = evidence_by_knowledge.get(
                knowledge.knowledge_id,
                [],
            )

            evidence_texts = [
                evidence.evidence_text
                for evidence in matching_evidence
                if evidence.evidence_text.strip()
            ]

            source_ids = list(
                dict.fromkeys(
                    evidence.source_id
                    for evidence in matching_evidence
                )
            )

            answer_evidence.append(
                AnswerEvidence(
                    knowledge_id=knowledge.knowledge_id,
                    statement=knowledge.statement,
                    confidence=knowledge.confidence,
                    verified=knowledge.verified,
                    evidence_texts=evidence_texts,
                    source_ids=source_ids,
                )
            )

        confidence = self._calculate_confidence(selected)

        verified = all(
            knowledge.verified
            for knowledge in selected
        )

        status = self._determine_status(
            aggregation,
            selected,
        )

        return ResearchAnswer(
            query=query,
            answer="\n".join(answer_lines),
            confidence=confidence,
            verified=verified,
            status=status,
            evidence=answer_evidence,
            knowledge_ids=[
                knowledge.knowledge_id
                for knowledge in selected
            ],
        )

    @staticmethod
    def _format_statement(
        knowledge: AggregatedKnowledge,
    ) -> str:
        return knowledge.statement.strip()

    @staticmethod
    def _calculate_confidence(
        knowledge_items: list[AggregatedKnowledge],
    ) -> float:
        if not knowledge_items:
            return 0.0

        total = sum(
            knowledge.confidence
            for knowledge in knowledge_items
        )

        return total / len(knowledge_items)

    @staticmethod
    def _determine_status(
        aggregation: ResearchAggregationResult,
        selected: list[AggregatedKnowledge],
    ) -> str:
        if not selected:
            return "NO_RESULT"

        if aggregation.unresolved_conflict_count > 0:
            if aggregation.resolved_conflict_count > 0:
                return "PARTIALLY_RESOLVED"

            return "CONFLICT_UNRESOLVED"

        if aggregation.resolved_conflict_count > 0:
            return "CONFLICT_RESOLVED"

        if all(
            knowledge.verified
            for knowledge in selected
        ):
            return "VERIFIED"

        return "UNVERIFIED"

    @staticmethod
    def _resolve_knowledge_id(
        evidence: Evidence,
        aggregation: ResearchAggregationResult,
    ) -> Optional[str]:
        """
        Resolve evidence to a knowledge candidate.

        Evidence currently points to a finding, not directly to
        knowledge. Therefore metadata may explicitly provide the
        knowledge ID. Without that mapping, the evidence is not
        attached automatically.
        """
        metadata = getattr(evidence, "metadata", {})

        knowledge_id = metadata.get("knowledge_id")

        if not knowledge_id:
            return None

        valid_ids = {
            knowledge.knowledge_id
            for knowledge in aggregation.results
        }

        if knowledge_id not in valid_ids:
            return None

        return knowledge_id
