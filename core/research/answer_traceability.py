from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from core.research.answer_synthesis import (
    AnswerClaimAssessment,
    QualityAwareAnswer,
)
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchFinding,
    ResearchSource,
)


ANSWER_TRACEABILITY_VERSION = "6G-9C"


@dataclass(frozen=True)
class AnswerTrace:
    statement: str
    knowledge_id: str
    finding_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    confidence_score: float
    answer_status: str
    verified: bool
    supported: bool
    trace_complete: bool
    missing_links: tuple[str, ...] = field(
        default_factory=tuple
    )
    version: str = ANSWER_TRACEABILITY_VERSION


@dataclass(frozen=True)
class AnswerTraceabilityResult:
    answer_id: str
    traces: tuple[AnswerTrace, ...]
    traceable_claim_count: int
    incomplete_claim_count: int
    trace_complete: bool
    version: str = ANSWER_TRACEABILITY_VERSION


class AnswerTraceabilityEngine:
    """
    6G-9C Answer Traceability Engine.

    Trace path:

        Answer Statement
            -> Knowledge
            -> Finding
            -> Evidence
            -> Source

    Design guarantees:
        - observational only
        - deterministic
        - no network access
        - no mutation of input objects
        - missing links are explicitly reported
        - traceability is not treated as truth verification
    """

    def trace_answer(
        self,
        *,
        answer: QualityAwareAnswer,
        knowledge_items: Sequence[KnowledgeCandidate],
        findings: Sequence[ResearchFinding],
        evidence_items: Sequence[Evidence],
        sources: Sequence[ResearchSource],
    ) -> AnswerTraceabilityResult:
        knowledge_by_id = {
            item.knowledge_id: item
            for item in knowledge_items
        }

        findings_by_id = {
            item.finding_id: item
            for item in findings
        }

        evidence_by_id = {
            item.evidence_id: item
            for item in evidence_items
        }

        sources_by_id = {
            item.source_id: item
            for item in sources
        }

        traces = tuple(
            self._trace_claim(
                assessment=assessment,
                knowledge_by_id=knowledge_by_id,
                findings_by_id=findings_by_id,
                evidence_by_id=evidence_by_id,
                sources_by_id=sources_by_id,
            )
            for assessment in answer.claims
        )

        traceable_count = sum(
            1
            for item in traces
            if item.trace_complete
        )

        incomplete_count = (
            len(traces) - traceable_count
        )

        return AnswerTraceabilityResult(
            answer_id=self._answer_id(answer),
            traces=traces,
            traceable_claim_count=traceable_count,
            incomplete_claim_count=incomplete_count,
            trace_complete=(
                incomplete_count == 0
            ),
        )

    def _trace_claim(
        self,
        *,
        assessment: AnswerClaimAssessment,
        knowledge_by_id: Mapping[
            str,
            KnowledgeCandidate,
        ],
        findings_by_id: Mapping[
            str,
            ResearchFinding,
        ],
        evidence_by_id: Mapping[
            str,
            Evidence,
        ],
        sources_by_id: Mapping[
            str,
            ResearchSource,
        ],
    ) -> AnswerTrace:
        knowledge_id = self._knowledge_id(
            assessment
        )

        missing_links: list[str] = []

        knowledge = None

        if knowledge_id:
            knowledge = knowledge_by_id.get(
                knowledge_id
            )

        if knowledge is None:
            missing_links.append(
                "knowledge"
            )

        finding_ids: list[str] = []
        evidence_ids: list[str] = []
        source_ids: list[str] = []

        if knowledge is not None:
            for finding_id in knowledge.findings:
                if finding_id in findings_by_id:
                    finding_ids.append(
                        finding_id
                    )
                else:
                    missing_links.append(
                        f"finding:{finding_id}"
                    )

            for evidence_id in knowledge.evidence:
                if evidence_id in evidence_by_id:
                    evidence_ids.append(
                        evidence_id
                    )
                else:
                    missing_links.append(
                        f"evidence:{evidence_id}"
                    )

        for evidence_id in evidence_ids:
            evidence = evidence_by_id[
                evidence_id
            ]

            source_id = evidence.source_id

            if source_id in sources_by_id:
                if source_id not in source_ids:
                    source_ids.append(
                        source_id
                    )
            else:
                missing_links.append(
                    f"source:{source_id}"
                )

        # A complete trace requires every declared
        # finding to exist, every declared evidence
        # item to exist, and every evidence source
        # to exist.
        trace_complete = (
            bool(knowledge_id)
            and bool(finding_ids)
            and bool(evidence_ids)
            and bool(source_ids)
            and not missing_links
        )

        return AnswerTrace(
            statement=assessment.statement,
            knowledge_id=knowledge_id,
            finding_ids=tuple(finding_ids),
            evidence_ids=tuple(evidence_ids),
            source_ids=tuple(source_ids),
            confidence_score=float(
                assessment.confidence_score
            ),
            answer_status=assessment.status,
            verified=(
                knowledge.verified
                if knowledge is not None
                else bool(assessment.verified)
            ),
            supported=bool(
                assessment.supported
            ),
            trace_complete=trace_complete,
            missing_links=tuple(
                missing_links
            ),
        )

    @staticmethod
    def _knowledge_id(
        assessment: AnswerClaimAssessment,
    ) -> str:
        value = assessment.knowledge_id

        if isinstance(value, str):
            return value.strip()

        return ""

    @staticmethod
    def _answer_id(
        answer: QualityAwareAnswer,
    ) -> str:
        value = getattr(
            answer,
            "answer_id",
            None,
        )

        if isinstance(value, str) and value.strip():
            return value.strip()

        return "answer_unknown"


def trace_answer(
    *,
    answer: QualityAwareAnswer,
    knowledge_items: Sequence[KnowledgeCandidate],
    findings: Sequence[ResearchFinding],
    evidence_items: Sequence[Evidence],
    sources: Sequence[ResearchSource],
) -> AnswerTraceabilityResult:
    """
    Functional wrapper around AnswerTraceabilityEngine.
    """
    engine = AnswerTraceabilityEngine()

    return engine.trace_answer(
        answer=answer,
        knowledge_items=knowledge_items,
        findings=findings,
        evidence_items=evidence_items,
        sources=sources,
    )
