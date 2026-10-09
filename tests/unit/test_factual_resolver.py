from core.brain.factual_resolver import resolve_local_fact


def test_resolves_india_capital_without_model():
    fact = resolve_local_fact("भारत की राजधानी क्या है?")
    assert fact is not None
    assert fact.fact_id == "IN-CAPITAL-001"
    assert "नई दिल्ली" in fact.answer
    assert "राष्ट्रीय राजधानी क्षेत्र" in fact.answer


def test_resolves_sky_color_in_hindi():
    fact = resolve_local_fact("आसमान नीला क्यों दिखाई देता है? ")
    assert fact is not None
    assert fact.fact_id == "PHYS-SCATTER-001"
    assert "बिखेरते" in fact.answer


def test_resolves_english_question():
    fact = resolve_local_fact("What is the capital of India?")
    assert fact is not None
    assert "New Delhi" in fact.answer or "नई दिल्ली" in fact.answer


def test_does_not_guess_on_unrecognized_or_expanded_question():
    assert resolve_local_fact("भारत की राजधानी क्या है और इतिहास भी बताओ?") is None
    assert resolve_local_fact("Who will win the next election?") is None
    assert resolve_local_fact("") is None


def test_resolves_photosynthesis_in_hindi_and_english():
    hindi = resolve_local_fact("प्रकाश संश्लेषण क्या है?")
    english = resolve_local_fact("Explain photosynthesis in simple Hindi.")
    assert hindi is not None and english is not None
    assert hindi.fact_id == "BIO-PHOTOSYNTHESIS-001"
    assert english.fact_id == hindi.fact_id
    assert "कार्बन डाइऑक्साइड" in hindi.answer
    assert "ऑक्सीजन" in hindi.answer


def test_does_not_partial_match_compound_photosynthesis_question():
    assert resolve_local_fact("प्रकाश संश्लेषण क्या है और पौधों के प्रकार बताओ?") is None


def test_ignores_trailing_response_format_instruction():
    fact = resolve_local_fact("भारत की राजधानी क्या है? एक छोटे वाक्य में जवाब दें।")
    assert fact is not None
    assert fact.fact_id == "IN-CAPITAL-001"


def test_ignores_english_response_format_instruction():
    fact = resolve_local_fact("What is the capital of India? Answer briefly.")
    assert fact is not None
    assert fact.fact_id == "IN-CAPITAL-001"
