from types import SimpleNamespace

from core.research.answer_arbitration import AnswerArbitrator


def test_arbitrator_accepts_matching_supported_candidates():
    quality = SimpleNamespace(
        claims=[
            SimpleNamespace(knowledge_id="k1"),
            SimpleNamespace(knowledge_id="k2"),
        ],
        overall_status="MULTI_SOURCE_SUPPORTED",
    )
    synthesized = SimpleNamespace(
        knowledge_ids=["k1", "k2"],
        verified=True,
    )

    result = AnswerArbitrator().arbitrate(
        quality_answer=quality,
        synthesized_answer=synthesized,
        unresolved_conflicts=0,
    )

    assert result.accepted is True
    assert result.status == "ACCEPTED"
    assert result.candidate_a_claim_ids == ("k1", "k2")
    assert result.candidate_b_claim_ids == ("k1", "k2")
    assert result.reasons == ()


def test_arbitrator_rejects_candidate_claim_disagreement():
    quality = SimpleNamespace(
        claims=[SimpleNamespace(knowledge_id="k1")],
        overall_status="SUPPORTED",
    )
    synthesized = SimpleNamespace(
        knowledge_ids=["k2"],
        verified=True,
    )

    result = AnswerArbitrator().arbitrate(
        quality_answer=quality,
        synthesized_answer=synthesized,
        unresolved_conflicts=0,
    )

    assert result.accepted is False
    assert "candidate_claim_sets_disagree" in result.reasons


def test_arbitrator_rejects_unverified_or_conflicted_candidates():
    quality = SimpleNamespace(
        claims=[SimpleNamespace(knowledge_id="k1")],
        overall_status="CONFLICTED",
    )
    synthesized = SimpleNamespace(
        knowledge_ids=["k1"],
        verified=False,
    )

    result = AnswerArbitrator().arbitrate(
        quality_answer=quality,
        synthesized_answer=synthesized,
        unresolved_conflicts=1,
    )

    assert result.accepted is False
    assert "quality_candidate_not_supported" in result.reasons
    assert "synthesis_candidate_not_verified" in result.reasons
    assert "unresolved_conflicts_present" in result.reasons


def test_arbitrator_rejects_empty_candidates():
    result = AnswerArbitrator().arbitrate(
        quality_answer=SimpleNamespace(claims=[], overall_status="SUPPORTED"),
        synthesized_answer=SimpleNamespace(knowledge_ids=[], verified=False),
        unresolved_conflicts=0,
    )

    assert result.accepted is False
    assert "one_or_both_candidates_empty" in result.reasons
