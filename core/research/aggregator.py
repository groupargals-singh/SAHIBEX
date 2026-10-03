from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List

from core.research.agreement import (
    MultiSourceAgreementAssessment,
    assess_multi_source_agreement,
)

from core.research.answer_synthesis import (
    QualityAwareAnswer,
    QualityAwareAnswerSynthesizer,
)

from core.research.answer_traceability import (
    AnswerTraceabilityEngine,
    AnswerTraceabilityResult,
)

from core.research.conflict import (
    ConflictPair,
    ResearchConflictDetector,
)

from core.research.conflict_intelligence import (
    ConflictIntelligenceAssessment,
    ResearchConflictIntelligence,
)

from core.research.conflict_resolver import (
    ConflictResolutionResult,
    EvidenceAwareConflictResolver,
)

from core.research.confidence import (
    ResearchConfidenceAssessment,
    ResearchConfidenceEngine,
)

from core.research.evidence_strength import (
    EvidenceStrengthAssessment,
)

from core.research.freshness import (
    FreshnessAssessment,
    assess_source_freshness,
)

from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchFinding,
    ResearchSource,
    utc_now,
)

from core.research.source_quality import (
    SourceQualityAssessment,
    assess_source_quality,
)

from core.research.source_ranking import (
    SourceRankingAssessment,
    SourceRankingEngine,
)


@dataclass(frozen=True)
class AggregatedKnowledge:
    knowledge_id: str
    statement: str
    confidence: float
    verified: bool


@dataclass(frozen=True)
class ResearchAggregationResult:
    total_candidates: int
    verified_count: int
    unverified_count: int

    results: List[AggregatedKnowledge]

    overall_confidence: float
    status: str

    conflict_count: int
    conflict_ids: List[str]

    resolved_conflict_count: int
    unresolved_conflict_count: int

    resolved_knowledge_ids: List[str]

    agreement_assessments: List[
        MultiSourceAgreementAssessment
    ]

    conflict_intelligence: List[
        ConflictIntelligenceAssessment
    ]

    freshness_assessments: List[
        FreshnessAssessment
    ]

    confidence_assessments: List[
        ResearchConfidenceAssessment
    ]

    source_ranking_assessments: List[
        SourceRankingAssessment
    ]

    answer: QualityAwareAnswer

    answer_traceability: AnswerTraceabilityResult


class ResearchResultAggregator:
    """
    Resolution-aware deterministic research aggregator.

    Pipeline:

        deduplicate
            ↓
        multi-source agreement assessment
            ↓
        timestamp / freshness assessment
            ↓
        source quality assessment
            ↓
        evidence strength assessment
            ↓
        conflict detection
            ↓
        evidence-aware resolution
            ↓
        conflict intelligence assessment
            ↓
        research confidence assessment
            ↓
        source ranking assessment
            ↓
        safe aggregation
            ↓
        quality-aware answer synthesis
            ↓
        answer traceability

    Rules:
    - duplicate knowledge IDs are removed
    - multi-source agreement is measured across
      distinct evidence source IDs
    - multiple evidence records from one source count
      as one source
    - freshness is measured independently
    - source quality is measured independently
    - evidence strength is measured independently
    - conflicts are detected before aggregation
    - resolved conflicts may contribute their selected claim
    - unresolved conflicts are excluded from final results
    - knowledge is never deleted or mutated
    - evidence is never deleted or mutated
    - sources are never deleted or mutated
    - conflict metadata is preserved
    - conflict intelligence is observational
    - freshness is observational
    - confidence is observational
    - source ranking is observational
    - answer synthesis is observational
    - answer traceability is observational
    - answer synthesis does not treat confidence as truth
    - unresolved conflicts are explicitly surfaced
    - unverified claims are not presented as verified facts
    - verified knowledge is preferred
    - higher confidence ranks first
    - freshness does not alter knowledge ranking
    - 6G-7 confidence does not silently replace
      KnowledgeCandidate.confidence
    - 6G-8 source ranking does not silently replace
      existing knowledge selection
    - 6G-9 answer synthesis does not silently replace
      existing knowledge selection
    - 6G-9C answer traceability does not replace
      answer synthesis or aggregation selection
    """

    def __init__(
        self,
        conflict_detector: ResearchConflictDetector | None = None,
        conflict_resolver: EvidenceAwareConflictResolver | None = None,
        conflict_intelligence: ResearchConflictIntelligence | None = None,
        confidence_engine: ResearchConfidenceEngine | None = None,
        source_ranking_engine: SourceRankingEngine | None = None,
        answer_synthesizer: QualityAwareAnswerSynthesizer | None = None,
        answer_traceability_engine: AnswerTraceabilityEngine | None = None,
    ) -> None:

        self.conflict_detector = (
            conflict_detector
            if conflict_detector is not None
            else ResearchConflictDetector()
        )

        self.conflict_resolver = (
            conflict_resolver
            if conflict_resolver is not None
            else EvidenceAwareConflictResolver()
        )

        self.conflict_intelligence = (
            conflict_intelligence
            if conflict_intelligence is not None
            else ResearchConflictIntelligence(
                detector=self.conflict_detector,
                resolver=self.conflict_resolver,
            )
        )

        self.confidence_engine = (
            confidence_engine
            if confidence_engine is not None
            else ResearchConfidenceEngine()
        )

        self.source_ranking_engine = (
            source_ranking_engine
            if source_ranking_engine is not None
            else SourceRankingEngine()
        )

        self.answer_synthesizer = (
            answer_synthesizer
            if answer_synthesizer is not None
            else QualityAwareAnswerSynthesizer()
        )

        self.answer_traceability_engine = (
            answer_traceability_engine
            if answer_traceability_engine is not None
            else AnswerTraceabilityEngine()
        )

    @staticmethod
    def _deduplicate(
        knowledge_items: Iterable[KnowledgeCandidate],
    ) -> list[KnowledgeCandidate]:

        unique: dict[
            str,
            KnowledgeCandidate,
        ] = {}

        for knowledge in knowledge_items:
            unique[knowledge.knowledge_id] = knowledge

        return list(unique.values())

    @staticmethod
    def _overall_confidence(
        knowledge_items: list[KnowledgeCandidate],
    ) -> float:

        if not knowledge_items:
            return 0.0

        total = sum(
            knowledge.confidence
            for knowledge in knowledge_items
        )

        return total / len(knowledge_items)

    @staticmethod
    def _conflict_pairs(
        knowledge_items: list[KnowledgeCandidate],
        detector: ResearchConflictDetector,
    ) -> list[ConflictPair]:

        conflicts: list[ConflictPair] = []

        for index, first in enumerate(
            knowledge_items
        ):
            for second in knowledge_items[
                index + 1:
            ]:
                conflict = detector.detect_pair(
                    first,
                    second,
                )

                if conflict is not None:
                    conflicts.append(conflict)

        return conflicts

    @staticmethod
    def _resolved_ids(
        resolution_result: ConflictResolutionResult,
    ) -> set[str]:

        return {
            resolution.selected_knowledge_id
            for resolution in resolution_result.resolutions
            if (
                resolution.status == "RESOLVED"
                and resolution.selected_knowledge_id
                is not None
            )
        }

    @staticmethod
    def _unresolved_ids(
        resolution_result: ConflictResolutionResult,
    ) -> set[str]:

        unresolved: set[str] = set()

        for resolution in resolution_result.resolutions:

            if resolution.status != "UNRESOLVED":
                continue

            unresolved.add(
                resolution.first_knowledge_id
            )

            unresolved.add(
                resolution.second_knowledge_id
            )

        return unresolved

    @staticmethod
    def _agreement_assessments(
        knowledge_items: list[KnowledgeCandidate],
        evidence_items: list[Evidence],
        sources: list[ResearchSource],
    ) -> list[MultiSourceAgreementAssessment]:
        """
        Build one 6G-4 agreement assessment per
        unique knowledge candidate.

        Agreement is based on distinct source IDs linked
        through Evidence.metadata["knowledge_id"].

        This does not modify knowledge, evidence,
        or sources.
        """

        return [
            assess_multi_source_agreement(
                knowledge=knowledge,
                evidence_items=evidence_items,
                sources=sources,
            )
            for knowledge in knowledge_items
        ]

    @staticmethod
    def _freshness_assessments(
        sources: list[ResearchSource],
        *,
        reference_time: datetime,
    ) -> list[FreshnessAssessment]:
        """
        Build one 6G-6 freshness assessment per source.

        Freshness is observational only.
        """

        return [
            assess_source_freshness(
                source,
                reference_time=reference_time,
            )
            for source in sources
        ]

    @staticmethod
    def _quality_assessments(
        sources: list[ResearchSource],
    ) -> list[SourceQualityAssessment]:
        """
        Build one 6G-2 source-quality assessment per source.

        Source quality is observational only.
        """

        return [
            assess_source_quality(source)
            for source in sources
        ]

    @staticmethod
    def _evidence_strength_assessments(
        knowledge_items: list[KnowledgeCandidate],
        evidence_items: list[Evidence],
        sources: list[ResearchSource],
    ) -> list[EvidenceStrengthAssessment]:
        """
        Read already-computed 6G-3 evidence-strength
        assessments from Evidence.metadata.

        The extraction pipeline stores the canonical
        assessment under:

            Evidence.metadata["evidence_strength"]

        Missing metadata is ignored here.
        It is handled conservatively by the confidence
        engine.
        """

        assessments: list[
            EvidenceStrengthAssessment
        ] = []

        knowledge_ids = {
            knowledge.knowledge_id
            for knowledge in knowledge_items
        }

        source_map = {
            source.source_id: source
            for source in sources
        }

        for evidence in evidence_items:

            metadata = evidence.metadata or {}

            knowledge_id = metadata.get(
                "knowledge_id"
            )

            if knowledge_id not in knowledge_ids:
                continue

            raw = metadata.get(
                "evidence_strength"
            )

            if not isinstance(raw, dict):
                continue

            try:
                assessment = (
                    EvidenceStrengthAssessment(
                        evidence_id=evidence.evidence_id,
                        strength_score=float(
                            raw.get(
                                "strength_score",
                                0.0,
                            )
                        ),
                        directness_score=float(
                            raw.get(
                                "directness_score",
                                0.0,
                            )
                        ),
                        specificity_score=float(
                            raw.get(
                                "specificity_score",
                                0.0,
                            )
                        ),
                        finding_linkage_score=float(
                            raw.get(
                                "finding_linkage_score",
                                0.0,
                            )
                        ),
                        source_linkage_score=float(
                            raw.get(
                                "source_linkage_score",
                                0.0,
                            )
                        ),
                        extraction_confidence_score=float(
                            raw.get(
                                "extraction_confidence_score",
                                0.0,
                            )
                        ),
                        version=str(
                            raw.get(
                                "version",
                                "6G-3",
                            )
                        ),
                    )
                )

            except (
                TypeError,
                ValueError,
            ):
                continue

            if evidence.source_id not in source_map:
                continue

            assessments.append(
                assessment
            )

        return assessments

    def _conflict_intelligence_assessments(
        self,
        conflicts: list[ConflictPair],
        knowledge_items: list[KnowledgeCandidate],
        evidence_items: list[Evidence],
        sources: list[ResearchSource],
    ) -> list[ConflictIntelligenceAssessment]:
        """
        Build one 6G-5 intelligence assessment per
        detected conflict.

        The existing resolver remains authoritative.
        """

        return [
            self.conflict_intelligence.assess_pair(
                conflict,
                knowledge_items,
                evidence_items,
                sources,
            )
            for conflict in conflicts
        ]

    def _confidence_assessments(
        self,
        knowledge_items: list[KnowledgeCandidate],
        evidence_items: list[Evidence],
        sources: list[ResearchSource],
        evidence_assessments: list[
            EvidenceStrengthAssessment
        ],
        agreement_assessments: list[
            MultiSourceAgreementAssessment
        ],
        conflict_intelligence: list[
            ConflictIntelligenceAssessment
        ],
        freshness_assessments: list[
            FreshnessAssessment
        ],
        quality_assessments: list[
            SourceQualityAssessment
        ],
    ) -> list[ResearchConfidenceAssessment]:
        """
        Build one 6G-7 confidence assessment per
        knowledge candidate.

        Confidence is observational.

        It does not modify
        KnowledgeCandidate.confidence.
        """

        return [
            self.confidence_engine.assess(
                knowledge=knowledge,
                evidence_items=evidence_items,
                sources=sources,
                evidence_assessments=(
                    evidence_assessments
                ),
                agreement_assessments=(
                    agreement_assessments
                ),
                conflict_assessments=(
                    conflict_intelligence
                ),
                freshness_assessments=(
                    freshness_assessments
                ),
                quality_assessments=(
                    quality_assessments
                ),
            )
            for knowledge in knowledge_items
        ]

    @staticmethod
    def _source_knowledge_map(
        knowledge_items: list[KnowledgeCandidate],
        evidence_items: list[Evidence],
        sources: list[ResearchSource],
    ) -> dict[str, list[str]]:
        """
        Build deterministic source -> knowledge mapping.

        Evidence.metadata["knowledge_id"] is the canonical
        relationship used by the research pipeline.

        This method is observational only.
        """

        valid_source_ids = {
            source.source_id
            for source in sources
        }

        knowledge_ids = {
            knowledge.knowledge_id
            for knowledge in knowledge_items
        }

        mapping: dict[
            str,
            set[str],
        ] = {
            source_id: set()
            for source_id in valid_source_ids
        }

        for evidence in evidence_items:

            source_id = evidence.source_id

            if source_id not in valid_source_ids:
                continue

            knowledge_id = (
                evidence.metadata or {}
            ).get(
                "knowledge_id"
            )

            if knowledge_id not in knowledge_ids:
                continue

            mapping[source_id].add(
                knowledge_id
            )

        return {
            source_id: sorted(
                linked_knowledge_ids
            )
            for (
                source_id,
                linked_knowledge_ids,
            ) in mapping.items()
        }

    def _source_ranking_assessments(
        self,
        knowledge_items: list[KnowledgeCandidate],
        evidence_items: list[Evidence],
        sources: list[ResearchSource],
        evidence_assessments: list[
            EvidenceStrengthAssessment
        ],
        agreement_assessments: list[
            MultiSourceAgreementAssessment
        ],
        conflict_intelligence: list[
            ConflictIntelligenceAssessment
        ],
        freshness_assessments: list[
            FreshnessAssessment
        ],
        quality_assessments: list[
            SourceQualityAssessment
        ],
        confidence_assessments: list[
            ResearchConfidenceAssessment
        ],
    ) -> list[SourceRankingAssessment]:
        """
        Build 6G-8 source rankings.

        Source ranking is observational only.

        Existing KnowledgeCandidate confidence and
        knowledge selection remain unchanged.
        """

        source_knowledge_map = (
            self._source_knowledge_map(
                knowledge_items=knowledge_items,
                evidence_items=evidence_items,
                sources=sources,
            )
        )

        return self.source_ranking_engine.rank(
            sources=sources,
            quality_assessments=quality_assessments,
            evidence_assessments=evidence_assessments,
            agreement_assessments=agreement_assessments,
            conflict_assessments=conflict_intelligence,
            freshness_assessments=freshness_assessments,
            confidence_assessments=confidence_assessments,
            source_knowledge_map=source_knowledge_map,
        )

    def aggregate(
        self,
        knowledge_items: Iterable[KnowledgeCandidate],
        *,
        verified_only: bool = True,
        limit: int = 10,
        evidence_items: Iterable[Evidence] = (),
        sources: Iterable[ResearchSource] = (),
        findings: Iterable[ResearchFinding] = (),
        reference_time: datetime | None = None,
    ) -> ResearchAggregationResult:

        if not isinstance(limit, int):
            raise TypeError(
                "limit must be an integer"
            )

        if limit < 1:
            raise ValueError(
                "limit must be >= 1"
            )

        unique_items = self._deduplicate(
            knowledge_items
        )

        evidence_items = list(
            evidence_items
        )

        sources = list(
            sources
        )

        findings = list(
            findings
        )

        if reference_time is None:
            reference_time = utc_now()

        # -------------------------------------------------
        # 6G-4 Multi-Source Agreement
        # -------------------------------------------------

        agreement_assessments = (
            self._agreement_assessments(
                unique_items,
                evidence_items,
                sources,
            )
        )

        # -------------------------------------------------
        # 6G-6 Timestamp / Freshness
        # -------------------------------------------------

        freshness_assessments = (
            self._freshness_assessments(
                sources,
                reference_time=reference_time,
            )
        )

        # -------------------------------------------------
        # 6G-2 Source Quality
        # -------------------------------------------------

        quality_assessments = (
            self._quality_assessments(
                sources
            )
        )

        # -------------------------------------------------
        # 6G-3 Evidence Strength
        # -------------------------------------------------

        evidence_strength_assessments = (
            self._evidence_strength_assessments(
                unique_items,
                evidence_items,
                sources,
            )
        )

        # -------------------------------------------------
        # Conflict Detection
        # -------------------------------------------------

        conflicts = self._conflict_pairs(
            unique_items,
            self.conflict_detector,
        )

        # -------------------------------------------------
        # Conflict Resolution
        # -------------------------------------------------

        resolution_result = (
            self.conflict_resolver.resolve(
                conflicts,
                unique_items,
                evidence_items,
                sources,
            )
        )

        # -------------------------------------------------
        # 6G-5 Conflict Intelligence
        # -------------------------------------------------

        conflict_intelligence = (
            self._conflict_intelligence_assessments(
                conflicts,
                unique_items,
                evidence_items,
                sources,
            )
        )

        # -------------------------------------------------
        # 6G-7 Research Confidence
        # -------------------------------------------------

        confidence_assessments = (
            self._confidence_assessments(
                unique_items,
                evidence_items,
                sources,
                evidence_strength_assessments,
                agreement_assessments,
                conflict_intelligence,
                freshness_assessments,
                quality_assessments,
            )
        )

        # -------------------------------------------------
        # 6G-8 Source Ranking
        # -------------------------------------------------

        source_ranking_assessments = (
            self._source_ranking_assessments(
                knowledge_items=unique_items,
                evidence_items=evidence_items,
                sources=sources,
                evidence_assessments=(
                    evidence_strength_assessments
                ),
                agreement_assessments=(
                    agreement_assessments
                ),
                conflict_intelligence=(
                    conflict_intelligence
                ),
                freshness_assessments=(
                    freshness_assessments
                ),
                quality_assessments=(
                    quality_assessments
                ),
                confidence_assessments=(
                    confidence_assessments
                ),
            )
        )

        # -------------------------------------------------
        # Conflict Metadata
        # -------------------------------------------------

        conflict_ids: set[str] = set()

        for conflict in conflicts:

            conflict_ids.add(
                conflict.first_knowledge_id
            )

            conflict_ids.add(
                conflict.second_knowledge_id
            )

        resolved_ids = self._resolved_ids(
            resolution_result
        )

        unresolved_ids = self._unresolved_ids(
            resolution_result
        )

        # -------------------------------------------------
        # Candidate Statistics
        # -------------------------------------------------

        verified_count = sum(
            1
            for knowledge in unique_items
            if knowledge.verified
        )

        unverified_count = (
            len(unique_items)
            - verified_count
        )

        # -------------------------------------------------
        # Safe Selection
        #
        # 6G-7 and 6G-8 do not replace the existing
        # selection policy.
        # -------------------------------------------------

        selectable: list[
            KnowledgeCandidate
        ] = []

        for knowledge in unique_items:

            knowledge_id = (
                knowledge.knowledge_id
            )

            if knowledge_id in unresolved_ids:
                continue

            if (
                knowledge_id in conflict_ids
                and knowledge_id not in resolved_ids
            ):
                continue

            selectable.append(
                knowledge
            )

        # -------------------------------------------------
        # Verified-only Filtering
        # -------------------------------------------------

        if verified_only:

            selectable = [
                knowledge
                for knowledge in selectable
                if knowledge.verified
            ]

        # -------------------------------------------------
        # Deterministic Ranking
        # -------------------------------------------------

        selectable.sort(
            key=lambda knowledge: (
                knowledge.verified,
                knowledge.confidence,
            ),
            reverse=True,
        )

        selected = selectable[:limit]

        # -------------------------------------------------
        # Aggregated Results
        # -------------------------------------------------

        results = [
            AggregatedKnowledge(
                knowledge_id=knowledge.knowledge_id,
                statement=knowledge.statement,
                confidence=knowledge.confidence,
                verified=knowledge.verified,
            )
            for knowledge in selected
        ]

        # -------------------------------------------------
        # 6G-9 Quality-Aware Answer Synthesis
        #
        # IMPORTANT:
        # Answer synthesis operates on the already-selected
        # knowledge. It does not replace or override the
        # existing aggregation selection policy.
        # -------------------------------------------------

        answer = self.answer_synthesizer.synthesize(
            knowledge_items=selected,
            evidence_items=evidence_items,
            sources=sources,
            confidence_assessments=(
                confidence_assessments
            ),
            agreement_assessments=(
                agreement_assessments
            ),
            conflict_assessments=(
                conflict_intelligence
            ),
            freshness_assessments=(
                freshness_assessments
            ),
            source_ranking_assessments=(
                source_ranking_assessments
            ),
        )

        # -------------------------------------------------
        # 6G-9C Answer Traceability
        #
        # IMPORTANT:
        # Traceability operates on the actual synthesized
        # answer and the actual selected knowledge.
        #
        # It is observational only.
        # It does not change:
        # - selection
        # - verification
        # - confidence
        # - answer content
        # -------------------------------------------------

        answer_traceability = (
            self.answer_traceability_engine.trace_answer(
                answer=answer,
                knowledge_items=selected,
                findings=findings,
                evidence_items=evidence_items,
                sources=sources,
            )
        )

        # -------------------------------------------------
        # Overall Confidence
        #
        # Existing KnowledgeCandidate confidence remains
        # the aggregation confidence for backward
        # compatibility.
        #
        # 6G-7 is exposed separately through
        # confidence_assessments.
        # -------------------------------------------------

        overall_confidence = (
            self._overall_confidence(
                selected
            )
        )

        # -------------------------------------------------
        # Conflict Statistics
        # -------------------------------------------------

        conflict_count = (
            resolution_result.total_conflicts
        )

        resolved_count = (
            resolution_result.resolved_count
        )

        unresolved_count = (
            resolution_result.unresolved_count
        )

        # -------------------------------------------------
        # Status
        # -------------------------------------------------

        if not unique_items:

            status = "NO_RESULT"

        elif (
            unresolved_count > 0
            and resolved_count > 0
        ):

            status = "PARTIALLY_RESOLVED"

        elif unresolved_count > 0:

            status = "CONFLICT_UNRESOLVED"

        elif resolved_count > 0:

            status = "CONFLICT_RESOLVED"

        elif (
            verified_only
            and verified_count > 0
        ):

            status = "VERIFIED"

        elif (
            not verified_only
            and verified_count > 0
        ):

            status = "VERIFIED_AVAILABLE"

        else:

            status = "UNVERIFIED"

        # -------------------------------------------------
        # Final Result
        # -------------------------------------------------

        return ResearchAggregationResult(
            total_candidates=len(
                unique_items
            ),

            verified_count=verified_count,

            unverified_count=unverified_count,

            results=results,

            overall_confidence=overall_confidence,

            status=status,

            conflict_count=conflict_count,

            conflict_ids=sorted(
                conflict_ids
            ),

            resolved_conflict_count=resolved_count,

            unresolved_conflict_count=unresolved_count,

            resolved_knowledge_ids=sorted(
                resolved_ids
            ),

            agreement_assessments=(
                agreement_assessments
            ),

            conflict_intelligence=(
                conflict_intelligence
            ),

            freshness_assessments=(
                freshness_assessments
            ),

            confidence_assessments=(
                confidence_assessments
            ),

            source_ranking_assessments=(
                source_ranking_assessments
            ),

            answer=answer,

            answer_traceability=(
                answer_traceability
            ),
        )
