from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from core.research.conflict import ConflictPair
from core.research.models import Evidence, KnowledgeCandidate, ResearchSource


@dataclass(frozen=True)
class ConflictResolution:
    first_knowledge_id: str
    second_knowledge_id: str
    status: str
    selected_knowledge_id: str | None
    reason: str


@dataclass(frozen=True)
class ConflictResolutionResult:
    total_conflicts: int
    resolved_count: int
    unresolved_count: int
    resolutions: List[ConflictResolution]
    status: str


class EvidenceAwareConflictResolver:
    """
    Conservative evidence-aware conflict resolver.

    Resolution priority:

    1. Evidence support strength
    2. Source reliability
    3. Knowledge confidence

    If the evidence is insufficient or tied, the conflict remains
    UNRESOLVED.

    This module does not delete or mutate knowledge.
    """

    @staticmethod
    def _evidence_score(
        knowledge_id: str,
        evidence_items: Iterable[Evidence],
    ) -> float:
        score = 0.0

        for evidence in evidence_items:
            if evidence.metadata.get("knowledge_id") != knowledge_id:
                continue

            strength = float(evidence.strength)

            if strength < 0:
                strength = 0.0

            if strength > 1:
                strength = 1.0

            if evidence.supports:
                score += strength
            else:
                score -= strength

        return score

    @staticmethod
    def _source_score(
        knowledge_id: str,
        evidence_items: Iterable[Evidence],
        sources: Iterable[ResearchSource],
    ) -> float:
        source_map = {
            source.source_id: source
            for source in sources
        }

        score = 0.0

        for evidence in evidence_items:
            if evidence.metadata.get("knowledge_id") != knowledge_id:
                continue

            source = source_map.get(evidence.source_id)

            if source is None:
                continue

            reliability = float(source.reliability)

            if reliability < 0:
                reliability = 0.0

            if reliability > 1:
                reliability = 1.0

            if evidence.supports:
                score += reliability
            else:
                score -= reliability

        return score

    def resolve_pair(
        self,
        conflict: ConflictPair,
        knowledge_items: Iterable[KnowledgeCandidate],
        evidence_items: Iterable[Evidence],
        sources: Iterable[ResearchSource],
    ) -> ConflictResolution:
        knowledge_map = {
            knowledge.knowledge_id: knowledge
            for knowledge in knowledge_items
        }

        first = knowledge_map.get(conflict.first_knowledge_id)
        second = knowledge_map.get(conflict.second_knowledge_id)

        if first is None or second is None:
            return ConflictResolution(
                first_knowledge_id=conflict.first_knowledge_id,
                second_knowledge_id=conflict.second_knowledge_id,
                status="UNRESOLVED",
                selected_knowledge_id=None,
                reason="knowledge candidate missing",
            )

        evidence_list = list(evidence_items)
        source_list = list(sources)

        first_evidence = self._evidence_score(
            first.knowledge_id,
            evidence_list,
        )

        second_evidence = self._evidence_score(
            second.knowledge_id,
            evidence_list,
        )

        if first_evidence > second_evidence:
            return ConflictResolution(
                first_knowledge_id=first.knowledge_id,
                second_knowledge_id=second.knowledge_id,
                status="RESOLVED",
                selected_knowledge_id=first.knowledge_id,
                reason="stronger supporting evidence",
            )

        if second_evidence > first_evidence:
            return ConflictResolution(
                first_knowledge_id=first.knowledge_id,
                second_knowledge_id=second.knowledge_id,
                status="RESOLVED",
                selected_knowledge_id=second.knowledge_id,
                reason="stronger supporting evidence",
            )

        first_source = self._source_score(
            first.knowledge_id,
            evidence_list,
            source_list,
        )

        second_source = self._source_score(
            second.knowledge_id,
            evidence_list,
            source_list,
        )

        if first_source > second_source:
            return ConflictResolution(
                first_knowledge_id=first.knowledge_id,
                second_knowledge_id=second.knowledge_id,
                status="RESOLVED",
                selected_knowledge_id=first.knowledge_id,
                reason="higher source reliability",
            )

        if second_source > first_source:
            return ConflictResolution(
                first_knowledge_id=first.knowledge_id,
                second_knowledge_id=second.knowledge_id,
                status="RESOLVED",
                selected_knowledge_id=second.knowledge_id,
                reason="higher source reliability",
            )

        if first.confidence > second.confidence:
            return ConflictResolution(
                first_knowledge_id=first.knowledge_id,
                second_knowledge_id=second.knowledge_id,
                status="RESOLVED",
                selected_knowledge_id=first.knowledge_id,
                reason="higher knowledge confidence",
            )

        if second.confidence > first.confidence:
            return ConflictResolution(
                first_knowledge_id=first.knowledge_id,
                second_knowledge_id=second.knowledge_id,
                status="RESOLVED",
                selected_knowledge_id=second.knowledge_id,
                reason="higher knowledge confidence",
            )

        return ConflictResolution(
            first_knowledge_id=first.knowledge_id,
            second_knowledge_id=second.knowledge_id,
            status="UNRESOLVED",
            selected_knowledge_id=None,
            reason="evidence, source reliability, and confidence are tied",
        )

    def resolve(
        self,
        conflicts: Iterable[ConflictPair],
        knowledge_items: Iterable[KnowledgeCandidate],
        evidence_items: Iterable[Evidence],
        sources: Iterable[ResearchSource],
    ) -> ConflictResolutionResult:
        conflicts = list(conflicts)
        knowledge_items = list(knowledge_items)
        evidence_items = list(evidence_items)
        sources = list(sources)

        resolutions = [
            self.resolve_pair(
                conflict,
                knowledge_items,
                evidence_items,
                sources,
            )
            for conflict in conflicts
        ]

        resolved_count = sum(
            1
            for resolution in resolutions
            if resolution.status == "RESOLVED"
        )

        unresolved_count = (
            len(resolutions) - resolved_count
        )

        if not resolutions:
            status = "NO_CONFLICT"

        elif unresolved_count == 0:
            status = "ALL_RESOLVED"

        elif resolved_count > 0:
            status = "PARTIALLY_RESOLVED"

        else:
            status = "UNRESOLVED"

        return ConflictResolutionResult(
            total_conflicts=len(resolutions),
            resolved_count=resolved_count,
            unresolved_count=unresolved_count,
            resolutions=resolutions,
            status=status,
        )
