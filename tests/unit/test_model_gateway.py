from core.model_gateway import (
    ModelGateway,
    ModelRequest,
    MockModelProvider,
)


def main() -> None:
    print("=" * 60)
    print("SAHIBEX MODEL GATEWAY TEST")
    print("=" * 60)

    gateway = ModelGateway()
    provider = MockModelProvider()

    gateway.register_provider(provider)

    assert gateway.providers() == ["mock"]
    print("[PASS] provider registration")

    request = ModelRequest(
        prompt="Explain what SAHIBEX is.",
    )

    response = gateway.generate(
        request,
        provider="mock",
    )

    assert response.success is True
    assert response.provider == "mock"
    assert response.model == "mock-v1"
    assert "SAHIBEX" in response.text
    print("[PASS] model generation")

    empty_response = gateway.generate(
        ModelRequest(prompt=""),
        provider="mock",
    )

    assert empty_response.success is False
    assert empty_response.error == "Prompt cannot be empty."
    print("[PASS] empty prompt rejection")

    try:
        gateway.get_provider("unknown")
        raise AssertionError("Unknown provider was not blocked.")
    except KeyError:
        pass

    print("[PASS] unknown provider blocked")

    print("=" * 60)
    print("SAHIBEX MODEL GATEWAY TEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
