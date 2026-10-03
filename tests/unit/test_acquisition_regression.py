from __future__ import annotations

import tempfile
from pathlib import Path

from core.policies.approval import PermissionEngine

from core.research.acquisition import (
    AcquisitionRequest,
    AcquisitionResult,
    AcquiredSource,
    ResearchAcquisitionEngine,
    ResearchAcquisitionProvider,
)

from core.research.acquisition_permission import (
    AcquisitionPermissionGate,
)

from core.research.acquisition_validator import (
    AcquisitionSafetyValidator,
)

from core.research.multi_source import (
    ResearchMultiSourceAcquisition,
)

from core.research.provider_router import (
    ResearchProviderRouter,
)


class FakeNetworkProvider(
    ResearchAcquisitionProvider
):
    provider_name = "regression_network"
    requires_network = True

    calls = 0

    def acquire(
        self,
        request: AcquisitionRequest,
    ) -> AcquisitionResult:
        type(self).calls += 1

        source = AcquiredSource(
            source_id="regression-network-source",
            title="Regression Network Source",
            source_type="web",
            locator="https://example.com/regression",
            content="network regression content",
        )

        return AcquisitionResult(
            query=request.query,
            sources=[source],
            completed=True,
            status="completed",
        )


class RegressionSearchProvider(
    ResearchAcquisitionProvider
):
    provider_name = "search"
    requires_network = True

    def acquire(
        self,
        request: AcquisitionRequest,
    ) -> AcquisitionResult:
        return AcquisitionResult(
            query=request.query,
            sources=[],
            completed=True,
            status="completed",
        )


class RegressionDocumentProvider(
    ResearchAcquisitionProvider
):
    provider_name = "document"
    requires_network = False

    def acquire(
        self,
        request: AcquisitionRequest,
    ) -> AcquisitionResult:
        return AcquisitionResult(
            query=request.query,
            sources=[
                AcquiredSource(
                    source_id="multi-source-1",
                    title="Multi Source Regression",
                    source_type="document",
                    locator="document://multi-source-1",
                    content="same source",
                )
            ],
            completed=True,
            status="completed",
        )


def check_acquisition_contract():
    request = AcquisitionRequest(
        query="SAHIBEX acquisition regression"
    )

    assert request.query == (
        "SAHIBEX acquisition regression"
    )

    assert request.max_sources == 10

    source = AcquiredSource(
        source_id="source-1",
        title="Test Source",
        source_type="mock",
        locator="mock://source-1",
        content="test",
    )

    result = AcquisitionResult(
        query=request.query,
        sources=[source],
        completed=True,
        status="completed",
    )

    assert result.query == request.query
    assert result.sources[0].source_id == "source-1"
    assert result.completed is True
    assert result.status == "completed"

    print("[PASS] acquisition contract")


def check_validator():
    validator = AcquisitionSafetyValidator()

    source = AcquiredSource(
        source_id="validator-source",
        title="Validator Source",
        source_type="mock",
        locator="mock://validator",
        content="validator test",
    )

    validator.validate(source)

    print("[PASS] acquisition validator")


def check_permission_boundary():
    FakeNetworkProvider.calls = 0

    engine = ResearchAcquisitionEngine(
        providers=[
            FakeNetworkProvider(),
        ]
    )

    permission_engine = PermissionEngine()

    gate = AcquisitionPermissionGate(
        permission_engine
    )

    request = AcquisitionRequest(
        query="network permission regression"
    )

    blocked = gate.check_network_access(
        confirmation=False
    )

    assert blocked.allowed is False
    assert FakeNetworkProvider.calls == 0

    allowed = gate.check_network_access(
        confirmation=True
    )

    assert allowed.allowed is True

    result = engine.acquire(
        request,
        provider_name="regression_network",
    )

    assert result.completed is True
    assert result.status == "completed"
    assert FakeNetworkProvider.calls == 1

    print("[PASS] network permission boundary")


def check_router():
    engine = ResearchAcquisitionEngine(
        providers=[
            RegressionSearchProvider(),
        ]
    )

    router = ResearchProviderRouter(
        engine
    )

    request = AcquisitionRequest(
        query="router regression",
        source_type="search",
    )

    route = router.route(request)

    assert route.provider_name == "search"
    assert isinstance(route.reason, str)
    assert route.reason.strip()

    print("[PASS] provider router")


def check_multi_source():
    engine = ResearchAcquisitionEngine(
        providers=[
            RegressionDocumentProvider(),
        ]
    )

    coordinator = ResearchMultiSourceAcquisition(
        acquisition_engine=engine,
    )

    request = AcquisitionRequest(
        query="multi source regression",
        source_type="document",
    )

    result = coordinator.acquire(
        [request],
        confirmation=False,
    )

    assert result.query == (
        "multi source regression"
    )

    assert result.completed is True
    assert result.status == "completed"

    assert len(result.provider_results) == 1
    assert (
        result.provider_results[0].provider_name
        == "document"
    )

    assert len(result.sources) == 1

    assert (
        result.sources[0].source_id
        == "multi-source-1"
    )

    assert result.failed_providers == []

    print("[PASS] multi-source acquisition")


def check_document_safety_contract():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        document = root / "regression.txt"

        document.write_text(
            "SAHIBEX document regression",
            encoding="utf-8",
        )

        assert document.exists()

        content = document.read_text(
            encoding="utf-8"
        )

        assert content == (
            "SAHIBEX document regression"
        )

    print("[PASS] local document regression fixture")


def main():
    print("SAHIBEX ACQUISITION REGRESSION")
    print("=" * 40)

    check_acquisition_contract()
    check_validator()
    check_permission_boundary()
    check_router()
    check_multi_source()
    check_document_safety_contract()

    print("=" * 40)
    print("SAHIBEX ACQUISITION REGRESSION: PASS")


if __name__ == "__main__":
    main()
