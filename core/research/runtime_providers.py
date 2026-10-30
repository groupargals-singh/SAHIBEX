from __future__ import annotations

from dataclasses import dataclass
import os

from security.secrets.credential_store import CredentialStore
from core.research.acquisition import ResearchAcquisitionEngine
from core.research.brave_search_backend import BraveSearchBackend
from core.research.duckduckgo_search_backend import DuckDuckGoHTMLBackend
from core.research.google_news_rss_search_backend import GoogleNewsRSSSearchBackend
from core.research.gdelt_search_backend import GDELTSearchBackend
from core.research.bing_news_rss_search_backend import BingNewsRSSSearchBackend
from core.research.multi_source_search_backend import MultiSourceSearchBackend
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
    SAHIBEX_SEARCH_BACKEND may explicitly select google_news_rss,
    duckduckgo_html, or a credential-backed Brave provider. Google News RSS
    is suitable for credential-free discovery; its links remain unverified
    until the publisher-content and evidence pipeline accepts them.
    Without an explicitly configured backend, search remains
    fail-closed rather than silently using a mock provider.
    """
    store = credential_store or CredentialStore()
    engine = ResearchAcquisitionEngine()

    engine.register_provider(
        DirectWebResearchProvider(
            WebProviderConfig(timeout_seconds=5.0, max_sources=10)
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
                MultiSourceSearchBackend([
                    BraveSearchBackend.from_credential_store(store),
                    GoogleNewsRSSSearchBackend(),
                    BingNewsRSSSearchBackend(),
                    GDELTSearchBackend(),
                    DuckDuckGoHTMLBackend(),
                ], timeout_seconds=6.0)
            )
        )
        search_backend = "multi_source"
    elif configured_backend == "google_news_rss":
        engine.register_provider(
            SearchResearchProvider(
                MultiSourceSearchBackend([
                    GoogleNewsRSSSearchBackend(),
                    BingNewsRSSSearchBackend(),
                    GDELTSearchBackend(),
                    DuckDuckGoHTMLBackend(),
                ], timeout_seconds=6.0)
            )
        )
        search_backend = "multi_source"
    elif configured_backend == "duckduckgo_html":
        engine.register_provider(
            SearchResearchProvider(
                MultiSourceSearchBackend([
                    DuckDuckGoHTMLBackend(),
                    GoogleNewsRSSSearchBackend(),
                    BingNewsRSSSearchBackend(),
                    GDELTSearchBackend(),
                ], timeout_seconds=6.0)
            )
        )
        search_backend = "multi_source"
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

    search_configured = brave_configured or configured_backend in {"duckduckgo_html", "google_news_rss"}
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
