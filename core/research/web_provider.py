from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import html
import ipaddress
import re
import socket
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import (
    Request,
    HTTPRedirectHandler,
    build_opener,
)


from core.research.acquisition import (
    AcquisitionRequest,
    AcquisitionResult,
    AcquiredSource,
    ResearchAcquisitionProvider,
)


@dataclass(frozen=True)
class WebProviderConfig:
    timeout_seconds: float = 15.0
    max_response_bytes: int = 2_000_000
    max_sources: int = 10
    user_agent: str = "SAHIBEX-Research/0.1"
    allow_http: bool = True
    allow_https: bool = True
    allow_redirects: bool = False

    def __post_init__(self):
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

        if not self.user_agent.strip():
            raise ValueError(
                "user_agent cannot be empty"
            )


class _NoRedirectHandler(HTTPRedirectHandler):
    """
    Prevent automatic redirects.

    Redirects are intentionally disabled by default so a server
    cannot silently redirect the research request to an unexpected
    host or private address.
    """

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


class DirectWebResearchProvider(
    ResearchAcquisitionProvider
):
    """
    Secure direct HTTP/HTTPS research acquisition provider.

    This provider performs network access.

    Therefore:
        requires_network = True

    IMPORTANT:
    The provider itself does not grant permission.

    ResearchAcquisitionPipeline must perform the existing
    NETWORK_ACCESS permission check before this provider is called.
    """

    provider_name = "direct_web"
    requires_network = True

    ALLOWED_CONTENT_TYPES = {
        "text/html",
        "text/plain",
        "application/xhtml+xml",
    }

    def __init__(
        self,
        config: WebProviderConfig | None = None,
    ):
        self.config = (
            config
            if config is not None
            else WebProviderConfig()
        )

        if self.config.allow_redirects:
            raise ValueError(
                "automatic redirects are not supported by the "
                "secure direct web provider"
            )

        self._opener = build_opener(
            _NoRedirectHandler()
        )

    # ---------------------------------------------------------
    # URL validation
    # ---------------------------------------------------------

    def _validate_url(
        self,
        url: str,
    ) -> None:
        if not isinstance(url, str):
            raise ValueError(
                "URL must be a string"
            )

        url = url.strip()

        if not url:
            raise ValueError(
                "URL cannot be empty"
            )

        parsed = urlparse(url)

        if parsed.scheme not in {
            "http",
            "https",
        }:
            raise ValueError(
                "only http and https URLs are allowed"
            )

        if parsed.scheme == "http" and not self.config.allow_http:
            raise ValueError(
                "HTTP URLs are disabled"
            )

        if parsed.scheme == "https" and not self.config.allow_https:
            raise ValueError(
                "HTTPS URLs are disabled"
            )

        if not parsed.hostname:
            raise ValueError(
                "URL hostname is required"
            )

        if parsed.username or parsed.password:
            raise ValueError(
                "URLs containing credentials are not allowed"
            )

        self._validate_hostname(
            parsed.hostname
        )

    # ---------------------------------------------------------
    # SSRF protection
    # ---------------------------------------------------------

    @staticmethod
    def _is_unsafe_ip(
        address: str,
    ) -> bool:
        ip = ipaddress.ip_address(
            address
        )

        return any(
            (
                ip.is_private,
                ip.is_loopback,
                ip.is_link_local,
                ip.is_multicast,
                ip.is_reserved,
                ip.is_unspecified,
            )
        )

    def _validate_hostname(
        self,
        hostname: str,
    ) -> None:
        hostname = hostname.strip().lower()

        if hostname in {
            "localhost",
            "localhost.localdomain",
        }:
            raise ValueError(
                "localhost is not allowed"
            )

        try:
            ip = ipaddress.ip_address(
                hostname
            )
        except ValueError:
            ip = None

        if ip is not None:
            if self._is_unsafe_ip(
                str(ip)
            ):
                raise ValueError(
                    "private or reserved IP addresses are not allowed"
                )

            return

        try:
            addresses = socket.getaddrinfo(
                hostname,
                None,
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise ValueError(
                f"hostname resolution failed: {hostname}"
            ) from exc

        if not addresses:
            raise ValueError(
                f"hostname has no resolved address: {hostname}"
            )

        for address_info in addresses:
            resolved = address_info[4][0]

            if self._is_unsafe_ip(
                resolved
            ):
                raise ValueError(
                    "hostname resolves to a private or reserved "
                    f"IP address: {resolved}"
                )

    # ---------------------------------------------------------
    # Response helpers
    # ---------------------------------------------------------

    @staticmethod
    def _content_type(
        headers,
    ) -> str:
        value = headers.get(
            "Content-Type",
            "",
        )

        if not value:
            return ""

        return value.split(
            ";",
            1,
        )[0].strip().lower()

    @staticmethod
    def _extract_title(
        content: str,
    ) -> str:
        match = re.search(
            r"<title\b[^>]*>(.*?)</title\s*>",
            content,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if not match:
            return "Untitled web document"

        title = re.sub(
            r"\s+",
            " ",
            match.group(1),
        ).strip()

        title = html.unescape(
            title
        )

        if not title:
            return "Untitled web document"

        return title[:1000]

    @staticmethod
    def _decode_content(
        payload: bytes,
        headers,
    ) -> str:
        charset = headers.get_content_charset()

        if charset:
            try:
                return payload.decode(
                    charset,
                    errors="replace",
                )
            except LookupError:
                pass

        return payload.decode(
            "utf-8",
            errors="replace",
        )

    # ---------------------------------------------------------
    # Fetch
    # ---------------------------------------------------------

    def fetch_url(
        self,
        url: str,
    ) -> dict:
        """
        Fetch one URL.

        This method performs network access and therefore MUST
        only be called after the SAHIBEX permission boundary has
        approved NETWORK_ACCESS.
        """

        self._validate_url(
            url
        )

        request = Request(
            url=url,
            method="GET",
            headers={
                "User-Agent": self.config.user_agent,
                "Accept": (
                    "text/html, "
                    "application/xhtml+xml, "
                    "text/plain;q=0.9, "
                    "*/*;q=0.1"
                ),
            },
        )

        try:
            response = self._opener.open(
                request,
                timeout=self.config.timeout_seconds,
            )

        except HTTPError as exc:
            raise RuntimeError(
                f"web request failed with HTTP {exc.code}"
            ) from exc

        except URLError as exc:
            raise RuntimeError(
                f"web request failed: {exc.reason}"
            ) from exc

        except TimeoutError as exc:
            raise RuntimeError(
                "web request timed out"
            ) from exc

        content_type = self._content_type(
            response.headers
        )

        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValueError(
                "unsupported web content type: "
                f"{content_type or 'unknown'}"
            )

        content_length = response.headers.get(
            "Content-Length"
        )

        if content_length:
            try:
                declared_size = int(
                    content_length
                )
            except ValueError:
                declared_size = None

            if (
                declared_size is not None
                and declared_size > self.config.max_response_bytes
            ):
                raise ValueError(
                    "web response exceeds maximum allowed size"
                )

        chunks = []
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

            chunks.append(
                chunk
            )

            total += len(chunk)

            if total >= self.config.max_response_bytes:
                extra = response.read(
                    1
                )

                if extra:
                    raise ValueError(
                        "web response exceeds maximum allowed size"
                    )

                break

        payload = b"".join(
            chunks
        )

        content = self._decode_content(
            payload,
            response.headers,
        )

        return {
            "url": url,
            "final_url": response.geturl(),
            "status": getattr(
                response,
                "status",
                200,
            ),
            "content_type": content_type,
            "content": content,
            "bytes": len(payload),
        }

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

        urls = request.metadata.get(
            "urls"
        )

        if urls is None:
            url = request.metadata.get(
                "url"
            )

            if url:
                urls = [url]

        if not isinstance(
            urls,
            (list, tuple),
        ):
            raise ValueError(
                "direct_web provider requires request.metadata['url'] "
                "or request.metadata['urls']"
            )

        max_sources = min(
            request.max_sources,
            self.config.max_sources,
        )

        acquired = []

        errors = []

        for raw_url in urls[:max_sources]:

            if not isinstance(
                raw_url,
                str,
            ):
                errors.append(
                    "URL must be a string"
                )
                continue

            try:
                fetched = self.fetch_url(
                    raw_url
                )

                content = fetched["content"]

                if not content.strip():
                    errors.append(
                        f"empty response: {raw_url}"
                    )
                    continue

                content_hash = hashlib.sha256(
                    content.encode(
                        "utf-8"
                    )
                ).hexdigest()

                title = self._extract_title(
                    content
                )

                source_id = (
                    f"web_{content_hash}"
                )

                acquired_at = datetime.now(
                    timezone.utc
                ).isoformat()

                metadata = {
                    "provider": self.provider_name,
                    "acquired_at": acquired_at,
                    "content_type": fetched[
                        "content_type"
                    ],
                    "http_status": fetched[
                        "status"
                    ],
                    "content_bytes": fetched[
                        "bytes"
                    ],
                    "content_hash": content_hash,
                    "requested_url": fetched[
                        "url"
                    ],
                    "final_url": fetched[
                        "final_url"
                    ],
                    "reliability": 0.5,
                }

                acquired.append(
                    AcquiredSource(
                        source_id=source_id,
                        title=title,
                        source_type="web",
                        locator=fetched[
                            "final_url"
                        ],
                        content=content,
                        metadata=metadata,
                    )
                )

            except (
                ValueError,
                RuntimeError,
            ) as exc:
                errors.append(
                    f"{raw_url}: {exc}"
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
                "requested_sources": len(urls),
                "acquired_sources": len(
                    acquired
                ),
                "errors": errors,
            },
        )
