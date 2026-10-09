from core.brain.math_resolver import resolve_math_question
from core.brain.master_brain import MasterBrain


def test_resolves_hindi_arithmetic_question():
    result = resolve_math_question("2 + 2 कितना होता है?")
    assert result is not None
    assert result.answer == "उत्तर: 4"


def test_supports_parentheses_and_precedence():
    assert resolve_math_question("(3 + 5) * 2 कितना है?").answer == "उत्तर: 16"
    assert resolve_math_question("10 / 4 कितना है?").answer == "उत्तर: 2.5"


def test_rejects_division_by_zero_and_unsupported_code():
    assert resolve_math_question("1 / 0 कितना है?") is None
    assert resolve_math_question("__import__('os').system('id')") is None
    assert resolve_math_question("2 + 2 and another unrelated request") is None


def test_master_brain_answers_arithmetic_without_model():
    brain = MasterBrain()
    result = brain.process("2 + 2 कितना होता है?")
    assert result.success
    assert result.message == "उत्तर: 4"
    assert result.metadata["response_source"] == "safe_arithmetic_resolver"


def test_resolves_english_arithmetic_with_output_instruction():
    result = resolve_math_question("What is 2 + 2? Answer with only the number.")
    assert result is not None
    assert result.answer == "उत्तर: 4"
    assert result.expression == "2 + 2"


def test_resolves_hindi_arithmetic_with_output_instruction():
    result = resolve_math_question("2 + 2, केवल संख्या में उत्तर दें।")
    assert result is not None
    assert result.answer == "उत्तर: 4"
