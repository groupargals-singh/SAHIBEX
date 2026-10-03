from __future__ import annotations

import hashlib
import ipaddress
import json
import socket
import urllib.error
import urllib.parse
import urllib.request

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from core.research.acquisition import (
    AcquiredSource,
    AcquisitionRequest,
    AcquisitionResult,
    ResearchAcquisitionProvider,
)


@dataclass(frozen=True)
class RESTJSONProviderConfig:
    timeout_seconds: float = 15.0
    max_response_bytes: int = 2_000_000
    max_sources: int = 10
    user_agent: str = "SAHIBEX-Research-API/0.1"
    allow_http: bool = True
    allow_https: bool = True
    allow_private_hosts: bool = False
    allow_redirects: bool = False
    default_content_type: str = "application/json"

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be greater than zero"
            )

        if self.max_response_bytes <= 0:
            raise ValueError(
                "max_response_bytes must be greater than zero"
            )

        if self.max_sources <= 0:
            raise ValueError(
                "max_sources must be greater than zero"
            )

        if (
            not isinstance(self.user_agent, str)
            or not self.user_agent.strip()
        ):
            raise ValueError(
                "user_agent cannot be empty"
            )

        if not isinstance(self.allow_http, bool):
            raise TypeError(
                "allow_http must be bool"
            )

        if not isinstance(self.allow_https, bool):
            raise TypeError(
                "allow_https must be bool"
            )

        if not isinstance(
            self.allow_private_hosts,
            bool,
        ):
            raise TypeError(
                "allow_private_hosts must be bool"
            )

        if not isinstance(
            self.allow_redirects,
            bool,
        ):
            raise TypeError(
                "allow_redirects must be bool"
            )

        if (
            not isinstance(
                self.default_content_type,
                str,
            )
            or not self.default_content_type.strip()
        ):
            raise ValueError(
                "default_content_type cannot be empty"
            )


class _NoRedirectHandler(
    urllib.request.HTTPRedirectHandler
):
    def redirect_request(
        self,
        req,
        fp,
        code,
        msg,
        headers,
        newurl,
    ):
        return None


class RESTJSONResearchProvider(
    ResearchAcquisitionProvider
):
    """
    Generic REST/JSON research acquisition provider.

    Network access is protected by the existing
    ResearchAcquisitionPipeline permission boundary.

    The provider itself does not grant permission.
    """

    provider_name = "rest_json_api"
    requires_network = True

    ALLOWED_JSON_CONTENT_TYPES = {
        "application/json",
        "application/json; charset=utf-8",
        "application/problem+json",
        "application/vnd.api+json",
        "text/json",
    }

    def __init__(
        self,
        config: Optional[
            RESTJSONProviderConfig
        ] = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else RESTJSONProviderConfig()
        )

        if self.config.allow_redirects:
            raise ValueError(
                "automatic redirects are not supported "
                "by the secure REST/JSON provider"
            )

        self._opener = urllib.request.build_opener(
            _NoRedirectHandler()
        )

    # ---------------------------------------------------------
    # URL / SSRF security
    # ---------------------------------------------------------

    @staticmethod
    def _is_unsafe_ip(
        address: str,
    ) -> bool:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return True

        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )

    def _validate_hostname(
        self,
        hostname: str,
    ) -> None:
        normalized = hostname.strip().lower()

        if not normalized:
            raise ValueError(
                "URL hostname cannot be empty"
            )

        if self.config.allow_private_hosts:
            return

        if normalized in {
            "localhost",
            "localhost.localdomain",
        }:
            raise ValueError(
                "localhost and private/local hosts are blocked"
            )

        try:
            direct_ip = ipaddress.ip_address(
                normalized
            )
        except ValueError:
            direct_ip = None

        if direct_ip is not None:
            if self._is_unsafe_ip(
                str(direct_ip)
            ):
                raise ValueError(
                    "private/reserved IP addresses "
                    "are blocked"
                )

            return

        try:
            addresses = socket.getaddrinfo(
                normalized,
                None,
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise ValueError(
                "hostname resolution failed"
            ) from exc

        if not addresses:
            raise ValueError(
                "hostname resolution returned no addresses"
            )

        for address_info in addresses:
            resolved = address_info[4][0]

            if self._is_unsafe_ip(
                resolved
            ):
                raise ValueError(
                    "hostname resolves to a "
                    "private/reserved address"
                )

    def _validate_url(
        self,
        url: str,
    ) -> str:
        if not isinstance(url, str):
            raise ValueError(
                "URL must be a string"
            )

        normalized = url.strip()

        if not normalized:
            raise ValueError(
                "URL cannot be empty"
            )

        parsed = urllib.parse.urlparse(
            normalized
        )

        if parsed.scheme not in {
            "http",
            "https",
        }:
            raise ValueError(
                "only HTTP/HTTPS URLs are allowed"
            )

        if (
            parsed.scheme == "http"
            and not self.config.allow_http
        ):
            raise ValueError(
                "HTTP URLs are disabled"
            )

        if (
            parsed.scheme == "https"
            and not self.config.allow_https
        ):
            raise ValueError(
                "HTTPS URLs are disabled"
            )

        if not parsed.hostname:
            raise ValueError(
                "URL hostname cannot be empty"
            )

        if (
            parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError(
                "credentials in URL are not allowed"
            )

        self._validate_hostname(
            parsed.hostname
        )

        return normalized

    # ---------------------------------------------------------
    # HTTP helpers
    # ---------------------------------------------------------

    @staticmethod
    def _content_type(
        headers,
    ) -> str:
        value = (
            headers.get(
                "Content-Type",
                "",
            )
            or ""
        )

        return value.split(
            ";",
            1,
        )[0].strip().lower()

    def _read_limited(
        self,
        response,
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
                    "invalid Content-Length"
                ) from exc

            if (
                declared_size
                > self.config.max_response_bytes
            ):
                raise ValueError(
                    "API response exceeds "
                    "maximum allowed size"
                )

        chunks: list[bytes] = []
        total = 0

        while True:
            chunk = response.read(
                min(
                    64 * 1024,
                    self.config.max_response_bytes
                    - total,
                )
            )

            if not chunk:
                break

            chunks.append(chunk)
            total += len(chunk)

            if (
                total
                >= self.config.max_response_bytes
            ):
                extra = response.read(1)

                if extra:
                    raise ValueError(
                        "API response exceeds "
                        "maximum allowed size"
                    )

                break

        return b"".join(chunks)

    def _request_json(
        self,
        url: str,
        *,
        headers: Optional[dict[str, str]] = None,
    ) -> tuple[Any, dict[str, Any]]:
        validated_url = self._validate_url(
            url
        )

        request_headers = {
            "User-Agent": self.config.user_agent,
            "Accept": (
                "application/json, "
                "application/problem+json, "
                "application/vnd.api+json"
            ),
        }

        if headers:
            for key, value in headers.items():
                if not isinstance(key, str):
                    raise ValueError(
                        "API header names must be strings"
                    )

                if not isinstance(value, str):
                    raise ValueError(
                        "API header values must be strings"
                    )

                if not key.strip():
                    raise ValueError(
                        "API header name cannot be empty"
                    )

                request_headers[key] = value

        request = urllib.request.Request(
            url=validated_url,
            method="GET",
            headers=request_headers,
        )

        try:
            response = self._opener.open(
                request,
                timeout=self.config.timeout_seconds,
            )

            try:
                content_type = self._content_type(
                    response.headers
                )

                if (
                    content_type
                    not in self.ALLOWED_JSON_CONTENT_TYPES
                ):
                    raise ValueError(
                        "unsupported API content type: "
                        f"{content_type or 'unknown'}"
                    )

                payload = self._read_limited(
                    response
                )

                status = getattr(
                    response,
                    "status",
                    200,
                )

                final_url = response.geturl()

            finally:
                response.close()

        except urllib.error.HTTPError as exc:
            if exc.code in {
                301,
                302,
                303,
                307,
                308,
            }:
                raise RuntimeError(
                    f"HTTP {exc.code}: "
                    "redirects are not allowed"
                ) from exc

            raise RuntimeError(
                f"API request failed with HTTP "
                f"{exc.code}"
            ) from exc

        except urllib.error.URLError as exc:
            raise RuntimeError(
                "API request failed: "
                f"{exc.reason}"
            ) from exc

        except TimeoutError as exc:
            raise RuntimeError(
                "API request timed out"
            ) from exc

        try:
            decoded = payload.decode(
                "utf-8"
            )
        except UnicodeDecodeError as exc:
            raise ValueError(
                "API response is not valid UTF-8 JSON"
            ) from exc

        try:
            data = json.loads(
                decoded
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "API response is not valid JSON"
            ) from exc

        return (
            data,
            {
                "url": validated_url,
                "final_url": final_url,
                "status": status,
                "content_type": content_type,
                "bytes": len(payload),
            },
        )

    # ---------------------------------------------------------
    # JSON extraction
    # ---------------------------------------------------------

    @staticmethod
    def _path_value(
        data: Any,
        path: Optional[str],
    ) -> Any:
        if path is None:
            return data

        if not isinstance(path, str):
            raise ValueError(
                "JSON result path must be a string or None"
            )

        normalized = path.strip()

        if not normalized:
            return data

        current = data

        for part in normalized.split("."):
            if isinstance(current, dict):
                if part not in current:
                    return None

                current = current[part]

            elif isinstance(current, list):
                try:
                    index = int(part)
                except ValueError:
                    return None

                if index < 0 or index >= len(current):
                    return None

                current = current[index]

            else:
                return None

        return current

    @staticmethod
    def _string_value(
        value: Any,
        default: str = "",
    ) -> str:
        if value is None:
            return default

        if isinstance(value, str):
            return value.strip()

        if isinstance(value, (int, float, bool)):
            return str(value)

        return default

    @staticmethod
    def _stable_source_id(
        locator: str,
        content: str,
    ) -> str:
        material = (
            locator.strip()
            + "\n"
            + content
        )

        digest = hashlib.sha256(
            material.encode("utf-8")
        ).hexdigest()

        return f"api_{digest}"

    def _build_source(
        self,
        item: Any,
        *,
        api_url: str,
        metadata: dict[str, Any],
        index: int,
    ) -> Optional[AcquiredSource]:
        if not isinstance(item, dict):
            return None

        title_path = metadata.get(
            "title_path",
            "title",
        )

        locator_path = metadata.get(
            "locator_path",
            "url",
        )

        content_path = metadata.get(
            "content_path",
            "content",
        )

        author_path = metadata.get(
            "author_path",
            "author",
        )

        published_path = metadata.get(
            "published_at_path",
            "published_at",
        )

        title = self._string_value(
            self._path_value(
                item,
                title_path,
            )
        )

        locator = self._string_value(
            self._path_value(
                item,
                locator_path,
            )
        )

        content = self._string_value(
            self._path_value(
                item,
                content_path,
            )
        )

        author = self._string_value(
            self._path_value(
                item,
                author_path,
            )
        )

        published_at = self._string_value(
            self._path_value(
                item,
                published_path,
            )
        )

        if not title:
            title = (
                f"API result {index + 1}"
            )

        if not locator:
            locator = api_url

        if not content:
            content = (
                json.dumps(
                    item,
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )

        if not content.strip():
            return None

        source_id = self._stable_source_id(
            locator,
            content,
        )

        acquired_at = datetime.now(
            timezone.utc
        ).isoformat()

        source_metadata = {
            "provider": self.__class__.__name__,
            "provider_name": self.provider_name,
            "api_url": api_url,
            "acquired_at": acquired_at,
            "result_index": index,
            "content_type": metadata.get(
                "_content_type",
                self.config.default_content_type,
            ),
            "http_status": metadata.get(
                "_http_status",
                200,
            ),
            "content_bytes": metadata.get(
                "_content_bytes",
                0,
            ),
            "requested_url": metadata.get(
                "_requested_url",
                api_url,
            ),
            "final_url": metadata.get(
                "_final_url",
                api_url,
            ),
            "discovery_only": True,
            "content_is_api_result": True,
            "reliability": 0.5,
        }

        return AcquiredSource(
            source_id=source_id,
            title=title,
            source_type="api",
            locator=locator,
            author=author or None,
            published_at=published_at or None,
            content=content,
            metadata=source_metadata,
        )

    # ---------------------------------------------------------
    # Acquisition contract
    # ---------------------------------------------------------

    def acquire(
        self,
        request: AcquisitionRequest,
    ) -> AcquisitionResult:
        if not isinstance(
            request,
            AcquisitionRequest,
        ):
            raise TypeError(
                "request must be an AcquisitionRequest"
            )

        metadata = request.metadata or {}

        urls = metadata.get(
            "urls"
        )

        if urls is None:
            url = metadata.get(
                "url"
            )

            if url is None:
                raise ValueError(
                    "REST/JSON API acquisition requires "
                    "request.metadata['url'] or "
                    "request.metadata['urls']"
                )

            urls = [url]

        if not isinstance(
            urls,
            (list, tuple),
        ):
            raise ValueError(
                "metadata['urls'] must be a list or tuple"
            )

        if not urls:
            raise ValueError(
                "metadata['urls'] cannot be empty"
            )

        result_path = metadata.get(
            "results_path",
            None,
        )

        headers = metadata.get(
            "headers",
            {},
        )

        if not isinstance(
            headers,
            dict,
        ):
            raise ValueError(
                "metadata['headers'] must be a dictionary"
            )

        limit = min(
            request.max_sources,
            self.config.max_sources,
        )

        acquired: list[AcquiredSource] = []
        errors: list[str] = []
        seen_source_ids: set[str] = set()
        seen_urls: set[str] = set()

        for raw_url in urls:
            if len(acquired) >= limit:
                break

            if not isinstance(
                raw_url,
                str,
            ):
                errors.append(
                    "URL must be a string"
                )
                continue

            normalized_url = raw_url.strip()

            if not normalized_url:
                errors.append(
                    "URL cannot be empty"
                )
                continue

            if normalized_url in seen_urls:
                continue

            seen_urls.add(
                normalized_url
            )

            try:
                data, response_metadata = (
                    self._request_json(
                        normalized_url,
                        headers=headers,
                    )
                )

                results = self._path_value(
                    data,
                    result_path,
                )

                if results is None:
                    raise ValueError(
                        "configured results_path "
                        "was not found"
                    )

                if isinstance(results, dict):
                    results = [results]

                if not isinstance(
                    results,
                    list,
                ):
                    raise ValueError(
                        "configured results_path "
                        "must resolve to a list "
                        "or object"
                    )

                source_metadata = dict(
                    metadata
                )

                source_metadata.update(
                    {
                        "_content_type": (
                            response_metadata[
                                "content_type"
                            ]
                        ),
                        "_http_status": (
                            response_metadata[
                                "status"
                            ]
                        ),
                        "_content_bytes": (
                            response_metadata[
                                "bytes"
                            ]
                        ),
                        "_requested_url": (
                            response_metadata[
                                "url"
                            ]
                        ),
                        "_final_url": (
                            response_metadata[
                                "final_url"
                            ]
                        ),
                    }
                )

                for index, item in enumerate(
                    results
                ):
                    if len(acquired) >= limit:
                        break

                    source = self._build_source(
                        item,
                        api_url=normalized_url,
                        metadata=source_metadata,
                        index=index,
                    )

                    if source is None:
                        continue

                    if (
                        source.source_id
                        in seen_source_ids
                    ):
                        continue

                    seen_source_ids.add(
                        source.source_id
                    )

                    acquired.append(
                        source
                    )

            except (
                ValueError,
                RuntimeError,
            ) as exc:
                errors.append(
                    f"{normalized_url}: {exc}"
                )

        if acquired:
            status = (
                "completed"
                if not errors
                else "partial"
            )
            completed = True
        else:
            status = "failed"
            completed = False

        return AcquisitionResult(
            query=request.query,
            sources=acquired,
            completed=completed,
            status=status,
            metadata={
                "provider": self.provider_name,
                "network_capable": (
                    self.requires_network
                ),
                "requested_sources": len(
                    seen_urls
                ),
                "acquired_sources": len(
                    acquired
                ),
                "errors": errors,
            },
        )
