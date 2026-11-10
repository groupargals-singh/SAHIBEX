from dataclasses import replace
from datetime import datetime, timezone
from types import SimpleNamespace

from core.research.answer import ResearchAnswer
from core.research.answer_pipeline import ResearchAnswerPipeline
from core.research.aggregator import ResearchResultAggregator
from core.research.engine import ResearchEngine
from core.research.models import KnowledgeCandidate, ResearchSource
from core.research.query import ResearchQueryEngine


def _now():
    return datetime.now(timezone.utc)


class _BrokenTraceAggregator:
    """Inject an incomplete trace while both synthesis candidates agree."""

    def __init__(self):
        self.inner = ResearchResultAggregator()

    def aggregate(self, *args, **kwargs):
        result = self.inner.aggregate(*args, **kwargs)
        ids = [item.knowledge_id for item in result.results]
        quality_answer = replace(
            result.answer,
            overall_status="SUPPORTED",
            claims=tuple(SimpleNamespace(knowledge_id=kid) for kid in ids),
        )
        traces = [
            SimpleNamespace(
                knowledge_id=kid,
                trace_complete=False,
                supported=True,
                verified=True,
                evidence_ids=("missing-evidence",),
                source_ids=("missing-source",),
            )
            for kid in ids
        ]
        return replace(
            result,
            answer=quality_answer,
            answer_traceability=SimpleNamespace(traces=traces),
        )


class _OptimisticSynthesizer:
    """Simulate an unsafe synthesis path that claims verification."""

    def synthesize(self, query, aggregation, *, evidence_items=()):
        ids = [item.knowledge_id for item in aggregation.results]
        return ResearchAnswer(
            query=query,
            answer="A deliberately optimistic test answer.",
            confidence=1.0,
            verified=bool(ids),
            status="VERIFIED" if ids else "NO_RESULT",
            evidence=[],
            knowledge_ids=ids,
        )


def test_end_to_end_gate_rejects_verified_answer_with_incomplete_trace():
    engine = ResearchEngine()
    source = ResearchSource(
        source_id="source-final-gate",
        title="Test source",
        source_type="test",
        locator="https://source.example/test",
        publisher="Test Publisher",
        reliability=0.9,
        accessed_at=_now(),
    )
    engine.register_source(source)
    knowledge = KnowledgeCandidate(
        knowledge_id="knowledge-final-gate",
        statement="Python is used for software development.",
        findings=[],
        evidence=[],
        confidence=0.95,
        verified=True,
        created_at=_now(),
        last_verified_at=_now(),
        metadata={"source_id": source.source_id, "verification_status": "VERIFIED"},
    )
    engine.knowledge[knowledge.knowledge_id] = knowledge

    pipeline = ResearchAnswerPipeline(
        query_engine=ResearchQueryEngine(engine),
        aggregator=_BrokenTraceAggregator(),
        synthesizer=_OptimisticSynthesizer(),
    )
    result = pipeline.run("Python software development")

    assert result.answer.verified is False
    assert result.answer.status == "TRACEABILITY_REJECTED"
    assert result.arbitration.accepted is False
    assert "synthesis_candidate_not_verified" in result.arbitration.reasons
