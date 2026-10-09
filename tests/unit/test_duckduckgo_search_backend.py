from __future__ import annotations

from unittest.mock import patch

import pytest

from core.research.duckduckgo_search_backend import DuckDuckGoHTMLBackend


class _FakeResponse:
    def __init__(self, body: bytes, status: int = 202):
        self._body = body
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size: int = -1) -> bytes:
        return self._body[:size]


def test_duckduckgo_captcha_challenge_is_not_reported_as_empty_results():
    body = (
        b"<html><body><div class='anomaly-modal__title'>"
        b"Unfortunately, bots use DuckDuckGo too."
        b"</div><div>Select all squares containing a duck</div></body></html>"
    )
    backend = DuckDuckGoHTMLBackend()
    with patch(
        "core.research.duckduckgo_search_backend.urllib.request.urlopen",
        return_value=_FakeResponse(body),
    ):
        with pytest.raises(RuntimeError, match="anti-bot challenge"):
            backend.search("latest AI safety report", max_results=5)


def test_duckduckgo_regular_html_results_still_parse():
    body = (
        b"<html><body><a class='result__a' href='https://example.org/report'>"
        b"Official AI Safety Report</a>"
        b"<td class='result__snippet'>Independent evidence</td></body></html>"
    )
    backend = DuckDuckGoHTMLBackend()
    with patch(
        "core.research.duckduckgo_search_backend.urllib.request.urlopen",
        return_value=_FakeResponse(body, status=200),
    ):
        results = backend.search("AI safety report", max_results=5)
    assert len(results) == 1
    assert results[0].title == "Official AI Safety Report"
    assert results[0].url == "https://example.org/report"
