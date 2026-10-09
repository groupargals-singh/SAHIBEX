from core.brain.answer_quality import assess_answer


def test_rejects_question_echo():
    result = assess_answer(
        "आसमान नीला क्यों दिखाई देता है?",
        "आसमान नीला क्यों दिखाई देता है? यह आसमान के दिन रात के बीच दिखाई देने के लिए",
    )
    assert not result.acceptable
    assert "question_echo_without_new_content" in result.reasons


def test_accepts_relevant_new_answer():
    result = assess_answer(
        "आसमान नीला क्यों दिखाई देता है?",
        "वायुमंडल के अणु सूर्य के प्रकाश की नीली तरंगों को अधिक बिखेरते हैं।",
    )
    assert result.acceptable


def test_rejects_internal_context_leak():
    result = assess_answer("Explain this", "Intent: explain. Memory data: none.")
    assert not result.acceptable
    assert "instruction_or_context_leak" in result.reasons


def test_empty_answer_fails_closed():
    assert not assess_answer("Question?", "  ").acceptable


def test_rejects_obvious_truncated_numeric_ending():
    result = assess_answer(
        "भारत की राजधानी और इतिहास बताओ",
        "नई दिल्ली की स्थापना 193",
    )
    assert not result.acceptable
    assert "possible_truncated_output" in result.reasons


def main():
    test_rejects_question_echo()
    test_accepts_relevant_new_answer()
    test_rejects_internal_context_leak()
    test_empty_answer_fails_closed()
    test_rejects_obvious_truncated_numeric_ending()
    print("SAHIBEX ANSWER QUALITY TEST: PASS")


if __name__ == "__main__":
    main()
