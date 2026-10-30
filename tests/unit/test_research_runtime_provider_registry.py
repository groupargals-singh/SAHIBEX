from pathlib import Path

from core.research.brave_search_backend import BraveSearchBackend
from core.research.google_news_rss_search_backend import GoogleNewsRSSSearchBackend
from core.research.multi_source_search_backend import MultiSourceSearchBackend
from core.research.search_provider import UnavailableSearchBackend
from core.research.runtime_providers import (
    build_default_research_acquisition_engine,
)


from security.secrets.credential_store import CredentialStore


class FakeCredentialStore(CredentialStore):
    def __init__(self, available: bool = False) -> None:
        self.available = available

    def has_credential(self, provider: str) -> bool:
        assert provider == "brave"
        return self.available

    def require_credential(self, provider: str) -> str:
        assert provider == "brave"
        return "test-brave-key"


def test_default_runtime_registry_is_network_safe_without_credentials():
    engine, status = build_default_research_acquisition_engine(
        project_root=Path.cwd(),
        credential_store=FakeCredentialStore(False),
    )

    assert "direct_web" in engine.providers()
    assert "rss_atom" in engine.providers()
    assert "document" in engine.providers()
    assert "search" in engine.providers()
    assert "search" not in status.providers
    assert status.search_backend is None
    assert status.brave_configured is False
    assert isinstance(
        engine.get_provider("search").backend,
        UnavailableSearchBackend,
    )
    assert engine.provider_requires_network("search") is True


def test_runtime_registry_wires_google_news_rss_when_explicitly_configured(monkeypatch):
    monkeypatch.setenv("SAHIBEX_SEARCH_BACKEND", "google_news_rss")
    engine, status = build_default_research_acquisition_engine(
        project_root=Path.cwd(),
        credential_store=FakeCredentialStore(False),
    )

    assert status.search_backend == "multi_source"
    assert status.brave_configured is False
    assert "search" in status.providers
    backend = engine.get_provider("search").backend
    assert isinstance(backend, MultiSourceSearchBackend)
    assert [item.backend_name for item in backend.backends] == [
        "google_news_rss", "bing_news_rss", "gdelt_doc_rss", "duckduckgo_html"
    ]
    # Bing RSS needs ~4–5 seconds on slower mobile connections. A 4s fan-out
    # deadline consistently discarded its direct publisher URLs and left only
    # Google News wrappers, which cannot be promoted to evidence.
    assert backend.timeout_seconds == 6.0


def test_default_runtime_registry_wires_brave_search_when_configured():
    engine, status = build_default_research_acquisition_engine(
        project_root=Path.cwd(),
        credential_store=FakeCredentialStore(True),
    )

    assert "search" in engine.providers()
    assert status.search_backend == "multi_source"
    assert status.brave_configured is True
    backend = engine.get_provider("search").backend
    assert isinstance(backend, MultiSourceSearchBackend)
    assert [item.backend_name for item in backend.backends] == [
        "brave_search", "google_news_rss", "bing_news_rss", "gdelt_doc_rss", "duckduckgo_html"
    ]
