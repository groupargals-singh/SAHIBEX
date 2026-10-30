from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List

from core.research.conflict import (
    ConflictPair,
    ResearchConflictDetector,
)
from core.research.conflict_resolver import (
    ConflictResolution,
    EvidenceAwareConflictResolver,
)
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)


CONFLICT_INTELLIGENCE_VERSION = "6G-5"


CONFLICT_TYPE_EXPLICIT_NEGATION = "EXPLICIT_NEGATION"
CONFLICT_TYPE_LEXICAL_CONTRADICTION = "LEXICAL_CONTRADICTION"
CONFLICT_TYPE_NUMERIC_CONTRADICTION = "NUMERIC_CONTRADICTION"
CONFLICT_TYPE_UNKNOWN = "UNKNOWN"


RESOLUTION_RESOLVED = "RESOLVED"
RESOLUTION_UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class ConflictIntelligenceAssessment:
    """
    Structured 6G-5 conflict intelligence assessment.

    This layer does not decide truth.

    It records:
        - what type of conflict was detected
        - whether the existing resolver resolved it
        - which knowledge candidate was selected, if any
        - the resolver's explicit reason
        - the score margins used by the resolver

    This object is observational and does not mutate
    knowledge, evidence, or sources.
    """

    first_knowledge_id: str
    second_knowledge_id: str

    conflict_type: str
    conflict_reason: str

    resolution_status: str
    selected_knowledge_id: str | None

    evidence_score_delta: float
    source_reliability_delta: float
    knowledge_confidence_delta: float

    resolution_reason: str

    version: str = CONFLICT_INTELLIGENCE_VERSION
    temporal_comparison_status: str = "UNKNOWN"
    publication_time_delta_seconds: float | None = None

    def __post_init__(self) -> None:
        valid_types = {
            CONFLICT_TYPE_EXPLICIT_NEGATION,
            CONFLICT_TYPE_LEXICAL_CONTRADICTION,
            CONFLICT_TYPE_NUMERIC_CONTRADICTION,
            CONFLICT_TYPE_UNKNOWN,
        }

        if self.conflict_type not in valid_types:
            raise ValueError(
                f"invalid conflict_type: {self.conflict_type}"
            )

        valid_statuses = {
            RESOLUTION_RESOLVED,
            RESOLUTION_UNRESOLVED,
        }

        if self.resolution_status not in valid_statuses:
            raise ValueError(
                f"invalid resolution_status: "
                f"{self.resolution_status}"
            )

        if not isinstance(self.first_knowledge_id, str):
            raise TypeError(
                "first_knowledge_id must be a string"
            )

        if not isinstance(self.second_knowledge_id, str):
            raise TypeError(
                "second_knowledge_id must be a string"
            )

        if self.resolution_status == RESOLUTION_UNRESOLVED:
            if self.selected_knowledge_id is not None:
                raise ValueError(
                    "unresolved conflict cannot have "
                    "selected_knowledge_id"
                )

        if self.resolution_status == RESOLUTION_RESOLVED:
            if not self.selected_knowledge_id:
                raise ValueError(
                    "resolved conflict must have "
                    "selected_knowledge_id"
                )


@dataclass(frozen=True)
class ConflictIntelligenceResult:
    """
    Structured result for a collection of conflicts.
    """

    total_conflicts: int
    resolved_count: int
    unresolved_count: int

    assessments: List[ConflictIntelligenceAssessment]

    status: str
    version: str = CONFLICT_INTELLIGENCE_VERSION

    def __post_init__(self) -> None:
        if self.total_conflicts < 0:
            raise ValueError(
                "total_conflicts cannot be negative"
            )

        if self.resolved_count < 0:
            raise ValueError(
                "resolved_count cannot be negative"
            )

        if self.unresolved_count < 0:
            raise ValueError(
                "unresolved_count cannot be negative"
            )

        if (
            self.resolved_count
            + self.unresolved_count
            != self.total_conflicts
        ):
            raise ValueError(
                "resolution counts must equal "
                "total_conflicts"
            )


class ResearchConflictIntelligence:
    """
    6G-5 conflict intelligence layer.

    Architecture:

        ConflictDetector
              |
              v
        ConflictPair
              |
              v
        Existing EvidenceAwareConflictResolver
              |
              v
        Structured ConflictIntelligenceAssessment

    Important rules:

    1. Do not invent semantic conflicts.
    2. Do not override the existing detector.
    3. Do not override the existing resolver.
    4. Do not mutate knowledge.
    5. Do not mutate evidence.
    6. Do not mutate sources.
    7. Preserve unresolved conflicts.
    8. Preserve the resolver's explicit reason.
    """

    def __init__(
        self,
        *,
        detector: ResearchConflictDetector | None = None,
        resolver: EvidenceAwareConflictResolver | None = None,
    ) -> None:
        self.detector = (
            detector
            if detector is not None
            else ResearchConflictDetector()
        )

        self.resolver = (
            resolver
            if resolver is not None
            else EvidenceAwareConflictResolver()
        )

    @staticmethod
    def _classify_conflict(
        conflict: ConflictPair,
    ) -> str:
        """
        Convert the existing detector reason into a
        stable conflict category.
        """

        reason = conflict.reason.lower().strip()

        if "explicit negation" in reason:
            return CONFLICT_TYPE_EXPLICIT_NEGATION

        if "contradictory lexical term" in reason:
            return CONFLICT_TYPE_LEXICAL_CONTRADICTION

        if "contradictory numeric value" in reason:
            return CONFLICT_TYPE_NUMERIC_CONTRADICTION

        return CONFLICT_TYPE_UNKNOWN

    @staticmethod
    def _evidence_score(
        knowledge_id: str,
        evidence_items: Iterable[Evidence],
    ) -> float:
        """
        Mirror the existing resolver's evidence scoring
        so that the score margin is observable.

        This method does not change resolver behavior.
        """

        score = 0.0

        for evidence in evidence_items:
            metadata = evidence.metadata or {}

            if metadata.get("knowledge_id") != knowledge_id:
                continue

            try:
                strength = float(evidence.strength)
            except (TypeError, ValueError):
                strength = 0.0

            strength = max(
                0.0,
                min(1.0, strength),
            )

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
        """
        Mirror the existing resolver's source-reliability
        scoring so that the reliability margin is observable.

        This method does not change resolver behavior.
        """

        source_map = {
            source.source_id: source
            for source in sources
        }

        score = 0.0

        for evidence in evidence_items:
            metadata = evidence.metadata or {}

            if metadata.get("knowledge_id") != knowledge_id:
                continue

            source = source_map.get(
                evidence.source_id
            )

            if source is None:
                continue

            try:
                reliability = float(
                    source.reliability
                )
            except (TypeError, ValueError):
                reliability = 0.0

            reliability = max(
                0.0,
                min(1.0, reliability),
            )

            if evidence.supports:
                score += reliability
            else:
                score -= reliability

        return score

    @staticmethod
    def _confidence_score(
        knowledge_id: str,
        knowledge_items: Iterable[KnowledgeCandidate],
    ) -> float:
        """
        Return the knowledge confidence for a candidate.
        """

        for knowledge in knowledge_items:
            if knowledge.knowledge_id != knowledge_id:
                continue

            try:
                confidence = float(
                    knowledge.confidence
                )
            except (TypeError, ValueError):
                confidence = 0.0

            return max(
                0.0,
                min(1.0, confidence),
            )

        return 0.0

    @staticmethod
    def _latest_publication_time(
        knowledge_id: str,
        evidence_items: Iterable[Evidence],
        sources: Iterable[ResearchSource],
    ) -> datetime | None:
        """Return the newest valid publication timestamp linked to a claim.

        Only evidence explicitly linked through metadata["knowledge_id"] is
        considered. Missing, naive, or timezone-without-offset timestamps are
        ignored rather than guessed.
        """
        source_map = {
            source.source_id: source
            for source in sources
        }
        timestamps: list[datetime] = []

        for evidence in evidence_items:
            metadata = evidence.metadata or {}
            if metadata.get("knowledge_id") != knowledge_id:
                continue

            source = source_map.get(evidence.source_id)
            if source is None or source.published_at is None:
                continue

            published_at = source.published_at
            if (
                published_at.tzinfo is None
                or published_at.utcoffset() is None
            ):
                continue

            timestamps.append(published_at)

        if not timestamps:
            return None

        return max(timestamps, key=lambda value: value.timestamp())

    def assess_pair(
        self,
        conflict: ConflictPair,
        knowledge_items: Iterable[KnowledgeCandidate],
        evidence_items: Iterable[Evidence],
        sources: Iterable[ResearchSource],
    ) -> ConflictIntelligenceAssessment:
        """
        Assess one already-detected conflict.

        The existing resolver remains authoritative for
        the actual resolution decision.
        """

        knowledge_list = list(
            knowledge_items
        )
        evidence_list = list(
            evidence_items
        )
        source_list = list(
            sources
        )

        first_evidence = self._evidence_score(
            conflict.first_knowledge_id,
            evidence_list,
        )

        second_evidence = self._evidence_score(
            conflict.second_knowledge_id,
            evidence_list,
        )

        first_source = self._source_score(
            conflict.first_knowledge_id,
            evidence_list,
            source_list,
        )

        second_source = self._source_score(
            conflict.second_knowledge_id,
            evidence_list,
            source_list,
        )

        first_confidence = self._confidence_score(
            conflict.first_knowledge_id,
            knowledge_list,
        )

        second_confidence = self._confidence_score(
            conflict.second_knowledge_id,
            knowledge_list,
        )

        resolution = self.resolver.resolve_pair(
            conflict,
            knowledge_list,
            evidence_list,
            source_list,
        )

        first_publication = self._latest_publication_time(
            conflict.first_knowledge_id,
            evidence_list,
            source_list,
        )
        second_publication = self._latest_publication_time(
            conflict.second_knowledge_id,
            evidence_list,
            source_list,
        )

        temporal_status = "UNKNOWN"
        publication_delta = None
        if (
            first_publication is not None
            and second_publication is not None
        ):
            publication_delta = round(
                (
                    first_publication - second_publication
                ).total_seconds(),
                3,
            )
            if publication_delta > 0:
                temporal_status = "FIRST_NEWER"
            elif publication_delta < 0:
                temporal_status = "SECOND_NEWER"
            else:
                temporal_status = "TIED"

        return ConflictIntelligenceAssessment(
            first_knowledge_id=(
                conflict.first_knowledge_id
            ),
            second_knowledge_id=(
                conflict.second_knowledge_id
            ),
            conflict_type=(
                self._classify_conflict(
                    conflict
                )
            ),
            conflict_reason=conflict.reason,
            resolution_status=resolution.status,
            selected_knowledge_id=(
                resolution.selected_knowledge_id
            ),
            evidence_score_delta=round(
                first_evidence - second_evidence,
                4,
            ),
            source_reliability_delta=round(
                first_source - second_source,
                4,
            ),
            knowledge_confidence_delta=round(
                first_confidence
                - second_confidence,
                4,
            ),
            resolution_reason=resolution.reason,
            temporal_comparison_status=temporal_status,
            publication_time_delta_seconds=publication_delta,
        )

    def analyze(
        self,
        knowledge_items: Iterable[KnowledgeCandidate],
        evidence_items: Iterable[Evidence] = (),
        sources: Iterable[ResearchSource] = (),
    ) -> ConflictIntelligenceResult:
        """
        Detect, resolve, and structurally assess all conflicts.
        """

        knowledge_list = list(
            knowledge_items
        )
        evidence_list = list(
            evidence_items
        )
        source_list = list(
            sources
        )

        detection = self.detector.analyze(
            knowledge_list
        )

        if not detection.conflicts:
            return ConflictIntelligenceResult(
                total_conflicts=0,
                resolved_count=0,
                unresolved_count=0,
                assessments=[],
                status="NO_CONFLICT",
            )

        assessments = [
            self.assess_pair(
                conflict,
                knowledge_list,
                evidence_list,
                source_list,
            )
            for conflict in detection.conflicts
        ]

        resolved_count = sum(
            1
            for assessment in assessments
            if assessment.resolution_status
            == RESOLUTION_RESOLVED
        )

        unresolved_count = (
            len(assessments)
            - resolved_count
        )

        if unresolved_count == 0:
            status = "ALL_RESOLVED"
        elif resolved_count > 0:
            status = "PARTIALLY_RESOLVED"
        else:
            status = "UNRESOLVED"

        return ConflictIntelligenceResult(
            total_conflicts=len(assessments),
            resolved_count=resolved_count,
            unresolved_count=unresolved_count,
            assessments=assessments,
            status=status,
        )
