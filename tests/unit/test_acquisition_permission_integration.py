from pathlib import Path
import tempfile

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

from core.research.acquisition_pipeline import (
    ResearchAcquisitionPipeline,
)

from core.policies.approval import (
    PermissionEngine,
)


class OfflineProvider(ResearchAcquisitionProvider):
    provider_name = "offline_test"
    requires_network = False

    def __init__(self):
        self.calls = 0

    def acquire(
        self,
        request: AcquisitionRequest,
    ) -> AcquisitionResult:
        self.calls += 1

        source = AcquiredSource(
            source_id="offline_001",
            title="Offline Test Source",
            source_type="mock",
            locator="mock://offline_001",
            content="Offline research test content.",
            metadata={
                "reliability": 0.9,
            },
        )

        return AcquisitionResult(
            query=request.query,
            sources=[source],
            completed=True,
            status="completed",
        )


class NetworkProvider(ResearchAcquisitionProvider):
    provider_name = "network_test"
    requires_network = True

    def __init__(self):
        self.calls = 0

    def acquire(
        self,
        request: AcquisitionRequest,
    ) -> AcquisitionResult:
        self.calls += 1

        source = AcquiredSource(
            source_id="network_001",
            title="Network Test Source",
            source_type="web",
            locator="https://example.com/test",
            content="Network research test content.",
            metadata={
                "reliability": 0.9,
            },
        )

        return AcquisitionResult(
            query=request.query,
            sources=[source],
            completed=True,
            status="completed",
        )


def main():
    print(
        "SAHIBEX ACQUISITION PERMISSION INTEGRATION TEST"
    )

    offline_provider = OfflineProvider()
    network_provider = NetworkProvider()

    engine = ResearchAcquisitionEngine(
        providers=[
            offline_provider,
            network_provider,
        ]
    )

    permission_engine = PermissionEngine()

    permission_gate = AcquisitionPermissionGate(
        permission_engine
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        database_path = Path(temp_dir) / "research.db"

        pipeline = ResearchAcquisitionPipeline(
            database_path=database_path,
            acquisition_engine=engine,
            permission_gate=permission_gate,
        )

        request = AcquisitionRequest(
            query="test research"
        )

        # -----------------------------------------------------
        # 1. Offline provider must work without permission.
        # -----------------------------------------------------

        result = pipeline.acquire_and_ingest(
            request,
            provider_name="offline_test",
        )

        assert result.stored_count == 1
        assert offline_provider.calls == 1

        print(
            "[PASS] non-network provider works without confirmation"
        )

        # -----------------------------------------------------
        # 2. Network provider must be blocked.
        # -----------------------------------------------------

        blocked = False

        try:
            pipeline.acquire_and_ingest(
                request,
                provider_name="network_test",
            )
        except PermissionError:
            blocked = True

        assert blocked is True

        # Most important security assertion:
        # provider.acquire() must NEVER have been called.
        assert network_provider.calls == 0

        print(
            "[PASS] network provider blocked without confirmation"
        )

        print(
            "[PASS] blocked network provider was never executed"
        )

        # -----------------------------------------------------
        # 3. Permission check must report confirmation required.
        # -----------------------------------------------------

        permission = pipeline.check_network_permission(
            "network_test"
        )

        assert permission["requires_network"] is True
        assert permission["allowed"] is False
        assert permission["requires_confirmation"] is True
        assert permission["risk"] == "medium"

        print(
            "[PASS] network permission reports confirmation required"
        )

        # -----------------------------------------------------
        # 4. Explicit confirmation allows network provider.
        # -----------------------------------------------------

        result = pipeline.acquire_and_ingest(
            request,
            provider_name="network_test",
            confirmation=True,
        )

        assert result.stored_count == 1
        assert network_provider.calls == 1

        print(
            "[PASS] confirmed network provider executed"
        )

        # -----------------------------------------------------
        # 5. Provider capability is correctly exposed.
        # -----------------------------------------------------

        assert (
            engine.provider_requires_network(
                "offline_test"
            )
            is False
        )

        assert (
            engine.provider_requires_network(
                "network_test"
            )
            is True
        )

        print(
            "[PASS] provider network capabilities classified correctly"
        )

        pipeline.close()

    print(
        "SAHIBEX ACQUISITION PERMISSION INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
