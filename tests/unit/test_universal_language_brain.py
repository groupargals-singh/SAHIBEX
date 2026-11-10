from __future__ import annotations

import pytest

from core.brain.universal_language_brain import UniversalLanguageBrain
from core.brain.human_interaction import HumanInteractionEngine, InteractionLanguage


def test_universal_language_brain_detects_common_scripts():
    brain = UniversalLanguageBrain()
    cases = [
        ("मुझे जवाब दो", "hi"),
        ("Mujhe jawab do", "hi-Latn"),
        ("SAHIBEX ko Hindi/Hinglish samajhne wala banao", "hi-Latn"),
        ("Hello, what can you do?", "en"),
        ("¿Cómo estás? gracias", "es"),
        ("Bonjour, comment allez vous?", "fr"),
        ("你好，你好吗", "zh"),
        ("こんにちは", "ja"),
        ("안녕하세요", "ko"),
        ("Привет, как дела", "ru"),
        ("مرحبا كيف حالك", "ar"),
        ("Ελλάδα", "el"),
        ("שלום", "he"),
        ("বাংলা ভাষা", "bn"),
        ("தமிழ் மொழி", "ta"),
        ("తెలుగు భాష", "te"),
        ("ภาษาไทย", "th"),
    ]
    for text, expected in cases:
        result = brain.detect(text)
        assert result.language_code == expected, (text, result)
        assert result.confidence > 0


def test_empty_and_non_string_inputs_are_handled_safely():
    brain = UniversalLanguageBrain()
    assert brain.detect("   ").language_code == "und"
    with pytest.raises(TypeError):
        brain.detect(None)  # type: ignore[arg-type]


def test_reply_instruction_requires_matching_detected_language():
    brain = UniversalLanguageBrain()
    instruction = brain.reply_instruction("你好")
    assert "Chinese" in instruction
    assert "Do not translate into English" in instruction


def test_response_language_consistency_rejects_wrong_language():
    brain = UniversalLanguageBrain()
    assert not brain.response_matches_language(
        "मला मदत करा, हे काय आहे?",
        "पानी शरीर के तापमान को नियंत्रित करता है।",
    )
    assert brain.response_matches_language(
        "मला मदत करा, हे काय आहे?",
        "पाणी शरीरासाठी महत्त्वाचे आहे.",
    )
    assert not brain.response_matches_language(
        "SAHIBEX ko Hindi/Hinglish samajhne wala banao",
        "I am unable to create content in Hindi as I do not have access to that capability.",
    )
    # Unknown-language output should not be falsely rejected by a weak heuristic.
    assert brain.response_matches_language("Hello", "xyzzy qwerty")


def test_operational_gate_rejects_model_answer_in_wrong_language(tmp_path):
    from core.brain.mother_operational_integration import MotherOperationalIntegration
    from core.model_gateway.base import ModelGateway, ModelProvider, ModelRequest, ModelResponse
    from core.research.storage import ResearchStorage

    class HindiOnlyProvider(ModelProvider):
        name = "hindi-only-test"

        def generate(self, request: ModelRequest) -> ModelResponse:
            return ModelResponse(
                text="पानी शरीर के तापमान को नियंत्रित करता है।",
                provider=self.name,
                model="fixture",
                success=True,
            )

    gateway = ModelGateway()
    provider = HindiOnlyProvider()
    gateway.register_provider(provider)
    integration = MotherOperationalIntegration(
        storage=ResearchStorage(tmp_path / "language-gate.db"),
        model_gateway=gateway,
    )
    result = integration.process_approved_request(
        objective="मला मदत करा, हे काय आहे?",
        intent="explain",
        provider=provider.name,
    )
    assert result.success is False
    assert result.verification_status == "QUALITY_REJECTED"
    assert "विश्वासार्ह" in result.response


def test_human_interaction_preserves_legacy_language_contract_and_exposes_universal_code():
    engine = HumanInteractionEngine()
    assert engine.detect_language("Hello SAHIBEX") is InteractionLanguage.ENGLISH
    assert engine.detect_language("मुझे यह समझाओ") is InteractionLanguage.HINDI
    assert engine.detect_language("Mujhe ye batao kaise karna hai") is InteractionLanguage.HINGLISH
    assert engine.assess_language("你好").language_code == "zh"
    assessment = engine.assess("Bonjour, comment allez vous?")
    assert assessment.language_code == "fr"


def test_operational_model_receives_detected_language_instruction():
    from core.brain.operational_model import OperationalModelIntegration
    from core.model_gateway.base import ModelGateway, ModelProvider, ModelRequest, ModelResponse

    class CapturingProvider(ModelProvider):
        name = "capture-language"
        request = None

        def generate(self, request: ModelRequest) -> ModelResponse:
            self.request = request
            return ModelResponse(
                text="你好。", provider=self.name, model="test-model", success=True
            )

    gateway = ModelGateway()
    provider = CapturingProvider()
    gateway.register_provider(provider)
    integration = OperationalModelIntegration(gateway)
    result = integration.generate(
        objective="你好，你好吗", intent="explain", prompt="Answer this question", provider=provider.name
    )
    assert result.success
    assert provider.request is not None
    assert "Chinese" in provider.request.system_prompt
    assert "Do not translate into English" in provider.request.system_prompt
    assert "do not falsely claim that Hindi support is unavailable" in provider.request.system_prompt


def test_indian_languages_and_shared_devanagari_languages_are_recognized():
    brain = UniversalLanguageBrain()
    cases = [
        ("मुझे जवाब दो", "hi"),
        ("मला मदत करा, हे काय आहे?", "mr"),
        ("मलाई मद्दत गर्नुहोस्", "ne"),
        ("अहं संस्कृतं पठामि", "sa"),
        ("আমি ভালো আছি", "bn"),
        ("অসমীয়া ভাষা", "as"),
        ("ਸਤ ਸ੍ਰੀ ਅਕਾਲ, ਤੁਸੀਂ ਕਿਵੇਂ ਹੋ?", "pa"),
        ("ગુજરાતી ભાષા", "gu"),
        ("ଓଡ଼ିଆ ଭାଷા", "or"),
        ("தமிழ் மொழி", "ta"),
        ("తెలుగు భాష", "te"),
        ("ಕನ್ನಡ ಭಾಷೆ", "kn"),
        ("മലയാളം ഭാഷ", "ml"),
        ("ꯃꯩꯇꯩ ꯂꯣꯟ", "mni"),
        ("ᱥᱟᱱᱛᱟᱲᱤ", "sat"),
        ("मैथिली भाषा अछि", "mai"),
        ("डोगरी भाषा", "doi"),
        ("कोंकणी भाषा", "kok"),
        ("बड़ो राव", "brx"),
        ("سنڌي ٻولي", "sd"),
        ("کٲشُر زبان", "ks"),
        ("آپ کیسے ہیں؟", "ur"),
        ("سلام، حال شما چطور است؟", "fa"),
        ("مرحبا كيف حالك", "ar"),
    ]
    for text, expected in cases:
        result = brain.detect(text)
        assert result.language_code == expected, (text, result)
        assert result.confidence > 0


def test_latin_world_languages_and_cjk_scripts_are_recognized():
    brain = UniversalLanguageBrain()
    cases = [
        ("Hello, what can you do?", "en"),
        ("¿Cómo estás? gracias", "es"),
        ("Bonjour, comment allez vous?", "fr"),
        ("Hallo, wie geht es dir?", "de"),
        ("Ciao, come stai?", "it"),
        ("Terima kasih, apa kabar?", "id"),
        ("こんにちは", "ja"),
        ("你好，你好吗", "zh"),
        ("안녕하세요", "ko"),
        ("Привет, как дела", "ru"),
        ("Ελλάδα", "el"),
        ("שלום", "he"),
    ]
    for text, expected in cases:
        result = brain.detect(text)
        assert result.language_code == expected, (text, result)


def test_indian_scheduled_languages_and_script_variants():
    brain = UniversalLanguageBrain()
    cases = [
        ("मुझे जवाब दो", "hi"),
        ("मला मदत करा, हे काय आहे?", "mr"),
        ("नेपाली भाषा", "ne"),
        ("अहं संस्कृतं पठामि", "sa"),
        ("अहाँ केना छी, मैथिली भाषा", "mai"),
        ("नोंथां बड़ो राव", "brx"),
        ("तुस थुआढ़े केह् करदे ओ", "doi"),
        ("हांव तुका कशें आसा, कोंकणी", "kok"),
        ("कश्मीरी भाषा", "ks"),
        ("असां सिंधी आहियूं", "sd"),
        ("আমি বাংলা বলি", "bn"),
        ("অসমীয়া ভাষা", "as"),
        ("ਸਤ ਸ੍ਰੀ ਅਕਾਲ, ਤੁਸੀਂ ਕਿਵੇਂ ਹੋ?", "pa"),
        ("ગુજરાતી ભાષા", "gu"),
        ("ଓଡ଼ିଆ ଭାଷା", "or"),
        ("தமிழ் மொழி", "ta"),
        ("తెలుగు భాష", "te"),
        ("ಕನ್ನಡ ಭಾಷೆ", "kn"),
        ("മലയാളം ഭാഷ", "ml"),
        ("ꯃꯩꯇꯩ ꯂꯣꯟ", "mni"),
        ("ᱥᱟᱱᱛᱟᱲᱤ", "sat"),
        ("آپ کیسے ہیں؟", "ur"),
    ]
    for text, expected in cases:
        result = brain.detect(text)
        assert result.language_code == expected, (text, result)


def test_romanized_indian_languages_are_supported():
    brain = UniversalLanguageBrain()
    cases = [
        ("Mala madat kara, krupaya", "mr-Latn"),
        ("Tapai lai kasto chha", "ne-Latn"),
        ("Tusi kiven ho, sat sri akaal", "pa-Latn"),
        ("Vanakkam, nandri", "ta-Latn"),
        ("Namaskaram, meeru ela unnaru", "te-Latn"),
        ("Namaskara, neevu hegiddira", "kn-Latn"),
        ("Namaskaram, ningal sugamano", "ml-Latn"),
        ("Kem cho, maja ma", "gu-Latn"),
    ]
    for text, expected in cases:
        result = brain.detect(text)
        assert result.language_code == expected, (text, result)
        assert result.language_name


def test_all_scheduled_indian_languages_have_regression_examples():
    brain = UniversalLanguageBrain()
    # Representative short phrases for India's 22 scheduled languages.
    cases = [
        ("अहं संस्कृतं पठामि", "sa"),
        ("অসমীয়া ভাষা", "as"),
        ("আমি ভালো আছি", "bn"),
        ("बड़ो राव", "brx"),
        ("तुस थुआढ़े केह्", "doi"),
        ("ગુજરાતી ભાષા", "gu"),
        ("मुझे जवाब दो", "hi"),
        ("ಕನ್ನಡ ಭಾಷೆ", "kn"),
        ("کٲشُر زبان", "ks"),
        ("हांव आमी कशें", "kok"),
        ("अहाँ केना छी", "mai"),
        ("മലയാളം ഭാഷ", "ml"),
        ("ꯃꯩꯇꯩ ꯂꯣꯟ", "mni"),
        ("मला मदत करा, हे काय आहे?", "mr"),
        ("मलाई मद्दत गर्नुहोस्", "ne"),
        ("ଓଡ଼ିଆ ଭାଷા", "or"),
        ("ਸਤ ਸ੍ਰੀ ਅਕਾਲ, ਤੁਸੀਂ ਕਿਵੇਂ ਹੋ?", "pa"),
        ("ᱥᱟᱱᱛᱟᱲᱤ", "sat"),
        ("سنڌي ٻولي", "sd"),
        ("தமிழ் மொழி", "ta"),
        ("తెలుగు భాష", "te"),
        ("آپ کیسے ہیں؟", "ur"),
    ]
    for phrase, expected in cases:
        assessment = brain.detect(phrase)
        assert assessment.language_code == expected, (phrase, assessment)
        assert assessment.confidence > 0


def test_indian_regional_and_romanized_languages():
    brain = UniversalLanguageBrain()
    cases = [
        ("हमार घर कहाँ बा?", "bho"),
        ("मोला बतावव, तोर नाव का हे?", "hne"),
        ("म्हाने बताओ, थाने केड़ो चाहिये?", "raj"),
        ("तन्नै के हाल सै, मन्नै बता", "bgc"),
        ("Mujhe batao kya karna hai", "hi-Latn"),
        ("Mala madat kara", "mr-Latn"),
        ("Tapai lai kasto chha", "ne-Latn"),
        ("Tusi kiven ho", "pa-Latn"),
        ("Ami bhalo achhi", "bn-Latn"),
        ("Vanakkam nandri", "ta-Latn"),
        ("Namaskaram meeru", "te-Latn"),
        ("Namaskara neevu", "kn-Latn"),
        ("Nanni ningal", "ml-Latn"),
        ("Kem cho tame", "gu-Latn"),
        ("Namaskar odia", "or-Latn"),
        ("Konknni mhaka kite sang", "kok-Latn"),
        ("Moi bhal asu, kenekoi asa", "as-Latn"),
        ("Mor naam sahibex havay", "hne-Latn"),
        ("Khamma ghani, mhane batao", "raj-Latn"),
        ("Tanne ke haal se", "bgc-Latn"),
    ]
    for phrase, expected in cases:
        assessment = brain.detect(phrase)
        assert assessment.language_code == expected, (phrase, assessment)


def test_quality_rejection_fallback_matches_user_language():
    from core.brain.mother_operational_integration import MotherOperationalIntegration

    cases = [
        ("मला मदत करा", "mr", "विश्वासार्ह"),
        ("கணினி என்றால் என்ன", "ta", "நம்பகமான"),
        ("آپ کیسے ہیں؟", "ur", "قابلِ اعتماد"),
        ("你好", "zh", "可靠"),
        ("Hello, help me", "en", "reliable"),
        ("Mala madat kara", "mr-Latn", "विश्वासार्ह"),
        ("हमार घर कहाँ बा?", "bho", "भरोसेमंद"),
    ]
    for question, code, expected_text in cases:
        message = MotherOperationalIntegration._quality_rejection_message(question)
        assert expected_text in message
        assert message.strip()
        assert UniversalLanguageBrain().detect(question).language_code == code


def test_hinglish_research_request_is_not_misclassified_as_english():
    assessment = UniversalLanguageBrain().detect(
        "Is topic par latest jankari khojo"
    )
    assert assessment.language_code == "hi-Latn"
