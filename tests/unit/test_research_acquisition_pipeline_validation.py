from __future__ import annotations

import tempfile
from pathlib import Path

from core.research.acquisition import (
    AcquisitionRequest,
    AcquisitionResult,
    AcquiredSource,
    ResearchAcquisitionEngine,
    ResearchAcquisitionProvider,
)
from core.research.acquisition_pipeline import (
    ResearchAcquisitionPipeline,
)
from core.research.storage import ResearchStorage


class SafeTestProvider(ResearchAcquisitionProvider):
    provider_name = "validation_safe_provider"

    def acquire(
        self,
        request: AcquisitionRequest,
    ) -> AcquisitionResult:
        return AcquisitionResult(
            query=request.query,
            sources=[
                AcquiredSource(
                    source_id="safe_source",
                    title="Safe Source",
                    source_type="web",
                    locator="https://example.com",
                    content="Safe research content.",
                    metadata={},
                )
            ],
            completed=True,
            status="completed",
        )


class InvalidTestProvider(ResearchAcquisitionProvider):
    provider_name = "validation_invalid_provider"

    def acquire(
        self,
        request: AcquisitionRequest,
    ) -> AcquisitionResult:
        return AcquisitionResult(
            query=request.query,
            sources=[
                AcquiredSource(
                    source_id="invalid_source",
                    title="Invalid Source",
                    source_type="web",
                    locator="ftp://malicious.example.com",
                    content="This source must never reach storage.",
                    metadata={},
                )
            ],
            completed=True,
            status="completed",
        )


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    print(
        "SAHIBEX RESEARCH ACQUISITION PIPELINE "
        "VALIDATION TEST"
    )

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "research.db"

        # ---------------------------------------------------------
        # 1. Create acquisition engine
        # ---------------------------------------------------------

        acquisition_engine = ResearchAcquisitionEngine()

        safe_provider = SafeTestProvider()
        invalid_provider = InvalidTestProvider()

        acquisition_engine.register_provider(
            safe_provider
        )

        acquisition_engine.register_provider(
            invalid_provider
        )

        # ---------------------------------------------------------
        # 2. Create acquisition pipeline
        # ---------------------------------------------------------

        pipeline = ResearchAcquisitionPipeline(
            database_path=db_path,
            acquisition_engine=acquisition_engine,
        )

        # ---------------------------------------------------------
        # 3. Valid acquisition
        # ---------------------------------------------------------

        safe_request = AcquisitionRequest(
            query="safe validation test",
        )

        safe_result = pipeline.acquire_and_ingest(
            safe_request,
            provider_name="validation_safe_provider",
        )

        check(
            safe_result.stored_count == 1,
            "valid acquired source stored",
        )

        check(
            safe_result.duplicate_count == 0,
            "valid source not marked duplicate",
        )

        # ---------------------------------------------------------
        # 4. Verify valid source persistence
        # ---------------------------------------------------------

        storage = ResearchStorage(db_path)

        safe_source = storage.get_source(
            "safe_source"
        )

        check(
            safe_source is not None,
            "valid source persisted",
        )

        # ---------------------------------------------------------
        # 5. Verify valid document persistence
        # ---------------------------------------------------------

        storage_summary = storage.summary()

        check(
            storage_summary["documents"] == 1,
            "valid document persisted",
        )

        # ---------------------------------------------------------
        # 6. Invalid acquisition must be rejected
        # ---------------------------------------------------------

        invalid_request = AcquisitionRequest(
            query="invalid validation test",
        )

        rejected = False

        try:
            pipeline.acquire_and_ingest(
                invalid_request,
                provider_name="validation_invalid_provider",
            )
        except ValueError:
            rejected = True

        check(
            rejected,
            "invalid acquired source rejected",
        )

        # ---------------------------------------------------------
        # 7. Invalid source must NOT be persisted
        # ---------------------------------------------------------

        invalid_source = storage.get_source(
            "invalid_source"
        )

        check(
            invalid_source is None,
            "invalid source not persisted",
        )

        # ---------------------------------------------------------
        # 8. Invalid document must NOT be persisted
        # ---------------------------------------------------------

        storage_summary_after = storage.summary()

        check(
            storage_summary_after["documents"] == 1,
            "invalid document not persisted",
        )

        # ---------------------------------------------------------
        # 9. Verify source count did not increase
        # ---------------------------------------------------------

        final_source = storage.get_source(
            "invalid_source"
        )

        check(
            final_source is None,
            "database contains no invalid source",
        )

        # ---------------------------------------------------------
        # 10. Close resources
        # ---------------------------------------------------------

        storage.close()
        pipeline.close()

    print()
    print(
        "SAHIBEX RESEARCH ACQUISITION PIPELINE "
        "VALIDATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
