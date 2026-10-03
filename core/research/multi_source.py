from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

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
from core.research.provider_router import (
    ResearchProviderRouter,
)


@dataclass(frozen=True)
class MultiSourceProviderResult:
    provider_name: str
    acquisition: AcquisitionResult


@dataclass(frozen=True)
class MultiSourceAcquisitionResult:
    query: str
    sources: List[AcquiredSource]
    provider_results: List[MultiSourceProviderResult]
    failed_providers: List[str]
    completed: bool
    status: str


class ResearchMultiSourceAcquisition:
    """
    Coordinates acquisition from multiple research providers.

    Responsibilities:
        - route requests to providers
        - enforce network permission before network providers
        - execute providers only after permission
        - merge acquired sources
        - remove duplicate source IDs

    This class does NOT:
        - bypass permission checks
        - perform network access itself
        - ingest research into the database
        - modify provider behavior
    """

    def __init__(
        self,
        acquisition_engine: ResearchAcquisitionEngine,
        permission_gate: AcquisitionPermissionGate | None = None,
        permission_engine: PermissionEngine | None = None,
    ) -> None:
        if not isinstance(
            acquisition_engine,
            ResearchAcquisitionEngine,
        ):
            raise TypeError(
                "acquisition_engine must be ResearchAcquisitionEngine"
            )

        self.acquisition_engine = acquisition_engine

        self.router = ResearchProviderRouter(
            acquisition_engine
        )

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

    def _check_permission(
        self,
        provider_name: str,
        *,
        confirmation: bool,
    ) -> None:
        requires_network = (
            self.acquisition_engine.provider_requires_network(
                provider_name
            )
        )

        if not requires_network:
            return

        permission = (
            self.permission_gate.check_network_access(
                confirmation=confirmation
            )
        )

        if not permission.allowed:
            raise PermissionError(
                "multi-source acquisition blocked for provider "
                f"{provider_name}: {permission.reason}"
            )

    def acquire(
        self,
        requests: Sequence[AcquisitionRequest],
        *,
        confirmation: bool = False,
    ) -> MultiSourceAcquisitionResult:
        if isinstance(requests, (str, bytes)):
            raise TypeError(
                "requests must be a sequence of AcquisitionRequest"
            )

        if not isinstance(
            requests,
            Sequence,
        ):
            raise TypeError(
                "requests must be a sequence of AcquisitionRequest"
            )

        if not requests:
            raise ValueError(
                "requests cannot be empty"
            )

        for request in requests:
            if not isinstance(
                request,
                AcquisitionRequest,
            ):
                raise TypeError(
                    "all requests must be AcquisitionRequest instances"
                )

        query = requests[0].query

        for request in requests[1:]:
            if request.query != query:
                raise ValueError(
                    "all multi-source requests must use the same query"
                )

        provider_results: List[
            MultiSourceProviderResult
        ] = []

        failed_providers: List[str] = []

        merged_sources: List[AcquiredSource] = []
        seen_source_ids: set[str] = set()

        for request in requests:
            try:
                route = self.router.route(request)
                provider_name = route.provider_name

                self._check_permission(
                    provider_name,
                    confirmation=confirmation,
                )

                acquisition = (
                    self.acquisition_engine.acquire(
                        request,
                        provider_name=provider_name,
                    )
                )

                provider_results.append(
                    MultiSourceProviderResult(
                        provider_name=provider_name,
                        acquisition=acquisition,
                    )
                )

                for source in acquisition.sources:
                    if source.source_id in seen_source_ids:
                        continue

                    seen_source_ids.add(
                        source.source_id
                    )

                    merged_sources.append(source)

            except Exception:
                try:
                    provider_name = (
                        self.router.route(
                            request
                        ).provider_name
                    )
                except Exception:
                    provider_name = "unknown"

                failed_providers.append(
                    provider_name
                )

        total_requested = len(requests)

        successful_providers = len(
            provider_results
        )

        if successful_providers == total_requested:
            completed = True
            status = "completed"

        elif successful_providers > 0:
            completed = False
            status = "partial"

        else:
            completed = False
            status = "failed"

        return MultiSourceAcquisitionResult(
            query=query,
            sources=merged_sources,
            provider_results=provider_results,
            failed_providers=failed_providers,
            completed=completed,
            status=status,
        )
