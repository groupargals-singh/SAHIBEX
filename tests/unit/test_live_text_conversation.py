from core.brain.master_brain import MasterBrain


def test_greeting_works_without_model_quality_gate():
    result = MasterBrain().process("नमस्ते")
    assert result.success is True
    assert "नमस्ते" in result.message
    assert result.metadata["response_source"] == "deterministic_text_conversation"
    assert result.verification_status == "STRUCTURALLY_VALID"
    assert result.plan_created is False


def test_roman_hindi_greeting_uses_deterministic_text_path():
    result = MasterBrain().process("Namaste Sahibex")
    assert result.success is True
    assert result.metadata["response_source"] == "deterministic_text_conversation"
    assert result.plan_created is False
    assert result.task_count == 0


def test_capabilities_are_truthful_about_text_only_scope():
    result = MasterBrain().process("तुम क्या कर सकते हो?")
    assert result.success is True
    assert "टेक्स्ट" in result.message
    assert "फोटो" in result.message
    assert "अनुमति" in result.message


def test_status_is_available_through_master_brain():
    result = MasterBrain().process("status")
    assert result.success is True
    assert result.intent == "system_status"
    assert result.metadata["response_id"] == "CONV-STATUS-001"


def test_unrecognized_text_still_uses_ai_path():
    from core.brain.conversation_resolver import resolve_local_conversation
    assert resolve_local_conversation("भारत के मौसम पर विस्तार से बताओ") is None


def main():
    test_greeting_works_without_model_quality_gate()
    test_capabilities_are_truthful_about_text_only_scope()
    test_status_is_available_through_master_brain()
    test_unrecognized_text_still_uses_ai_path()
    print("SAHIBEX LIVE TEXT CONVERSATION TEST: PASS")


if __name__ == "__main__":
    main()
