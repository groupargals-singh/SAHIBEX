from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.research.acquisition import (
    AcquisitionRequest,
    ResearchAcquisitionEngine,
)


@dataclass(frozen=True)
class ProviderRoute:
    provider_name: str
    reason: str


class ResearchProviderRouter:
    """
    Selects the appropriate research acquisition provider.

    The router ONLY decides which registered provider should handle
    an AcquisitionRequest.

    It does NOT:
        - execute the provider
        - perform network access
        - bypass permission checks
        - ingest research
        - modify the request

    Actual acquisition must still pass through the normal
    ResearchAcquisitionPipeline permission boundary.
    """

    SOURCE_TYPE_MAP = {
        "document": "document",
        "rss": "rss_atom",
        "api": "rest_json_api",
        "web": "direct_web",
        "search": "search",
    }

    def __init__(
        self,
        acquisition_engine: ResearchAcquisitionEngine,
    ) -> None:
        if not isinstance(
            acquisition_engine,
            ResearchAcquisitionEngine,
        ):
            raise TypeError(
                "acquisition_engine must be ResearchAcquisitionEngine"
            )

        self.acquisition_engine = acquisition_engine

    @staticmethod
    def _metadata_value(
        request: AcquisitionRequest,
        *keys: str,
    ) -> Optional[object]:
        for key in keys:
            if key in request.metadata:
                value = request.metadata[key]

                if isinstance(value, str):
                    if value.strip():
                        return value.strip()
                elif isinstance(value, (list, tuple)):
                    if value:
                        return value

        return None

    def _ensure_provider_available(
        self,
        provider_name: str,
    ) -> str:
        try:
            self.acquisition_engine.get_provider(
                provider_name
            )
        except KeyError as exc:
            raise KeyError(
                "required acquisition provider is not registered: "
                f"{provider_name}"
            ) from exc

        return provider_name

    def route(
        self,
        request: AcquisitionRequest,
    ) -> ProviderRoute:
        """
        Select the provider for an acquisition request.

        Explicit source_type has highest priority.

        If source_type is omitted, routing uses safe metadata
        hints before falling back to the search provider.
        """

        if not isinstance(
            request,
            AcquisitionRequest,
        ):
            raise TypeError(
                "request must be an AcquisitionRequest"
            )

        # ---------------------------------------------------------
        # 1. Explicit source type
        # ---------------------------------------------------------
        if request.source_type is not None:
            source_type = request.source_type.strip().lower()

            provider_name = self.SOURCE_TYPE_MAP.get(
                source_type
            )

            if provider_name is None:
                raise ValueError(
                    "unsupported acquisition source_type: "
                    f"{request.source_type}"
                )

            self._ensure_provider_available(
                provider_name
            )

            return ProviderRoute(
                provider_name=provider_name,
                reason=(
                    "explicit source_type requested: "
                    f"{source_type}"
                ),
            )

        # ---------------------------------------------------------
        # 2. Local document metadata
        # ---------------------------------------------------------
        document_path = self._metadata_value(
            request,
            "path",
            "paths",
            "document_path",
            "document_paths",
        )

        if document_path is not None:
            provider_name = self._ensure_provider_available(
                "document"
            )

            return ProviderRoute(
                provider_name=provider_name,
                reason=(
                    "document path metadata detected"
                ),
            )

        # ---------------------------------------------------------
        # 3. Explicit URL metadata
        # ---------------------------------------------------------
        url = self._metadata_value(
            request,
            "url",
            "urls",
            "endpoint",
            "endpoints",
        )

        if url is not None:
            provider_name = self._ensure_provider_available(
                "direct_web"
            )

            return ProviderRoute(
                provider_name=provider_name,
                reason=(
                    "URL/endpoint metadata detected"
                ),
            )

        # ---------------------------------------------------------
        # 4. Default research discovery
        # ---------------------------------------------------------
        provider_name = self._ensure_provider_available(
            "search"
        )

        return ProviderRoute(
            provider_name=provider_name,
            reason=(
                "no explicit provider hint; "
                "defaulting to search discovery"
            ),
        )

    def provider_name(
        self,
        request: AcquisitionRequest,
    ) -> str:
        """
        Convenience method returning only the selected provider name.
        """
        return self.route(request).provider_name
