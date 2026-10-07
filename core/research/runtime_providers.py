from __future__ import annotations

from dataclasses import dataclass

from security.secrets.credential_store import CredentialStore
from core.research.acquisition import ResearchAcquisitionEngine
from core.research.brave_search_backend import BraveSearchBackend
from core.research.document_provider import (
    DocumentProviderConfig,
    LocalDocumentResearchProvider,
)
from core.research.rss_provider import RSSAtomResearchProvider
from core.research.search_provider import SearchResearchProvider
from core.research.web_provider import DirectWebResearchProvider


@dataclass(frozen=True)
class ResearchRuntimeProviderStatus:
    providers: tuple[str, ...]
    search_backend: str | None
    brave_configured: bool


def build_default_research_acquisition_engine(
    *,
    project_root,
    credential_store: CredentialStore | None = None,
) -> tuple[ResearchAcquisitionEngine, ResearchRuntimeProviderStatus]:
    """
    Build the production research provider registry.

    Network-capable providers are registered here, but this factory
    never grants NETWORK_ACCESS permission. The acquisition pipeline
    remains the only execution gate.

    Search uses Brave when SAHIBEX_BRAVE_API_KEY is configured.
    Without it, the registry remains explicit about search being
    unavailable rather than silently using a mock provider.
    """
    store = credential_store or CredentialStore()
    engine = ResearchAcquisitionEngine()

    engine.register_provider(DirectWebResearchProvider())
    engine.register_provider(RSSAtomResearchProvider())

    engine.register_provider(
        LocalDocumentResearchProvider(
            DocumentProviderConfig(project_root=project_root)
        )
    )

    search_backend = None
    brave_configured = store.has_credential("brave")

    if brave_configured:
        engine.register_provider(
            SearchResearchProvider(
                BraveSearchBackend.from_credential_store(
                    store
                )
            )
        )
        search_backend = "brave_search"
    return (
        engine,
        ResearchRuntimeProviderStatus(
            providers=tuple(engine.providers()),
            search_backend=search_backend,
            brave_configured=brave_configured,
        ),
    )
