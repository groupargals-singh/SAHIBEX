from email.message import Message
import ipaddress
from urllib.error import HTTPError

import pytest

from core.research.web_provider import DirectWebResearchProvider, WebProviderConfig


class FakeResponse:
    def __init__(self, url):
        self._url = url
        self.closed = False

    def geturl(self):
        return self._url

    def close(self):
        self.closed = True


class FakeOpener:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.urls = []

    def open(self, request, timeout):
        self.urls.append(request.full_url)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def redirect(url, code=302, location=None):
    headers = Message()
    if location is not None:
        headers["Location"] = location
    return HTTPError(url, code, "redirect", headers, None)


def provider_with(outcomes):
    provider = DirectWebResearchProvider(WebProviderConfig(timeout_seconds=1))
    # Keep these tests deterministic and offline; unsafe literal IPs are still
    # rejected by _validate_url before hostname resolution.
    def validate_hostname(hostname):
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            return
        if provider._is_unsafe_ip(str(address)):
            raise ValueError("private or reserved IP addresses are not allowed")
    provider._validate_hostname = validate_hostname
    provider._opener = FakeOpener(outcomes)
    return provider


def test_resolves_valid_redirect_with_validation_on_each_hop():
    response = FakeResponse("https://publisher.example/article")
    provider = provider_with([
        redirect("https://news.google.com/story", location="https://publisher.example/article"),
        response,
    ])
    assert provider.resolve_redirect_url("https://news.google.com/story", max_hops=3) == "https://publisher.example/article"
    assert provider._opener.urls == ["https://news.google.com/story", "https://publisher.example/article"]
    assert response.closed


def test_rejects_private_redirect_target_before_request():
    provider = provider_with([redirect("https://news.google.com/story", location="http://127.0.0.1/admin")])
    with pytest.raises(ValueError, match="private or reserved"):
        provider.resolve_redirect_url("https://news.google.com/story")
    assert provider._opener.urls == ["https://news.google.com/story"]


def test_rejects_redirect_without_location():
    provider = provider_with([redirect("https://news.google.com/story")])
    with pytest.raises(RuntimeError, match="no Location"):
        provider.resolve_redirect_url("https://news.google.com/story")


def test_rejects_redirect_loop():
    provider = provider_with([
        redirect("https://news.google.com/story", location="https://publisher.example/article"),
        redirect("https://publisher.example/article", location="https://news.google.com/story"),
    ])
    with pytest.raises(RuntimeError, match="loop"):
        provider.resolve_redirect_url("https://news.google.com/story")


def test_rejects_redirect_chain_over_hop_limit():
    provider = provider_with([
        redirect("https://news.google.com/0", location="https://a.example/1"),
        redirect("https://a.example/1", location="https://b.example/2"),
        redirect("https://b.example/2", location="https://c.example/3"),
        redirect("https://c.example/3", location="https://d.example/4"),
    ])
    with pytest.raises(RuntimeError, match="hop limit"):
        provider.resolve_redirect_url("https://news.google.com/0", max_hops=3)


def test_automatic_redirects_remain_disabled_by_default():
    provider = DirectWebResearchProvider()
    with pytest.raises(ValueError, match="automatic redirects"):
        DirectWebResearchProvider(WebProviderConfig(allow_redirects=True))
    assert provider.config.allow_redirects is False
