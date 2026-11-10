from __future__ import annotations

import pytest

from core.brain.confidence_verification_brain import ConfidenceVerificationBrain


def test_ambiguous_word_requires_clarification():
    brain = ConfidenceVerificationBrain()
    ambiguous, question, reasons = brain.detect_ambiguity("Explain bank")
    assert ambiguous is True
    assert "financial bank" in question
    assert reasons == ("ambiguous_word:bank",)


@pytest.mark.parametrize(
    "text",
    [
        "Explain the river bank",
        "Write Python code",
        "Turn on the light bulb",
        "Take the right turn",
        "Charge my phone battery",
        "Hit the cricket bat with the ball",
    ],
)
def test_context_disambiguates_polysemy(text):
    ambiguous, _, _ = ConfidenceVerificationBrain.detect_ambiguity(text)
    assert ambiguous is False


def test_unresolved_demonstrative_requires_clarification_without_context():
    ambiguous, question, reasons = ConfidenceVerificationBrain.detect_ambiguity(
        "Ye kya hai?", language_code="hi-Latn"
    )
    assert ambiguous is True
    assert "किस चीज़" in question
    assert reasons == ("unresolved_demonstrative_reference",)


def test_demonstrative_can_use_prior_context():
    ambiguous, _, _ = ConfidenceVerificationBrain.detect_ambiguity(
        "What is this?",
        context_text="We are discussing Python programming. Python is a language.",
        language_code="en",
    )
    assert ambiguous is False


def test_action_with_unresolved_object_requires_clarification():
    ambiguous, question, reasons = ConfidenceVerificationBrain.detect_ambiguity(
        "delete it"
    )
    assert ambiguous is True
    assert "Which file" in question
    assert reasons == ("unresolved_action_reference",)


def test_assessment_separates_understanding_uncertainty_from_factual_truth():
    brain = ConfidenceVerificationBrain()
    result = brain.assess(
        input_id="test-input-1",
        text="Explain bank",
        intent_confidence=0.65,
        language_confidence=0.95,
        ambiguity_question="Do you mean a financial bank or a river bank?",
        ambiguity_reasons=("ambiguous_word:bank",),
        missing_information=True,
    )
    data = result.to_dict()
    assert result.decision == "CLARIFICATION_REQUIRED"
    assert result.clarification_required is True
    assert result.uncertainty > 0
    assert result.factual_claim_status == "NOT_FACTUALLY_VERIFIED"
    assert data["truth_score"] is False
    assert data["grants_permission"] is False
    assert data["executes_actions"] is False


def test_low_semantic_confidence_requires_clarification():
    result = ConfidenceVerificationBrain().assess(
        input_id="test-input-2",
        text="Do it",
        intent_confidence=0.30,
        language_confidence=0.90,
        semantic_confidence=0.41,
    )
    assert result.decision == "CLARIFICATION_REQUIRED"
    assert result.clarification_question


def test_generated_or_routing_verified_answer_is_not_a_verified_fact():
    brain = ConfidenceVerificationBrain()
    assert brain.factual_status_for_response("GENERATED") == "NOT_FACTUALLY_VERIFIED"
    assert brain.factual_status_for_response("STRUCTURALLY_VALID") == "NOT_FACTUALLY_VERIFIED"
    assert brain.factual_status_for_response("VERIFIED") == "NOT_FACTUALLY_VERIFIED"
    assert brain.factual_status_for_response("CURATED_KNOWLEDGE") == (
        "CURATED_KNOWLEDGE_NOT_INDEPENDENTLY_VERIFIED"
    )
    assert brain.factual_status_for_response(
        "VERIFIED", {"factual_verification": "evidence_verified"}
    ) == "EVIDENCE_VERIFIED"


def test_brain_cannot_grant_permission_execute_or_upgrade_guesses():
    brain = ConfidenceVerificationBrain()
    assert brain.grants_permission() is False
    assert brain.executes_actions() is False
    assert brain.upgrades_guess_to_fact() is False


def test_unrelated_context_does_not_resolve_action_reference():
    ambiguous, _, reasons = ConfidenceVerificationBrain.detect_ambiguity(
        "delete it", context_text="We are discussing Python programming."
    )
    assert ambiguous is True
    assert reasons == ("unresolved_action_reference",)


def test_unrelated_context_does_not_resolve_demonstrative():
    ambiguous, _, reasons = ConfidenceVerificationBrain.detect_ambiguity(
        "What is this?", context_text="Hello, how are you?"
    )
    assert ambiguous is True
    assert reasons == ("unresolved_demonstrative_reference",)


def test_context_with_specific_file_resolves_action_reference():
    ambiguous, _, _ = ConfidenceVerificationBrain.detect_ambiguity(
        "delete it", context_text="The report.docx file is the selected item."
    )
    assert ambiguous is False


def test_contextual_factual_evidence_is_read_from_operational_result():
    brain = ConfidenceVerificationBrain()
    assert brain.factual_status_for_response(
        "VERIFIED",
        {"mother_operational_integration": {"factual_verification": True}},
    ) == "EVIDENCE_VERIFIED"
    assert brain.factual_status_for_response(
        "VERIFIED",
        {"mother_operational_integration": {"factual_verification": False}},
    ) == "NOT_FACTUALLY_VERIFIED"


def test_hinglish_bat_ambiguity_includes_hindi_baat_meaning():
    ambiguous, question, _ = ConfidenceVerificationBrain.detect_ambiguity(
        "bat batao", language_code="hi-Latn"
    )
    assert ambiguous is True
    assert "बात" in question
    clear, _, _ = ConfidenceVerificationBrain.detect_ambiguity(
        "bat ki baat samjhao", language_code="hi-Latn"
    )
    assert clear is False


def test_unresolved_topic_reference_requires_a_specific_subject():
    ambiguous, question, reasons = ConfidenceVerificationBrain.detect_ambiguity(
        "Is topic par latest jankari khojo", language_code="hi-Latn"
    )
    assert ambiguous is True
    assert "किस विषय" in question
    assert reasons == ("unresolved_topic_reference",)


def test_topic_reference_can_use_a_subject_from_recent_context():
    ambiguous, _, _ = ConfidenceVerificationBrain.detect_ambiguity(
        "Is topic par latest jankari khojo",
        context_text="We are discussing Python programming and its language ecosystem.",
        language_code="hi-Latn",
    )
    assert ambiguous is False
