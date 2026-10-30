from __future__ import annotations

from core.brain.conversation_resolver import resolve_local_conversation
from core.brain.mother_operational_integration import MotherOperationalIntegration
from core.brain.operational_model import OperationalModelIntegration
from core.model_gateway.base import ModelGateway, ModelProvider, ModelRequest, ModelResponse


def test_hindi_greeting_uses_feminine_self_reference():
    result = resolve_local_conversation("नमस्ते")
    assert result is not None
    assert "मदद करूँगी" in result.answer
    assert "करूँगा" not in result.answer


def test_capability_reply_uses_feminine_self_reference():
    result = resolve_local_conversation("तुम क्या कर सकते हो")
    assert result is not None
    assert "आप मुझसे टेक्स्ट में सवाल पूछें" in result.answer
    assert "कर सकता हूँ" not in result.answer
    assert "करूँगा" not in result.answer


def test_operational_greetings_use_feminine_hindi_and_hinglish():
    assert "कर सकती हूँ" in MotherOperationalIntegration._greeting_response("नमस्ते")
    assert "kar sakti hoon" in MotherOperationalIntegration._greeting_response("namaste")


def test_uncertainty_messages_use_feminine_first_person():
    integration = object.__new__(MotherOperationalIntegration)
    hindi = integration._uncertainty_message("इस सवाल का जवाब क्या है?")
    hinglish = integration._uncertainty_message("Iska jawab kya hai?")
    assert "नहीं करूँगी" in hindi
    assert "nahi karungi" in hinglish



class _CaptureProvider(ModelProvider):
    name = "capture"

    def __init__(self):
        self.request = None

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.request = request
        return ModelResponse(
            text="Main aapki madad kar sakti hoon.",
            provider=self.name,
            model="capture-test",
            success=True,
        )


def test_model_system_prompt_requires_feminine_persona_in_hindi_hinglish_and_english():
    gateway = ModelGateway()
    provider = _CaptureProvider()
    gateway.register_provider(provider)
    OperationalModelIntegration(gateway).generate(
        objective="Namaste",
        intent="general_request",
        prompt="Namaste",
        provider="capture",
    )
    assert provider.request is not None
    prompt = provider.request.system_prompt
    assert "female-presenting AI assistant" in prompt
    assert "kar sakti hoon" in prompt
    assert "bataungi" in prompt
    assert "without gender stereotypes" in prompt


def test_identity_question_works_without_local_model_and_uses_feminine_hinglish():
    integration = MotherOperationalIntegration()
    result = integration.process_approved_request(
        objective="SAHIBEX, tum kaun ho? Apni pehchan ek female AI assistant ke roop mein batao.",
        intent="general_request",
    )
    assert result.success is True
    assert result.provider == "deterministic_identity"
    assert result.diagnostics["llm_required"] is False
    assert "Main SAHIBEX hoon" in result.response
    assert "madad kar sakti hoon" in result.response
    assert "bataungi" in result.response
    assert "kar sakta hoon" not in result.response
