from core.research.answer import ResearchAnswerSynthesizer
from core.research.answer_synthesis import QualityAwareAnswer
from core.research.answer_traceability import AnswerTraceabilityResult
from core.research.aggregator import AggregatedKnowledge, ResearchAggregationResult


def make_aggregation(quality_status: str) -> ResearchAggregationResult:
    return ResearchAggregationResult(
        total_candidates=1,
        verified_count=1,
        unverified_count=0,
        results=[
            AggregatedKnowledge(
                knowledge_id="knowledge-1",
                statement="A candidate claim.",
                confidence=0.95,
                verified=True,
            )
        ],
        overall_confidence=0.95,
        status="VERIFIED",
        conflict_count=0,
        conflict_ids=[],
        resolved_conflict_count=0,
        unresolved_conflict_count=0,
        resolved_knowledge_ids=[],
        agreement_assessments=[],
        conflict_intelligence=[],
        freshness_assessments=[],
        confidence_assessments=[],
        source_ranking_assessments=[],
        answer=QualityAwareAnswer(
            answer="A candidate claim.",
            claims=(),
            supported_claims=("A candidate claim.",) if quality_status == "SUPPORTED" else (),
            uncertain_claims=(),
            conflicted_claims=(),
            stale_claims=("A candidate claim.",) if quality_status == "STALE" else (),
            overall_status=quality_status,
            overall_confidence=0.95,
        ),
        answer_traceability=AnswerTraceabilityResult(
            answer_id="answer-1",
            traces=(),
            traceable_claim_count=0,
            incomplete_claim_count=0,
            trace_complete=False,
        ),
    )


def test_stale_quality_aware_answer_cannot_be_promoted_to_verified():
    result = ResearchAnswerSynthesizer().synthesize(
        "What is the claim?", make_aggregation("STALE")
    )
    assert result.verified is False
    assert result.status == "STALE"


def test_supported_quality_aware_answer_can_remain_verified():
    result = ResearchAnswerSynthesizer().synthesize(
        "What is the claim?", make_aggregation("SUPPORTED")
    )
    assert result.verified is True
    assert result.status == "VERIFIED"
