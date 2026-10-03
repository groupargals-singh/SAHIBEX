from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional

from core.research.search_provider import (
    SearchProviderBackend,
    SearchResult,
)
from security.secrets.credential_store import CredentialStore

@dataclass(frozen=True)
class BraveSearchConfig:
    endpoint: str = (
        "https://api.search.brave.com/"
        "res/v1/web/search"
    )

    timeout_seconds: float = 10.0
    max_response_bytes: int = 2_000_000

    country: str = "IN"
    search_lang: str = "en"
    ui_lang: str = "en-IN"

    safesearch: str = "moderate"
    spellcheck: bool = True

    user_agent: str = (
        "SAHIBEX-Research-Search/0.1"
    )

    def __post_init__(self) -> None:
        if (
            not isinstance(self.endpoint, str)
            or not self.endpoint.strip()
        ):
            raise ValueError(
                "endpoint must be a non-empty string"
            )

        parsed = urllib.parse.urlparse(
            self.endpoint
        )

        if parsed.scheme != "https":
            raise ValueError(
                "Brave endpoint must use HTTPS"
            )

        if not parsed.hostname:
            raise ValueError(
                "endpoint must contain a hostname"
            )

        if parsed.username or parsed.password:
            raise ValueError(
                "endpoint must not contain credentials"
            )

        if self.timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be positive"
            )

        if self.max_response_bytes <= 0:
            raise ValueError(
                "max_response_bytes must be positive"
            )

        if not isinstance(self.country, str):
            raise ValueError(
                "country must be a string"
            )

        if len(self.country) != 2:
            raise ValueError(
                "country must be a 2-letter code"
            )

        if not isinstance(
            self.search_lang,
            str,
        ):
            raise ValueError(
                "search_lang must be a string"
            )

        if not self.search_lang.strip():
            raise ValueError(
                "search_lang must not be empty"
            )

        if not isinstance(
            self.ui_lang,
            str,
        ):
            raise ValueError(
                "ui_lang must be a string"
            )

        if not self.ui_lang.strip():
            raise ValueError(
                "ui_lang must not be empty"
            )

        if self.safesearch not in {
            "off",
            "moderate",
            "strict",
        }:
            raise ValueError(
                "invalid safesearch value"
            )

        if (
            not isinstance(
                self.user_agent,
                str,
            )
            or not self.user_agent.strip()
        ):
            raise ValueError(
                "user_agent must be non-empty"
            )


class BraveSearchBackend(SearchProviderBackend):
    """
    Concrete Brave Search API adapter.

    This class performs search only.
    It does not perform research ingestion,
    verification, permission decisions,
    or knowledge creation.

    The API key must be supplied by the caller.
    It is never stored in the URL.
    """

    backend_name = "brave_search"

    API_KEY_HEADER = "X-Subscription-Token"

    def __init__(
        self,
        api_key: str,
        *,
        config: Optional[BraveSearchConfig] = None,
    ):
        if (
            not isinstance(api_key, str)
            or not api_key.strip()
        ):
            raise ValueError(
                "api_key must be a non-empty string"
            )

        self.api_key = api_key.strip()

        self.config = (
            config
            if config is not None
            else BraveSearchConfig()
        )

        if not isinstance(
            self.config,
            BraveSearchConfig,
        ):
            raise TypeError(
                "config must be BraveSearchConfig"
            )
    @classmethod
    def from_credential_store(
        cls,
        credential_store: CredentialStore | None = None,
        *,
        config: Optional[BraveSearchConfig] = None,
    ) -> "BraveSearchBackend":
        store = (
            credential_store
            if credential_store is not None
            else CredentialStore()
        )

        if not isinstance(store, CredentialStore):
            raise TypeError(
                "credential_store must be CredentialStore"
            )

        api_key = store.require_credential("brave")

        return cls(
            api_key,
            config=config,
        )


    def _build_url(
        self,
        query: str,
        max_results: int,
    ) -> str:
        params = {
            "q": query,
            "count": str(
                min(max_results, 20)
            ),
            "country": self.config.country,
            "search_lang": (
                self.config.search_lang
            ),
            "ui_lang": self.config.ui_lang,
            "safesearch": (
                self.config.safesearch
            ),
            "spellcheck": (
                "true"
                if self.config.spellcheck
                else "false"
            ),
        }

        return (
            self.config.endpoint
            + "?"
            + urllib.parse.urlencode(params)
        )

    @staticmethod
    def _read_limited(
        response,
        max_bytes: int,
    ) -> bytes:
        content_length = response.headers.get(
            "Content-Length"
        )

        if content_length:
            try:
                declared_size = int(
                    content_length
                )
            except ValueError as exc:
                raise ValueError(
                    "invalid Content-Length header"
                ) from exc

            if declared_size > max_bytes:
                raise ValueError(
                    "HTTP response exceeds "
                    "configured size limit"
                )

        chunks: list[bytes] = []
        total = 0

        while True:
            remaining = max_bytes - total

            if remaining <= 0:
                raise ValueError(
                    "HTTP response exceeds "
                    "configured size limit"
                )

            chunk = response.read(
                min(
                    64 * 1024,
                    remaining + 1,
                )
            )

            if not chunk:
                break

            total += len(chunk)

            if total > max_bytes:
                raise ValueError(
                    "HTTP response exceeds "
                    "configured size limit"
                )

            chunks.append(chunk)

        return b"".join(chunks)

    def _request_json(
        self,
        query: str,
        max_results: int,
    ) -> Any:
        url = self._build_url(
            query,
            max_results,
        )

        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": (
                    self.config.user_agent
                ),
                self.API_KEY_HEADER: (
                    self.api_key
                ),
            },
            method="GET",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=(
                    self.config.timeout_seconds
                ),
            ) as response:

                status = getattr(
                    response,
                    "status",
                    200,
                )

                if status < 200 or status >= 300:
                    raise RuntimeError(
                        "Brave Search API returned "
                        f"HTTP status {status}"
                    )

                content_type = response.headers.get(
                    "Content-Type",
                    "",
                ).lower()

                if (
                    content_type
                    and "application/json"
                    not in content_type
                ):
                    raise ValueError(
                        "Brave Search API did not "
                        "return application/json"
                    )

                payload = self._read_limited(
                    response,
                    self.config.max_response_bytes,
                )

        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403}:
                raise PermissionError(
                    "Brave Search API "
                    "authentication failed"
                ) from exc

            raise RuntimeError(
                "Brave Search API returned "
                f"HTTP status {exc.code}"
            ) from exc

        except urllib.error.URLError as exc:
            raise RuntimeError(
                "Brave Search API request failed: "
                f"{exc.reason}"
            ) from exc

        try:
            return json.loads(
                payload.decode("utf-8")
            )

        except UnicodeDecodeError as exc:
            raise ValueError(
                "Brave Search API response is "
                "not valid UTF-8"
            ) from exc

        except json.JSONDecodeError as exc:
            raise ValueError(
                "Brave Search API response is "
                "not valid JSON"
            ) from exc

    @staticmethod
    def _web_results(
        payload: Any,
    ) -> list[dict[str, Any]]:
        if not isinstance(payload, dict):
            raise ValueError(
                "Brave response must be a JSON object"
            )

        web = payload.get("web")

        if not isinstance(web, dict):
            raise ValueError(
                "Brave response missing web object"
            )

        results = web.get("results")

        if not isinstance(results, list):
            raise ValueError(
                "Brave web.results must be a list"
            )

        return results

    @staticmethod
    def _optional_string(
        item: dict[str, Any],
        key: str,
    ) -> Optional[str]:
        value = item.get(key)

        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(
                f"Brave field '{key}' must be "
                "a string when present"
            )

        return value.strip() or None

    def _map_result(
        self,
        item: Any,
        rank: int,
    ) -> SearchResult:
        if not isinstance(item, dict):
            raise ValueError(
                "Brave search result must "
                "be a JSON object"
            )

        title = item.get("title")
        url = item.get("url")
        description = item.get(
            "description",
            "",
        )

        if (
            not isinstance(title, str)
            or not title.strip()
        ):
            raise ValueError(
                "Brave search result title "
                "is invalid"
            )

        if (
            not isinstance(url, str)
            or not url.strip()
        ):
            raise ValueError(
                "Brave search result URL "
                "is invalid"
            )

        if not isinstance(
            description,
            str,
        ):
            raise ValueError(
                "Brave description must "
                "be a string"
            )

        return SearchResult(
            title=title.strip(),
            url=url.strip(),
            snippet=description.strip(),
            publisher=self._optional_string(
                item,
                "profile",
            ),
            author=None,
            published_at=(
                self._optional_string(
                    item,
                    "page_age",
                )
            ),
            rank=rank,
            metadata={
                "backend": self.backend_name,
                "provider": "brave",
            },
        )

    def search(
        self,
        query: str,
        *,
        max_results: int,
    ) -> list[SearchResult]:
        if (
            not isinstance(query, str)
            or not query.strip()
        ):
            raise ValueError(
                "query must be a non-empty string"
            )

        if (
            not isinstance(max_results, int)
            or max_results <= 0
        ):
            raise ValueError(
                "max_results must be a "
                "positive integer"
            )

        if len(query.strip()) > 600:
            raise ValueError(
                "query exceeds Brave's "
                "600-character limit"
            )

        capped_results = min(
            max_results,
            20,
        )

        payload = self._request_json(
            query.strip(),
            capped_results,
        )

        raw_results = self._web_results(
            payload
        )

        results: list[SearchResult] = []

        for item in raw_results[
            :capped_results
        ]:
            results.append(
                self._map_result(
                    item,
                    len(results) + 1,
                )
            )

        return results
