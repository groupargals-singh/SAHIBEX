from core.brain.intent import IntentEngine


def test_hindi_current_updates_route_to_research():
    result = IntentEngine().detect("आज AI सुरक्षा में क्या नया है?")
    assert result.intent == "search"


def test_hindi_latest_information_routes_to_research():
    result = IntentEngine().detect("AI सुरक्षा की नवीनतम जानकारी बताओ")
    assert result.intent == "search"


def test_regular_explanation_is_not_research():
    result = IntentEngine().detect("आसमान नीला क्यों दिखाई देता है?")
    assert result.intent == "explain"
