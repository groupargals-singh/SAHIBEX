from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class AcquisitionRequest:
    query: str
    source_type: Optional[str] = None
    max_sources: int = 10
    metadata: Dict[str, object] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.query, str) or not self.query.strip():
            raise ValueError("query must be a non-empty string")

        if not isinstance(self.max_sources, int) or isinstance(
            self.max_sources,
            bool,
        ):
            raise ValueError("max_sources must be an integer")

        if self.max_sources <= 0:
            raise ValueError("max_sources must be greater than zero")

        if self.source_type is not None:
            if not isinstance(self.source_type, str):
                raise ValueError("source_type must be a string or None")

            if not self.source_type.strip():
                raise ValueError("source_type cannot be empty")


@dataclass(frozen=True)
class AcquiredSource:
    source_id: str
    title: str
    source_type: str
    locator: str
    publisher: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[object] = None
    content: str = ""
    metadata: Dict[str, object] = field(default_factory=dict)

    def __post_init__(self):
        if not self.source_id:
            raise ValueError("source_id is required")

        if not self.title:
            raise ValueError("title is required")

        if not self.source_type:
            raise ValueError("source_type is required")

        if not self.locator:
            raise ValueError("locator is required")

        if not isinstance(self.content, str):
            raise ValueError("content must be a string")


@dataclass(frozen=True)
class AcquisitionResult:
    query: str
    sources: List[AcquiredSource]
    completed: bool
    status: str
    metadata: Dict[str, object] = field(default_factory=dict)


class ResearchAcquisitionProvider:
    """
    Interface for research acquisition providers.

    Security contract
    -----------------
    requires_network=True:
        Provider may perform network access and therefore must pass
        the SAHIBEX NETWORK_ACCESS permission boundary.

    requires_network=False:
        Provider is expected to operate without network access.

    Network-capable providers MUST explicitly declare:
        requires_network = True
    """

    provider_name = "base"

    # Safe default for the abstract/base provider.
    # Real network providers MUST explicitly set this to True.
    requires_network = False

    def acquire(
        self,
        request: AcquisitionRequest,
    ) -> AcquisitionResult:
        raise NotImplementedError(
            "acquisition provider must implement acquire()"
        )


class ResearchAcquisitionEngine:
    """
    Routes acquisition requests to registered providers.

    The engine itself does not perform network access.

    Provider network capability is exposed through the
    provider's `requires_network` contract so the caller can
    enforce the SAHIBEX NETWORK_ACCESS permission boundary
    before provider.acquire() is executed.
    """

    def __init__(
        self,
        providers: Optional[Iterable[ResearchAcquisitionProvider]] = None,
    ):
        self._providers: Dict[str, ResearchAcquisitionProvider] = {}

        if providers:
            for provider in providers:
                self.register_provider(provider)

    def register_provider(
        self,
        provider: ResearchAcquisitionProvider,
        *,
        replace: bool = False,
    ) -> None:
        if not isinstance(
            provider,
            ResearchAcquisitionProvider,
        ):
            raise TypeError(
                "provider must be a ResearchAcquisitionProvider"
            )

        name = provider.provider_name

        if not isinstance(name, str) or not name.strip():
            raise ValueError("provider_name is required")

        if name in self._providers and not replace:
            raise ValueError(
                f"provider already registered: {name}"
            )

        requires_network = getattr(
            provider,
            "requires_network",
            None,
        )

        if not isinstance(requires_network, bool):
            raise ValueError(
                "provider requires_network must be boolean"
            )

        self._providers[name] = provider

    def get_provider(
        self,
        provider_name: str,
    ) -> ResearchAcquisitionProvider:
        if not isinstance(provider_name, str) or not provider_name.strip():
            raise ValueError(
                "provider_name is required"
            )

        if provider_name not in self._providers:
            raise KeyError(
                f"unknown acquisition provider: {provider_name}"
            )

        return self._providers[provider_name]

    def providers(self) -> List[str]:
        return sorted(self._providers.keys())

    def provider_requires_network(
        self,
        provider_name: str,
    ) -> bool:
        provider = self.get_provider(provider_name)

        return bool(
            provider.requires_network
        )

    def acquire(
        self,
        request: AcquisitionRequest,
        provider_name: str,
    ) -> AcquisitionResult:
        if not isinstance(
            request,
            AcquisitionRequest,
        ):
            raise TypeError(
                "request must be an AcquisitionRequest"
            )

        provider = self.get_provider(provider_name)

        result = provider.acquire(request)

        if not isinstance(
            result,
            AcquisitionResult,
        ):
            raise TypeError(
                "provider must return AcquisitionResult"
            )

        if result.query != request.query:
            raise ValueError(
                "provider result query does not match request"
            )

        return result
