from core.brain.master_brain import MasterBrain


def test_exact_curated_question_is_not_claimed_fully_verified():
    brain = MasterBrain()
    result = brain.process("भारत की राजधानी क्या है?")
    assert result.success is True
    assert "नई दिल्ली" in result.message
    assert result.verification_status == "STRUCTURALLY_VALID"
    assert result.metadata.get("response_source") == "curated_local_knowledge"
    assert result.metadata.get("fact_id") == "IN-CAPITAL-001"


def test_compound_question_does_not_use_substring_fastpath():
    brain = MasterBrain()
    result = brain.process("भारत की राजधानी क्या है और इतिहास भी बताओ?")
    assert result.metadata.get("response_source") != "curated_fast_fact"


def main():
    test_exact_curated_question_is_not_claimed_fully_verified()
    test_compound_question_does_not_use_substring_fastpath()
    print("SAHIBEX MASTER FACTUAL FAST-PATH TEST: PASS")


if __name__ == "__main__":
    main()
