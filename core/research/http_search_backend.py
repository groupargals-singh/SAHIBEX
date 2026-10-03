from __future__ import annotations

import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from core.research.search_provider import (
    SearchProviderBackend,
    SearchResult,
)


@dataclass(frozen=True)
class HTTPJsonSearchConfig:
    endpoint: str
    query_parameter: str = "q"
    results_path: tuple[str, ...] = ("results",)

    title_field: str = "title"
    url_field: str = "url"
    snippet_field: str = "snippet"

    publisher_field: Optional[str] = "publisher"
    author_field: Optional[str] = "author"
    published_at_field: Optional[str] = "published_at"

    timeout_seconds: float = 10.0
    max_response_bytes: int = 1_000_000

    user_agent: str = "SAHIBEX-Research-Search/0.1"

    allow_http: bool = False
    allow_https: bool = True

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

        if parsed.scheme not in {"http", "https"}:
            raise ValueError(
                "endpoint must use http or https"
            )

        if not parsed.hostname:
            raise ValueError(
                "endpoint must contain a hostname"
            )

        if parsed.username or parsed.password:
            raise ValueError(
                "endpoint must not contain credentials"
            )

        if (
            parsed.scheme == "http"
            and not self.allow_http
        ):
            raise ValueError(
                "HTTP endpoint is disabled"
            )

        if (
            parsed.scheme == "https"
            and not self.allow_https
        ):
            raise ValueError(
                "HTTPS endpoint is disabled"
            )

        if (
            not isinstance(self.query_parameter, str)
            or not self.query_parameter
        ):
            raise ValueError(
                "query_parameter must be non-empty"
            )

        if not isinstance(
            self.results_path,
            tuple,
        ):
            raise ValueError(
                "results_path must be a tuple"
            )

        if self.timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be positive"
            )

        if self.max_response_bytes <= 0:
            raise ValueError(
                "max_response_bytes must be positive"
            )

        if (
            not isinstance(self.user_agent, str)
            or not self.user_agent.strip()
        ):
            raise ValueError(
                "user_agent must be non-empty"
            )


class HTTPJsonSearchBackend(SearchProviderBackend):
    backend_name = "http_json"

    SENSITIVE_HEADER_NAMES = {
        "authorization",
        "proxy-authorization",
        "x-api-key",
        "api-key",
        "apikey",
        "x-auth-token",
        "x-access-token",
    }

    def __init__(
        self,
        config: HTTPJsonSearchConfig,
        *,
        headers: Optional[Mapping[str, str]] = None,
    ):
        if not isinstance(
            config,
            HTTPJsonSearchConfig,
        ):
            raise TypeError(
                "config must be HTTPJsonSearchConfig"
            )

        self.config = config
        self.headers = dict(headers or {})

        for key, value in self.headers.items():
            if (
                not isinstance(key, str)
                or not key
            ):
                raise ValueError(
                    "header names must be "
                    "non-empty strings"
                )

            if not isinstance(value, str):
                raise ValueError(
                    "header values must be strings"
                )

    def _build_url(
        self,
        query: str,
        max_results: int,
    ) -> str:
        parsed = urllib.parse.urlparse(
            self.config.endpoint
        )

        query_values = urllib.parse.parse_qs(
            parsed.query,
            keep_blank_values=True,
        )

        query_values[
            self.config.query_parameter
        ] = [query]

        query_values["limit"] = [
            str(max_results)
        ]

        encoded_query = urllib.parse.urlencode(
            query_values,
            doseq=True,
        )

        return urllib.parse.urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                encoded_query,
                parsed.fragment,
            )
        )

    @staticmethod
    def _redact_url(url: str) -> str:
        parsed = urllib.parse.urlparse(url)

        sensitive_query_keys = {
            "api_key",
            "apikey",
            "key",
            "token",
            "access_token",
            "auth",
            "authorization",
        }

        safe_query_parts: list[str] = []

        for key, value in urllib.parse.parse_qsl(
            parsed.query,
            keep_blank_values=True,
        ):
            encoded_key = urllib.parse.quote_plus(
                key
            )

            if key.lower() in sensitive_query_keys:
                safe_query_parts.append(
                    f"{encoded_key}=[REDACTED]"
                )
            else:
                encoded_value = (
                    urllib.parse.quote_plus(
                        value
                    )
                )

                safe_query_parts.append(
                    f"{encoded_key}="
                    f"{encoded_value}"
                )

        redacted_query = "&".join(
            safe_query_parts
        )

        return urllib.parse.urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                redacted_query,
                "",
            )
        )

    @classmethod
    def _redact_headers(
        cls,
        headers: Mapping[str, str],
    ) -> dict[str, str]:
        redacted: dict[str, str] = {}

        for key, value in headers.items():
            if (
                key.lower()
                in cls.SENSITIVE_HEADER_NAMES
            ):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = value

        return redacted

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

        request_headers = {
            "Accept": "application/json",
            "User-Agent": self.config.user_agent,
        }

        request_headers.update(
            self.headers
        )

        request = urllib.request.Request(
            url,
            headers=request_headers,
            method="GET",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.config.timeout_seconds,
            ) as response:

                status = getattr(
                    response,
                    "status",
                    200,
                )

                if status < 200 or status >= 300:
                    raise RuntimeError(
                        "search API returned "
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
                        "search API did not return "
                        "application/json"
                    )

                payload = self._read_limited(
                    response,
                    self.config.max_response_bytes,
                )

        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                "search API returned "
                f"HTTP status {exc.code}"
            ) from exc

        except urllib.error.URLError as exc:
            reason = str(exc.reason)

            raise RuntimeError(
                "search API request failed: "
                f"{reason}"
            ) from exc

        except socket.timeout as exc:
            raise TimeoutError(
                "search API request timed out"
            ) from exc

        try:
            return json.loads(
                payload.decode("utf-8")
            )

        except UnicodeDecodeError as exc:
            raise ValueError(
                "search API response is not "
                "valid UTF-8"
            ) from exc

        except json.JSONDecodeError as exc:
            raise ValueError(
                "search API response is not "
                "valid JSON"
            ) from exc

    @staticmethod
    def _get_path(
        payload: Any,
        path: Sequence[str],
    ) -> Any:
        current = payload

        for key in path:
            if not isinstance(
                current,
                dict,
            ):
                raise ValueError(
                    "configured results path "
                    "does not match JSON structure"
                )

            if key not in current:
                raise ValueError(
                    "configured results path "
                    f"missing key: {key}"
                )

            current = current[key]

        return current

    @staticmethod
    def _optional_string(
        item: Mapping[str, Any],
        field: Optional[str],
    ) -> Optional[str]:
        if field is None:
            return None

        value = item.get(field)

        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(
                f"search result field "
                f"'{field}' must be a string"
            )

        return value

    def _map_result(
        self,
        item: Any,
        rank: int,
    ) -> SearchResult:
        if not isinstance(item, dict):
            raise ValueError(
                "each search result must be "
                "a JSON object"
            )

        title = item.get(
            self.config.title_field
        )

        url = item.get(
            self.config.url_field
        )

        snippet = item.get(
            self.config.snippet_field,
            "",
        )

        if (
            not isinstance(title, str)
            or not title.strip()
        ):
            raise ValueError(
                "search result title is invalid"
            )

        if (
            not isinstance(url, str)
            or not url.strip()
        ):
            raise ValueError(
                "search result URL is invalid"
            )

        if not isinstance(snippet, str):
            raise ValueError(
                "search result snippet is invalid"
            )

        return SearchResult(
            title=title.strip(),
            url=url.strip(),
            snippet=snippet.strip(),
            publisher=self._optional_string(
                item,
                self.config.publisher_field,
            ),
            author=self._optional_string(
                item,
                self.config.author_field,
            ),
            published_at=self._optional_string(
                item,
                self.config.published_at_field,
            ),
            rank=rank,
            metadata={
                "backend": self.backend_name
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
                "max_results must be "
                "a positive integer"
            )

        capped_results = min(
            max_results,
            100,
        )

        payload = self._request_json(
            query.strip(),
            capped_results,
        )

        raw_results = self._get_path(
            payload,
            self.config.results_path,
        )

        if not isinstance(
            raw_results,
            list,
        ):
            raise ValueError(
                "configured results path must "
                "contain a list"
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
