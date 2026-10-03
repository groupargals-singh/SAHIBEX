from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from core.research.models import Evidence, KnowledgeCandidate, ResearchSource


@dataclass(frozen=True)
class EvidenceTrace:
    evidence_id: str
    knowledge_id: str
    finding_id: str
    source_id: Optional[str]
    evidence_text: str
    supports: bool
    strength: float


@dataclass(frozen=True)
class SourceTrace:
    source_id: str
    title: str
    publisher: Optional[str]
    source_type: str
    locator: str
    reliability: float


@dataclass(frozen=True)
class KnowledgeTrace:
    knowledge_id: str
    statement: str
    confidence: float
    verified: bool
    evidence: List[EvidenceTrace] = field(default_factory=list)
    sources: List[SourceTrace] = field(default_factory=list)


@dataclass(frozen=True)
class ResearchTraceabilityResult:
    knowledge_count: int
    evidence_count: int
    source_count: int
    traces: List[KnowledgeTrace]
    status: str


class ResearchTraceabilityEngine:
    """
    Builds an auditable trace from knowledge -> evidence -> source.

    The engine is deliberately conservative:
    evidence is attached to knowledge only when the evidence metadata
    explicitly contains a valid knowledge_id.
    """

    def trace(
        self,
        knowledge_items: Iterable[KnowledgeCandidate],
        evidence_items: Iterable[Evidence] = (),
        sources: Iterable[ResearchSource] = (),
    ) -> ResearchTraceabilityResult:

        knowledge_list = list(knowledge_items)
        evidence_list = list(evidence_items)
        source_list = list(sources)

        knowledge_map: Dict[str, KnowledgeCandidate] = {
            item.knowledge_id: item
            for item in knowledge_list
            if item.knowledge_id
        }

        source_map: Dict[str, ResearchSource] = {
            source.source_id: source
            for source in source_list
            if source.source_id
        }

        evidence_by_knowledge: Dict[str, List[EvidenceTrace]] = {}

        for evidence in evidence_list:
            metadata = evidence.metadata or {}

            knowledge_id = metadata.get("knowledge_id")

            if not isinstance(knowledge_id, str):
                continue

            if knowledge_id not in knowledge_map:
                continue

            source_id = evidence.source_id

            trace = EvidenceTrace(
                evidence_id=evidence.evidence_id,
                knowledge_id=knowledge_id,
                finding_id=evidence.finding_id,
                source_id=source_id,
                evidence_text=evidence.evidence_text,
                supports=bool(evidence.supports),
                strength=float(evidence.strength),
            )

            evidence_by_knowledge.setdefault(
                knowledge_id,
                [],
            ).append(trace)

        traces: List[KnowledgeTrace] = []

        for knowledge in knowledge_list:
            knowledge_id = knowledge.knowledge_id

            knowledge_evidence = evidence_by_knowledge.get(
                knowledge_id,
                [],
            )

            traced_sources: List[SourceTrace] = []
            seen_sources = set()

            for evidence in knowledge_evidence:
                source_id = evidence.source_id

                if not source_id:
                    continue

                if source_id in seen_sources:
                    continue

                source = source_map.get(source_id)

                if source is None:
                    continue

                seen_sources.add(source_id)

                traced_sources.append(
                    SourceTrace(
                        source_id=source.source_id,
                        title=source.title,
                        publisher=source.publisher,
                        source_type=source.source_type,
                        locator=source.locator,
                        reliability=float(source.reliability),
                    )
                )

            traces.append(
                KnowledgeTrace(
                    knowledge_id=knowledge_id,
                    statement=knowledge.statement,
                    confidence=float(knowledge.confidence),
                    verified=bool(knowledge.verified),
                    evidence=knowledge_evidence,
                    sources=traced_sources,
                )
            )

        evidence_count = sum(
            len(trace.evidence)
            for trace in traces
        )

        source_count = len({
            source.source_id
            for trace in traces
            for source in trace.sources
        })

        if not traces:
            status = "NO_KNOWLEDGE"
        elif evidence_count == 0:
            status = "NO_TRACEABLE_EVIDENCE"
        elif source_count == 0:
            status = "EVIDENCE_WITHOUT_SOURCE"
        else:
            status = "TRACEABLE"

        return ResearchTraceabilityResult(
            knowledge_count=len(traces),
            evidence_count=evidence_count,
            source_count=source_count,
            traces=traces,
            status=status,
        )
