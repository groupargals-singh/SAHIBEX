from core.brain.operational_model import (
    OperationalModelIntegration,
    OperationalModelResult,
)
from core.model_gateway.base import ModelGateway
from core.model_gateway.mock_provider import MockModelProvider


def main() -> None:
    gateway = ModelGateway()
    gateway.register_provider(MockModelProvider())

    integration = OperationalModelIntegration(gateway)

    result = integration.generate(
        objective="Research AI security",
        intent="RESEARCH",
        prompt="Explain AI security in simple terms.",
        provider="mock",
    )

    assert isinstance(result, OperationalModelResult)
    assert result.success is True
    assert result.objective == "Research AI security"
    assert result.intent == "research"
    assert result.provider == "mock"
    assert result.model == "mock-v1"
    assert result.response_text
    assert result.integration_id

    try:
        integration.generate(
            objective="Research",
            intent="research",
            prompt="",
            provider="mock",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Empty prompt must be rejected")

    try:
        integration.generate(
            objective="Research",
            intent="research",
            prompt="Test",
            provider="unknown-provider",
        )
    except ValueError:
        pass
    except KeyError:
        pass
    else:
        raise AssertionError("Unknown provider must be rejected")

    forbidden_methods = (
        "grant_permission",
        "execute_action",
        "override_constitution",
    )

    for method_name in forbidden_methods:
        assert not hasattr(integration, method_name), (
            f"Forbidden method exists: {method_name}"
        )

    print("SAHIBEX 6O-2 MODEL GATEWAY INTEGRATION TEST: PASS")


if __name__ == "__main__":
    main()
