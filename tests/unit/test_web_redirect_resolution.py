from __future__ import annotations

from email.message import Message
import time
from urllib.error import HTTPError
from urllib.parse import urlparse
from unittest.mock import Mock

import pytest

import core.research.web_provider as web_provider
from core.research.web_provider import DirectWebResearchProvider, WebProviderConfig


class FakeResponse:
    def __init__(self, url: str):
        self.url = url
        self.closed = False

    def geturl(self):
        return self.url

    def close(self):
        self.closed = True


class SequenceOpener:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.requests = []

    def open(self, request, timeout=None):
        self.requests.append((request, timeout))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def redirect(code: int, location: str | None):
    headers = Message()
    if location is not None:
        headers["Location"] = location
    return HTTPError("https://news.google.com/start", code, "redirect", headers, None)


def provider_with(outcomes):
    provider = DirectWebResearchProvider(WebProviderConfig(timeout_seconds=1))
    provider._opener = SequenceOpener(outcomes)
    # Avoid DNS/network dependency in unit tests while still modeling SSRF checks.
    def validate(url):
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("unsafe URL")
        if parsed.hostname in {"127.0.0.1", "localhost", "10.0.0.1", "169.254.169.254"}:
            raise ValueError("private or reserved host")
    provider._validate_url = validate
    return provider


def test_hostname_resolution_timeout_fails_closed_without_blocking(monkeypatch):
    monkeypatch.setattr(web_provider, "_DNS_LOOKUP_TIMEOUT_SECONDS", 0.02)

    def stalled_getaddrinfo(*args, **kwargs):
        time.sleep(0.2)
        return [(None, None, None, None, ("93.184.216.34", 0))]

    monkeypatch.setattr(web_provider.socket, "getaddrinfo", stalled_getaddrinfo)
    provider = DirectWebResearchProvider(WebProviderConfig(timeout_seconds=1))

    started = time.monotonic()
    with pytest.raises(ValueError, match="hostname resolution timed out"):
        provider._validate_hostname("example.com")

    assert time.monotonic() - started < 0.15


def test_resolves_valid_redirect_without_enabling_automatic_redirects():
    final = FakeResponse("https://publisher.example/article")
    provider = provider_with([redirect(302, "https://publisher.example/article"), final])
    assert provider.resolve_redirect_url("https://news.google.com/start") == "https://publisher.example/article"
    assert final.closed is True
    assert len(provider._opener.requests) == 2


def test_rejects_private_host_redirect_before_requesting_it():
    provider = provider_with([redirect(302, "http://127.0.0.1/admin")])
    with pytest.raises(ValueError, match="private or reserved"):
        provider.resolve_redirect_url("https://news.google.com/start")
    assert len(provider._opener.requests) == 1


def test_rejects_redirect_without_location():
    provider = provider_with([redirect(301, None)])
    with pytest.raises(RuntimeError, match="no Location"):
        provider.resolve_redirect_url("https://news.google.com/start")


def test_rejects_redirect_loop():
    provider = provider_with([
        redirect(302, "https://news.google.com/again"),
        redirect(302, "https://news.google.com/start"),
    ])
    with pytest.raises(RuntimeError, match="loop"):
        provider.resolve_redirect_url("https://news.google.com/start")


def test_rejects_redirect_chain_over_hop_limit():
    provider = provider_with([
        redirect(302, "https://news.google.com/one"),
        redirect(302, "https://news.google.com/two"),
    ])
    with pytest.raises(RuntimeError, match="hop limit"):
        provider.resolve_redirect_url("https://news.google.com/start", max_hops=1)


def test_rejects_invalid_hop_limit():
    provider = provider_with([])
    with pytest.raises(ValueError, match="max_hops"):
        provider.resolve_redirect_url("https://news.google.com/start", max_hops=99)


def test_default_direct_fetch_still_disables_automatic_redirects():
    provider = DirectWebResearchProvider()
    assert provider.config.allow_redirects is False
    with pytest.raises(ValueError, match="automatic redirects"):
        DirectWebResearchProvider(WebProviderConfig(allow_redirects=True))
