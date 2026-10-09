from pathlib import Path

from core.research.brave_search_backend import BraveSearchBackend
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


def test_default_runtime_registry_wires_brave_search_when_configured():
    engine, status = build_default_research_acquisition_engine(
        project_root=Path.cwd(),
        credential_store=FakeCredentialStore(True),
    )

    assert "search" in engine.providers()
    assert status.search_backend == "brave_search"
    assert status.brave_configured is True
    assert isinstance(
        engine.get_provider("search").backend,
        BraveSearchBackend,
    )
