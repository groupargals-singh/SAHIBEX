from core.research.acquisition import (
    AcquisitionRequest,
    AcquisitionResult,
    AcquiredSource,
    ResearchAcquisitionEngine,
    ResearchAcquisitionProvider,
)


class MockResearchProvider(ResearchAcquisitionProvider):
    provider_name = "mock"

    def acquire(self, request):
        source = AcquiredSource(
            source_id="source-001",
            title="Mock Research Source",
            source_type="mock",
            locator="mock://source-001",
            publisher="SAHIBEX Test",
            content="This is mock research content.",
        )

        return AcquisitionResult(
            query=request.query,
            sources=[source],
            completed=True,
            status="SUCCESS",
        )


class SecondMockProvider(ResearchAcquisitionProvider):
    provider_name = "second"

    def acquire(self, request):
        return AcquisitionResult(
            query=request.query,
            sources=[],
            completed=True,
            status="EMPTY",
        )


class InvalidResultProvider(ResearchAcquisitionProvider):
    provider_name = "invalid"

    def acquire(self, request):
        return "invalid-result"


class MismatchedResultProvider(ResearchAcquisitionProvider):
    provider_name = "mismatch"

    def acquire(self, request):
        return AcquisitionResult(
            query="different-query",
            sources=[],
            completed=True,
            status="SUCCESS",
        )


def expect_error(function, expected_type):
    try:
        function()
    except expected_type:
        return True

    return False


def main():
    print("SAHIBEX RESEARCH ACQUISITION TEST")

    # ---------------------------------------------------------
    # Request validation
    # ---------------------------------------------------------

    request = AcquisitionRequest(
        query="AI security research",
        max_sources=5,
    )

    assert request.query == "AI security research"
    assert request.max_sources == 5
    print("[PASS] acquisition request validation")

    assert expect_error(
        lambda: AcquisitionRequest(""),
        ValueError,
    )
    print("[PASS] empty query protection")

    assert expect_error(
        lambda: AcquisitionRequest(
            "test",
            max_sources=0,
        ),
        ValueError,
    )
    print("[PASS] invalid max_sources protection")

    assert expect_error(
        lambda: AcquisitionRequest(
            "test",
            max_sources=-1,
        ),
        ValueError,
    )
    print("[PASS] negative max_sources protection")

    # ---------------------------------------------------------
    # Source validation
    # ---------------------------------------------------------

    source = AcquiredSource(
        source_id="source-test",
        title="Test Source",
        source_type="mock",
        locator="mock://test",
        content="test content",
    )

    assert source.source_id == "source-test"
    assert source.content == "test content"
    print("[PASS] acquired source validation")

    assert expect_error(
        lambda: AcquiredSource(
            source_id="",
            title="Test",
            source_type="mock",
            locator="mock://test",
        ),
        ValueError,
    )
    print("[PASS] invalid source ID protection")

    # ---------------------------------------------------------
    # Engine registration
    # ---------------------------------------------------------

    engine = ResearchAcquisitionEngine()

    engine.register_provider(
        MockResearchProvider()
    )

    assert engine.providers() == ["mock"]
    print("[PASS] provider registration")

    assert engine.get_provider("mock").provider_name == "mock"
    print("[PASS] provider lookup")

    # ---------------------------------------------------------
    # Duplicate provider protection
    # ---------------------------------------------------------

    assert expect_error(
        lambda: engine.register_provider(
            MockResearchProvider()
        ),
        ValueError,
    )
    print("[PASS] duplicate provider protection")

    # ---------------------------------------------------------
    # Unknown provider protection
    # ---------------------------------------------------------

    assert expect_error(
        lambda: engine.get_provider("unknown"),
        KeyError,
    )
    print("[PASS] unknown provider protection")

    # ---------------------------------------------------------
    # Acquisition
    # ---------------------------------------------------------

    result = engine.acquire(
        request,
        "mock",
    )

    assert isinstance(
        result,
        AcquisitionResult,
    )

    assert result.query == request.query
    assert result.completed is True
    assert result.status == "SUCCESS"
    assert len(result.sources) == 1
    assert result.sources[0].source_id == "source-001"

    print("[PASS] provider acquisition")
    print("[PASS] acquisition result validation")
    print("[PASS] acquired source returned")

    # ---------------------------------------------------------
    # Multiple providers
    # ---------------------------------------------------------

    engine.register_provider(
        SecondMockProvider()
    )

    assert engine.providers() == [
        "mock",
        "second",
    ]

    second_result = engine.acquire(
        request,
        "second",
    )

    assert second_result.status == "EMPTY"
    assert second_result.sources == []

    print("[PASS] multiple provider support")

    # ---------------------------------------------------------
    # Invalid provider result protection
    # ---------------------------------------------------------

    engine.register_provider(
        InvalidResultProvider()
    )

    assert expect_error(
        lambda: engine.acquire(
            request,
            "invalid",
        ),
        TypeError,
    )

    print("[PASS] invalid provider result protection")

    # ---------------------------------------------------------
    # Mismatched query protection
    # ---------------------------------------------------------

    engine.register_provider(
        MismatchedResultProvider()
    )

    assert expect_error(
        lambda: engine.acquire(
            request,
            "mismatch",
        ),
        ValueError,
    )

    print("[PASS] mismatched query protection")

    # ---------------------------------------------------------
    # Invalid engine request
    # ---------------------------------------------------------

    assert expect_error(
        lambda: engine.acquire(
            "not-a-request",
            "mock",
        ),
        TypeError,
    )

    print("[PASS] invalid acquisition request protection")

    # ---------------------------------------------------------
    # Invalid provider registration
    # ---------------------------------------------------------

    assert expect_error(
        lambda: engine.register_provider(
            object()
        ),
        TypeError,
    )

    print("[PASS] invalid provider registration protection")

    print("SAHIBEX RESEARCH ACQUISITION TEST: PASS")


if __name__ == "__main__":
    main()
