from __future__ import annotations

from dataclasses import dataclass
import os

from security.secrets.credential_store import CredentialStore
from core.research.acquisition import ResearchAcquisitionEngine
from core.research.brave_search_backend import BraveSearchBackend
from core.research.duckduckgo_search_backend import DuckDuckGoHTMLBackend
from core.research.bing_news_rss_search_backend import BingNewsRSSSearchBackend
from core.research.document_provider import (
    DocumentProviderConfig,
    LocalDocumentResearchProvider,
)
from core.research.rss_provider import RSSAtomResearchProvider
from core.research.search_provider import (
    SearchResearchProvider,
    UnavailableSearchBackend,
)
from core.research.web_provider import (
    DirectWebResearchProvider,
    WebProviderConfig,
)


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
    When SAHIBEX_SEARCH_BACKEND=duckduckgo_html is explicitly set,
    the dependency-free DuckDuckGo discovery backend is enabled.
    Without an explicitly configured backend, search remains
    fail-closed rather than silently using a mock provider.
    """
    store = credential_store or CredentialStore()
    engine = ResearchAcquisitionEngine()

    engine.register_provider(
        DirectWebResearchProvider(
            WebProviderConfig(timeout_seconds=5.0, max_sources=5)
        )
    )
    engine.register_provider(RSSAtomResearchProvider())

    engine.register_provider(
        LocalDocumentResearchProvider(
            DocumentProviderConfig(project_root=project_root)
        )
    )

    search_backend = None
    brave_configured = store.has_credential("brave")
    configured_backend = os.environ.get("SAHIBEX_SEARCH_BACKEND", "").strip().lower()

    if brave_configured:
        engine.register_provider(
            SearchResearchProvider(
                BraveSearchBackend.from_credential_store(
                    store
                )
            )
        )
        search_backend = "brave_search"
    elif configured_backend == "duckduckgo_html":
        engine.register_provider(
            SearchResearchProvider(
                DuckDuckGoHTMLBackend(),
                fallback_backend=BingNewsRSSSearchBackend(),
            )
        )
        search_backend = "duckduckgo_html"
    else:
        # Keep the search capability registered for a stable provider
        # contract, but use an explicit fail-closed backend. It is not
        # advertised as an active runtime provider until configured.
        engine.register_provider(
            SearchResearchProvider(
                UnavailableSearchBackend()
            )
        )
        search_backend = None

    search_configured = brave_configured or configured_backend == "duckduckgo_html"
    active_providers = tuple(
        provider
        for provider in engine.providers()
        if provider != "search" or search_configured
    )

    return (
        engine,
        ResearchRuntimeProviderStatus(
            providers=active_providers,
            search_backend=search_backend,
            brave_configured=brave_configured,
        ),
    )
