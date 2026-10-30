from datetime import datetime, timezone

from core.brain.factual_answer_gate import (
    assess_verified_knowledge,
    is_factual_question,
)
from core.research.models import KnowledgeCandidate


def item(knowledge_id, statement, *, confidence=0.95, verified=True, evidence=None):
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        confidence=confidence,
        verified=verified,
        evidence=evidence if evidence is not None else ["reviewed evidence record"],
        last_verified_at=datetime.now(timezone.utc) if verified else None,
    )


def test_detects_hindi_and_english_factual_questions():
    assert is_factual_question("पौधों को सूर्य के प्रकाश की आवश्यकता क्यों होती है?")
    assert is_factual_question("Why do plants need sunlight?")
    assert is_factual_question("Explain photosynthesis in simple words.")
    assert not is_factual_question("Write a short poem about rain.")


def test_verified_evidence_can_ground_english_answer():
    knowledge = [
        item("k-plants", "Plants use sunlight to power photosynthesis and make sugars.")
    ]
    result = assess_verified_knowledge("Why do plants need sunlight?", knowledge)
    assert result.status == "VERIFIED_KNOWLEDGE"
    assert result.answer == knowledge[0].statement
    assert result.knowledge_ids == ("k-plants",)


def test_verified_evidence_can_ground_hindi_answer():
    knowledge = [
        item("k-hindi", "पौधे प्रकाश संश्लेषण के लिए सूर्य के प्रकाश का उपयोग करते हैं।")
    ]
    result = assess_verified_knowledge(
        "पौधों को सूर्य के प्रकाश की आवश्यकता क्यों होती है?", knowledge
    )
    assert result.status == "VERIFIED_KNOWLEDGE"
    assert "प्रकाश संश्लेषण" in result.answer


def test_no_evidence_fails_closed_with_uncertainty_status():
    result = assess_verified_knowledge("Why do plants need sunlight?", [])
    assert result.status == "INSUFFICIENT_EVIDENCE"
    assert result.answer is None
    assert result.reason == "no_relevant_verified_knowledge_with_evidence"


def test_unverified_or_evidence_free_claim_is_not_accepted():
    knowledge = [
        item("unverified", "Plants use sunlight for photosynthesis.", verified=False),
        item("no-evidence", "Plants use sunlight to grow.", evidence=[]),
    ]
    result = assess_verified_knowledge("Why do plants need sunlight?", knowledge)
    assert result.status == "INSUFFICIENT_EVIDENCE"


def test_conflicting_verified_evidence_is_not_silently_chosen():
    knowledge = [
        item("k-yes", "Plants need sunlight for photosynthesis."),
        item("k-no", "Plants do not need sunlight for photosynthesis."),
    ]
    result = assess_verified_knowledge("Why do plants need sunlight?", knowledge)
    assert result.status == "CONFLICTING_EVIDENCE"
    assert result.answer is None
