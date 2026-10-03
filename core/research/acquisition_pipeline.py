from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib

from core.policies.approval import PermissionEngine

from core.research.acquisition import (
    AcquisitionRequest,
    AcquisitionResult,
    AcquiredSource,
    ResearchAcquisitionEngine,
)

from core.research.acquisition_permission import (
    AcquisitionPermissionGate,
)

from core.research.acquisition_validator import (
    AcquisitionSafetyValidator,
)

from core.research.deduplication import (
    DocumentDeduplicator,
)

from core.research.models import (
    ResearchDocument,
    ResearchSource,
)

from core.research.pipeline import (
    IngestionResult,
    ResearchIngestionPipeline,
)
from core.research.reliability import apply_reliability_contract

@dataclass(frozen=True)
class AcquiredIngestionResult:
    acquisition: AcquisitionResult
    ingested: list[IngestionResult]
    stored_count: int
    duplicate_count: int


class ResearchAcquisitionPipeline:
    """
    Complete research acquisition safety pipeline.

    Flow:

        Request
          ↓
        Provider capability check
          ↓
        Network permission gate
          ↓
        Provider acquisition
          ↓
        Acquisition safety validation
          ↓
        Research conversion
          ↓
        Deduplication
          ↓
        Persistent ingestion

    IMPORTANT:
    Network-capable providers are never executed unless
    NETWORK_ACCESS permission has been explicitly granted.
    """

    def __init__(
        self,
        database_path: str | Path,
        acquisition_engine: ResearchAcquisitionEngine,
        source_registry=None,
        deduplicator: DocumentDeduplicator | None = None,
        engine=None,
        validator: AcquisitionSafetyValidator | None = None,
        permission_gate: AcquisitionPermissionGate | None = None,
        permission_engine: PermissionEngine | None = None,
    ):
        if not isinstance(
            acquisition_engine,
            ResearchAcquisitionEngine,
        ):
            raise TypeError(
                "acquisition_engine must be ResearchAcquisitionEngine"
            )

        self.acquisition_engine = acquisition_engine

        self.validator = (
            validator
            if validator is not None
            else AcquisitionSafetyValidator()
        )

        # Allow either a pre-built permission gate or a permission engine.
        if permission_gate is not None:
            if not isinstance(
                permission_gate,
                AcquisitionPermissionGate,
            ):
                raise TypeError(
                    "permission_gate must be AcquisitionPermissionGate"
                )

            self.permission_gate = permission_gate

        else:
            if permission_engine is None:
                permission_engine = PermissionEngine()

            if not isinstance(
                permission_engine,
                PermissionEngine,
            ):
                raise TypeError(
                    "permission_engine must be PermissionEngine"
                )

            self.permission_gate = AcquisitionPermissionGate(
                permission_engine
            )

        self.ingestion_pipeline = ResearchIngestionPipeline(
            database_path=database_path,
            source_registry=source_registry,
            deduplicator=deduplicator,
            engine=engine,
        )

    @staticmethod
    def _build_source(
        acquired: AcquiredSource,
    ) -> ResearchSource:
        metadata = apply_reliability_contract(
            acquired.metadata,
        )

        metadata["acquisition"] = True

        if acquired.locator:
            metadata["locator"] = acquired.locator

        reliability = metadata["reliability"]

        return ResearchSource(
            source_id=acquired.source_id,
            title=acquired.title,
            source_type=acquired.source_type,
            locator=acquired.locator,
            publisher=acquired.publisher,
            author=acquired.author,
            published_at=acquired.published_at,
            reliability=reliability,
            metadata=metadata,
        )

    @staticmethod
    def _build_document(
        acquired: AcquiredSource,
    ) -> ResearchDocument:
        if not acquired.content.strip():
            raise ValueError(
                "acquired source content cannot be empty"
            )

        content_hash = hashlib.sha256(
            acquired.content.encode("utf-8")
        ).hexdigest()

        metadata = dict(acquired.metadata)

        metadata["acquisition"] = True
        metadata["locator"] = acquired.locator
        metadata["source_id"] = acquired.source_id

        return ResearchDocument(
            document_id=f"doc_{content_hash}",
            source_id=acquired.source_id,
            title=acquired.title,
            content=acquired.content,
            collected_at=acquired.metadata.get(
                "collected_at"
            ),
            content_hash=content_hash,
            language=acquired.metadata.get(
                "language",
                "unknown",
            ),
            metadata=metadata,
        )

    def validate_acquired_source(
        self,
        acquired: AcquiredSource,
    ):
        """
        Validate an acquired source before conversion
        or persistence.
        """
        return self.validator.validate(acquired)

    def check_network_permission(
        self,
        provider_name: str,
        *,
        confirmation: bool = False,
    ):
        """
        Check whether the selected provider is network-capable
        and whether NETWORK_ACCESS permission is available.
        """

        requires_network = (
            self.acquisition_engine.provider_requires_network(
                provider_name
            )
        )

        if not requires_network:
            return {
                "allowed": True,
                "requires_network": False,
                "requires_confirmation": False,
                "risk": "low",
                "reason": (
                    "Provider is declared non-network."
                ),
            }

        result = self.permission_gate.check_network_access(
            confirmation=confirmation,
        )

        return {
            "allowed": result.allowed,
            "requires_network": True,
            "requires_confirmation": result.requires_confirmation,
            "risk": result.risk,
            "reason": result.reason,
        }

    def ingest_acquired_sources(
        self,
        acquisition: AcquisitionResult,
    ) -> AcquiredIngestionResult:
        if not isinstance(
            acquisition,
            AcquisitionResult,
        ):
            raise TypeError(
                "acquisition must be AcquisitionResult"
            )

        ingested: list[IngestionResult] = []

        stored_count = 0
        duplicate_count = 0

        for acquired in acquisition.sources:

            validation = self.validator.validate(
                acquired
            )

            if not validation.valid:
                errors = "; ".join(
                    validation.errors
                )

                raise ValueError(
                    "acquired source failed safety validation: "
                    f"{acquired.source_id}: {errors}"
                )

            source = self._build_source(
                acquired
            )

            document = self._build_document(
                acquired
            )

            result = self.ingestion_pipeline.ingest(
                source,
                document,
            )

            ingested.append(result)

            if result.duplicate:
                duplicate_count += 1
            else:
                stored_count += 1

        return AcquiredIngestionResult(
            acquisition=acquisition,
            ingested=ingested,
            stored_count=stored_count,
            duplicate_count=duplicate_count,
        )

    def acquire_and_ingest(
        self,
        request: AcquisitionRequest,
        provider_name: str,
        *,
        confirmation: bool = False,
    ) -> AcquiredIngestionResult:
        """
        Acquire and ingest research.

        Network-capable providers MUST pass the
        NETWORK_ACCESS permission gate before provider.acquire()
        is called.

        `confirmation=True` MUST only be supplied after explicit
        user approval has been obtained by the upper-level system.
        """

        if not isinstance(
            request,
            AcquisitionRequest,
        ):
            raise TypeError(
                "request must be an AcquisitionRequest"
            )

        if not isinstance(
            provider_name,
            str,
        ) or not provider_name.strip():
            raise ValueError(
                "provider_name is required"
            )

        # ---------------------------------------------------------
        # SECURITY BOUNDARY
        # ---------------------------------------------------------
        #
        # Determine provider capability BEFORE calling acquire().
        #
        permission = self.check_network_permission(
            provider_name,
            confirmation=confirmation,
        )

        if not permission["allowed"]:
            if permission["requires_confirmation"]:
                raise PermissionError(
                    "research acquisition blocked: "
                    "NETWORK_ACCESS permission requires explicit "
                    f"user confirmation. {permission['reason']}"
                )

            raise PermissionError(
                "research acquisition blocked: "
                f"{permission['reason']}"
            )

        # ---------------------------------------------------------
        # Provider execution happens ONLY after permission.
        # ---------------------------------------------------------

        acquisition = self.acquisition_engine.acquire(
            request,
            provider_name=provider_name,
        )

        return self.ingest_acquired_sources(
            acquisition
        )

    def close(self) -> None:
        self.ingestion_pipeline.close()

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        self.close()
        return False
