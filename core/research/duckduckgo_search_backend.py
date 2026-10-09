from __future__ import annotations

from html.parser import HTMLParser
import urllib.parse
import urllib.request
from dataclasses import dataclass

from core.research.search_provider import (
    SearchProviderBackend,
    SearchResult,
)


@dataclass
class _ResultRow:
    title: str = ""
    url: str = ""
    snippet: str = ""


class _DuckDuckGoHTMLParser(HTMLParser):
    """Small dependency-free parser for DuckDuckGo HTML results."""

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[_ResultRow] = []
        self._row: _ResultRow | None = None
        self._mode: str | None = None
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs_map = dict(attrs)
        classes = set((attrs_map.get("class") or "").split())

        if tag == "a" and ("result__a" in classes or "result-link" in classes):
            if self._row is not None and self._row.title:
                self.rows.append(self._row)
            self._row = _ResultRow()
            self._mode = "title"
            self._buffer = []
            href = attrs_map.get("href") or ""
            self._row.url = href

        elif tag in {"a", "div", "td"} and (
            "result__snippet" in classes or "result-snippet" in classes
        ):
            if self._row is None:
                self._row = _ResultRow()
            self._mode = "snippet"
            self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._mode is not None:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._mode == "title" and tag == "a":
            if self._row is not None:
                self._row.title = " ".join("".join(self._buffer).split())
            self._mode = None
            self._buffer = []

        elif self._mode == "snippet" and tag in {"div", "td"}:
            if self._row is not None:
                self._row.snippet = " ".join("".join(self._buffer).split())
            self._mode = None
            self._buffer = []

    def finish(self) -> list[_ResultRow]:
        if self._row is not None and self._row.title:
            self.rows.append(self._row)
        return self.rows


class DuckDuckGoHTMLBackend(SearchProviderBackend):
    """Dependency-free web search backend.

    It uses DuckDuckGo's HTML search endpoint and returns discovery
    metadata only. Source verification remains downstream.
    """

    backend_name = "duckduckgo_html"

    def __init__(
        self,
        *,
        endpoint: str = "https://lite.duckduckgo.com/lite/",
        timeout_seconds: float = 10.0,
        max_response_bytes: int = 2_000_000,
        user_agent: str = "SAHIBEX-Research-Search/0.1",
    ) -> None:
        if not endpoint.startswith("https://"):
            raise ValueError("endpoint must use HTTPS")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if max_response_bytes <= 0:
            raise ValueError("max_response_bytes must be positive")
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes
        self.user_agent = user_agent

    def search(
        self,
        query: str,
        *,
        max_results: int,
    ) -> list[SearchResult]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if not isinstance(max_results, int) or max_results <= 0:
            raise ValueError("max_results must be a positive integer")

        params = urllib.parse.urlencode({"q": query.strip()})
        request = urllib.request.Request(
            f"{self.endpoint}?{params}",
            headers={"User-Agent": self.user_agent, "Accept": "text/html"},
            method="GET",
        )

        with urllib.request.urlopen(
            request,
            timeout=self.timeout_seconds,
        ) as response:
            payload = response.read(self.max_response_bytes + 1)

        if len(payload) > self.max_response_bytes:
            raise ValueError("search response exceeds configured size limit")

        decoded_payload = payload.decode("utf-8", errors="replace")
        # DuckDuckGo can return HTTP 202 with a human CAPTCHA instead of
        # search results. Do not silently interpret that challenge page as
        # a valid empty search; fail with an actionable diagnostic.
        lowered_payload = decoded_payload.casefold()
        if (
            "anomaly-modal" in lowered_payload
            or "bots use duckduckgo too" in lowered_payload
            or "select all squares containing a duck" in lowered_payload
        ):
            raise RuntimeError(
                "DuckDuckGo returned an anti-bot challenge instead of search results; "
                "configure an approved alternative search backend or retry later."
            )

        parser = _DuckDuckGoHTMLParser()
        parser.feed(decoded_payload)

        results: list[SearchResult] = []
        for row in parser.finish()[:max_results]:
            url = row.url.strip()
            if url.startswith("//"):
                url = "https:" + url
            if "duckduckgo.com/l/?uddg=" in url:
                parsed = urllib.parse.urlparse(url)
                target = urllib.parse.parse_qs(parsed.query).get("uddg", [""])[0]
                if target:
                    url = target
            if not url.startswith(("http://", "https://")):
                continue
            results.append(
                SearchResult(
                    title=row.title,
                    url=url,
                    snippet=row.snippet,
                    rank=len(results) + 1,
                    metadata={
                        "backend": self.backend_name,
                        "provider": "duckduckgo",
                        "discovery_only": True,
                    },
                )
            )

        return results
