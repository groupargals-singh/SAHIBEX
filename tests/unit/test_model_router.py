from core.model_gateway import (
    ModelGateway,
    ModelRequest,
    MockModelProvider,
)

from core.model_gateway.router import ModelRouter


def main() -> None:
    print("=" * 60)
    print("SAHIBEX MODEL ROUTER TEST")
    print("=" * 60)

    gateway = ModelGateway()
    gateway.register_provider(MockModelProvider())

    router = ModelRouter(
        gateway,
        default_provider="mock",
    )

    request = ModelRequest(
        prompt="Explain SAHIBEX.",
    )

    decision = router.decide(request)

    assert decision.provider == "mock"
    assert decision.metadata["selection"] == "default"
    print("[PASS] default provider routing")

    response = router.generate(request)

    assert response.success is True
    assert response.provider == "mock"
    assert "SAHIBEX" in response.text
    print("[PASS] routed model generation")

    explicit_decision = router.decide(
        request,
        preferred_provider="mock",
    )

    assert explicit_decision.provider == "mock"
    assert explicit_decision.metadata["selection"] == "explicit"
    print("[PASS] explicit provider routing")

    try:
        router.decide(
            request,
            preferred_provider="unknown",
        )
        raise AssertionError(
            "Unknown provider was not rejected."
        )
    except KeyError:
        pass

    print("[PASS] unknown provider rejected")

    broken_gateway = ModelGateway()

    broken_router = ModelRouter(
        broken_gateway,
        default_provider="mock",
    )

    try:
        broken_router.decide(request)
        raise AssertionError(
            "Missing default provider was not rejected."
        )
    except RuntimeError:
        pass

    print("[PASS] missing default provider rejected")

    print("=" * 60)
    print("SAHIBEX MODEL ROUTER TEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
