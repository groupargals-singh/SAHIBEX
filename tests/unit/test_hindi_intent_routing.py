from core.brain.intent import IntentEngine
from core.brain.human_interaction import HumanInteractionEngine, InteractionLanguage


def test_hindi_current_updates_route_to_research():
    result = IntentEngine().detect("आज AI सुरक्षा में क्या नया है?")
    assert result.intent == "search"


def test_hindi_latest_information_routes_to_research():
    result = IntentEngine().detect("AI सुरक्षा की नवीनतम जानकारी बताओ")
    assert result.intent == "search"


def test_regular_explanation_is_not_research():
    result = IntentEngine().detect("आसमान नीला क्यों दिखाई देता है?")
    assert result.intent == "explain"

def test_hindi_weather_question_routes_to_research():
    result = IntentEngine().detect(
        "भारत के मौसम पर विस्तार से बताओ"
    )
    assert result.intent == "search"


def test_english_weather_question_routes_to_research():
    result = IntentEngine().detect(
        "Tell me the weather forecast for India"
    )
    assert result.intent == "search"


def test_general_explanation_still_routes_to_explain():
    result = IntentEngine().detect(
        "मौसम कैसे बनता है, समझाओ"
    )
    assert result.intent == "explain"


def test_hinglish_current_research_routes_to_search():
    result = IntentEngine().detect(
        "Aaj AI safety me latest update batao"
    )
    assert result.intent == "search"


def test_hinglish_learning_request_routes_to_learn():
    result = IntentEngine().detect("Mujhe Python sikhao")
    assert result.intent == "learn"


def test_hindi_code_request_routes_to_code():
    result = IntentEngine().detect("Python ka code likho")
    assert result.intent == "code"


def test_devanagari_code_request_routes_to_code():
    result = IntentEngine().detect("कोड लिखो")
    assert result.intent == "code"


def test_hinglish_file_request_routes_to_file_operation():
    result = IntentEngine().detect("file kholo")
    assert result.intent == "file_operation"


def test_devanagari_file_request_routes_to_file_operation():
    result = IntentEngine().detect("फाइल खोलो")
    assert result.intent == "file_operation"


def test_hinglish_explanation_routes_to_explain():
    result = IntentEngine().detect("Mausam kaise banta hai?")
    assert result.intent == "explain"


def test_hindi_creation_request_routes_to_create():
    result = IntentEngine().detect("Mere liye ek poster banao")
    assert result.intent == "create"


def test_empty_input_stays_empty():
    result = IntentEngine().detect("   ")
    assert result.intent == "empty"


def test_hinglish_human_interaction_keeps_research_route():
    result = HumanInteractionEngine().assess(
        "Aaj AI safety me latest update batao"
    )
    assert result.language == InteractionLanguage.HINGLISH
    assert result.intent is not None
    assert result.intent.intent == "search"


def test_hindi_human_interaction_keeps_explanation_route():
    result = HumanInteractionEngine().assess("आसमान नीला क्यों दिखाई देता है?")
    assert result.language == InteractionLanguage.HINDI
    assert result.intent is not None
    assert result.intent.intent == "explain"


def test_explicit_search_for_python_language_is_not_misrouted_to_code():
    result = IntentEngine().detect("Search for an overview of the Python language.")
    assert result.intent == "search"


def test_explicit_search_for_programming_topic_is_not_misrouted_to_code():
    result = IntentEngine().detect("Search for a high-level programming language overview.")
    assert result.intent == "search"


def test_explicit_python_code_creation_still_routes_to_code():
    result = IntentEngine().detect("Write a Python program that adds two numbers.")
    assert result.intent == "code"


def test_hindi_greeting_with_short_answer_instruction_uses_safe_local_reply():
    from core.brain.conversation_resolver import resolve_local_conversation

    result = resolve_local_conversation(
        "नमस्ते साहिबेक्स, एक छोटे वाक्य में हिंदी में जवाब दो।"
    )
    assert result is not None
    assert result.response_id == "CONV-GREETING-001"
    assert "नमस्ते" in result.answer


def test_greeting_with_substantive_question_is_not_swallowed_by_greeting_fast_path():
    from core.brain.conversation_resolver import resolve_local_conversation

    assert resolve_local_conversation("नमस्ते, AI सुरक्षा क्या है?") is None
