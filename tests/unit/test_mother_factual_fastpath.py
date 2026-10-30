from core.brain.mother_operational_integration import MotherOperationalIntegration
from core.model_gateway.base import ModelGateway
from core.model_gateway.mock_provider import MockModelProvider


def test_curated_fact_fast_path_skips_language_model():
    gateway = ModelGateway()
    gateway.register_provider(MockModelProvider())
    integration = MotherOperationalIntegration(model_gateway=gateway)

    def unexpected_model_call(**kwargs):
        raise AssertionError("curated fact should not invoke the language model")

    integration.model.generate = unexpected_model_call
    result = integration.process_approved_request(
        objective="आसमान नीला क्यों दिखाई देता है?",
        intent="general_request",
    )

    assert result.success is True
    assert result.provider == "curated_local_knowledge:PHYS-SCATTER-001"
    assert "वायुमंडल" in result.response
    assert result.verification_status == "CURATED_KNOWLEDGE"


def test_curated_compound_question_uses_complete_fact_without_model():
    gateway = ModelGateway()
    gateway.register_provider(MockModelProvider())
    integration = MotherOperationalIntegration(model_gateway=gateway)
    result = integration.process_approved_request(
        objective="भारत की राजधानी क्या है और इतिहास भी बताओ?",
        intent="general_request",
    )
    assert result.success is True
    assert result.provider == "curated_local_knowledge:IN-CAPITAL-HISTORY-001"
    assert "नई दिल्ली" in result.response
    assert "1911" in result.response and "1931" in result.response
    assert result.verification_status == "CURATED_KNOWLEDGE"


def test_photosynthesis_curated_fast_path_skips_weak_local_model():
    gateway = ModelGateway()
    gateway.register_provider(MockModelProvider())
    integration = MotherOperationalIntegration(model_gateway=gateway)

    def unexpected_model_call(**kwargs):
        raise AssertionError("curated photosynthesis fact should not invoke the model")

    integration.model.generate = unexpected_model_call
    result = integration.process_approved_request(
        objective="Explain photosynthesis in simple Hindi.",
        intent="explain",
    )
    assert result.success is True
    assert result.provider == "curated_local_knowledge:BIO-PHOTOSYNTHESIS-001"
    assert "कार्बन डाइऑक्साइड" in result.response
    assert "ऑक्सीजन" in result.response
    assert result.verification_status == "CURATED_KNOWLEDGE"
