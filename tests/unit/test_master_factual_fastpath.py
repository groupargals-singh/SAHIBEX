from core.brain.master_brain import MasterBrain


def test_sahibex_project_identity_is_answered_from_curated_project_definition():
    brain = MasterBrain()
    for question in (
        "SAHIBEX kya hai? Hindi mein 3 points.",
        "What is SAHIBEX? Explain in 3 points.",
    ):
        result = brain.process(question)
        assert result.success is True
        assert result.verification_status == "CURATED_KNOWLEDGE"
        assert result.metadata.get("response_source") == "curated_local_knowledge"
        assert result.metadata.get("fact_id", "").startswith("SAHIBEX-PROJECT-IDENTITY-001")
        assert "Main Brain" in result.message
        assert ("vikasadhin" in result.message) if "Hindi" in question else ("under development" in result.message)
        assert ("SAHIBEX ke baare mein" in result.message) if "Hindi" in question else ("SAHIBEX in 3 points" in result.message)


def test_exact_curated_question_is_not_claimed_fully_verified():
    brain = MasterBrain()
    result = brain.process("भारत की राजधानी क्या है?")
    assert result.success is True
    assert "नई दिल्ली" in result.message
    assert result.verification_status == "CURATED_KNOWLEDGE"
    assert result.metadata.get("response_source") == "curated_local_knowledge"
    assert result.metadata.get("fact_id") == "IN-CAPITAL-001"


def test_curated_compound_question_uses_explicit_complete_fact():
    brain = MasterBrain()
    result = brain.process("भारत की राजधानी क्या है और इतिहास भी बताओ?")
    assert result.success is True
    assert "नई दिल्ली" in result.message
    assert "1911" in result.message and "1931" in result.message
    assert result.metadata.get("fact_id") == "IN-CAPITAL-HISTORY-001"
    assert result.verification_status == "CURATED_KNOWLEDGE"


def main():
    test_exact_curated_question_is_not_claimed_fully_verified()
    test_compound_question_does_not_use_substring_fastpath()
    print("SAHIBEX MASTER FACTUAL FAST-PATH TEST: PASS")


if __name__ == "__main__":
    main()
