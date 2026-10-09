from core.brain.mother_operational_integration import MotherOperationalIntegration
from core.model_gateway.base import ModelGateway
from core.model_gateway.mock_provider import MockModelProvider


def test_mother_operational_uses_registered_default_provider_when_omitted():
    gateway = ModelGateway()
    gateway.register_provider(MockModelProvider())
    integration = MotherOperationalIntegration(model_gateway=gateway)

    result = integration.process_approved_request(
        objective="SAHIBEX",
        intent="explain",
    )

    assert result.success is False
    assert result.provider == integration.default_provider == "mock"
    assert result.verification_status == "QUALITY_REJECTED"


def test_mother_operational_explicit_provider_still_overrides_default():
    gateway = ModelGateway()
    gateway.register_provider(MockModelProvider())
    integration = MotherOperationalIntegration(model_gateway=gateway)

    result = integration.process_approved_request(
        objective="SAHIBEX",
        intent="explain",
        provider="mock",
    )

    assert result.success is False
    assert result.provider == "mock"
    assert result.verification_status == "QUALITY_REJECTED"
