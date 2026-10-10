from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
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


class _VisibleTextParser(HTMLParser):
    """Extract visible text from HTML while ignoring active/non-content nodes."""

    _BLOCK_TAGS = {
        "address", "article", "aside", "blockquote", "br", "dd", "div",
        "dl", "dt", "fieldset", "figcaption", "figure", "footer", "form",
        "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "li",
        "main", "nav", "ol", "p", "pre", "section", "table", "td", "th",
        "tr", "ul",
    }
    _IGNORED_TAGS = {
        "script", "style", "noscript", "svg", "template",
        "nav", "header", "footer", "aside", "form", "menu",
    }
    _IGNORED_CLASS_HINTS = (
        "advert", "author-bio", "authorbox", "related", "recommended",
        "trending", "popular", "newsletter", "sidebar", "promo",
        "social-share", "share-buttons", "tag-list", "more-stories",
        "latest-stories", "read-more",
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0
        self._tag_stack: list[tuple[str, bool]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = {str(key).lower(): str(value or "") for key, value in attrs}
        class_and_id = (attributes.get("class", "") + " " + attributes.get("id", "")).casefold()
        class_ignored = any(hint in class_and_id for hint in self._IGNORED_CLASS_HINTS)
        ignored = tag in self._IGNORED_TAGS or class_ignored
        self._tag_stack.append((tag, ignored))
        if ignored:
            self._ignored_depth += 1
        elif self._ignored_depth == 0 and tag in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        matched_index = None
        for index in range(len(self._tag_stack) - 1, -1, -1):
            if self._tag_stack[index][0] == tag:
                matched_index = index
                break
        was_ignored = False
        if matched_index is not None:
            popped = self._tag_stack[matched_index:]
            was_ignored = self._tag_stack[matched_index][1]
            self._ignored_depth = max(
                0,
                self._ignored_depth - sum(1 for _, ignored in popped if ignored),
            )
            del self._tag_stack[matched_index:]
        if not was_ignored and self._ignored_depth == 0 and tag in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignored_depth == 0 and data.strip():
            self.parts.append(data)
            self.parts.append(" ")

    def text(self) -> str:
        return " ".join(" ".join(self.parts).split())


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
    def _extract_published_at(content: str) -> datetime | None:
        """Extract an explicitly published timestamp from common page metadata.

        Only parse publisher-supplied structured timestamps; never infer a
        publication date from the fetch time or from unrelated page text.
        """
        # Only publication/creation timestamps establish recency. A modified
        # timestamp can make an old article appear newly published, so it is
        # deliberately excluded from this publication-date field.
        pattern = r'<meta\b[^>]*(?:property|name)=["\'](?:article:published_time|datePublished|pubdate|date)["\'][^>]*>'
        candidates: list[str] = []
        for tag in re.findall(pattern, content, flags=re.IGNORECASE):
            match = re.search(r'\bcontent=["\']([^"\']+)["\']', tag, flags=re.IGNORECASE)
            if match:
                candidates.append(html.unescape(match.group(1)).strip())
        candidates.extend(re.findall(
            r'["\'](?:datePublished|dateCreated)["\']\s*:\s*["\']([^"\']+)["\']',
            content,
            flags=re.IGNORECASE,
        ))
        for candidate in candidates:
            try:
                normalized = candidate[:-1] + "+00:00" if candidate.endswith(("Z", "z")) else candidate
                parsed = datetime.fromisoformat(normalized)
                if parsed.tzinfo is not None and parsed.utcoffset() is not None:
                    return parsed.astimezone(timezone.utc)
            except (TypeError, ValueError, OverflowError):
                continue
        return None

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

    @staticmethod
    def _content_fragment(content: str) -> tuple[str, str]:
        """Prefer article/main markup over the whole publisher page."""
        for tag in ("article", "main"):
            match = re.search(
                rf"<{tag}\b[^>]*>.*?</{tag}\s*>",
                content,
                flags=re.IGNORECASE | re.DOTALL,
            )
            if match and len(match.group(0)) >= 50:
                return match.group(0), tag
        return content, "full_page_fallback"

    @staticmethod
    def _visible_text(content: str, *, max_chars: int = 200_000) -> tuple[str, bool]:
        """Convert HTML to bounded visible text; return text and truncation flag."""
        parser = _VisibleTextParser()
        parser.feed(content)
        parser.close()
        visible = parser.text()
        truncated = len(visible) > max_chars
        return visible[:max_chars].strip(), truncated

    # ---------------------------------------------------------
    # Explicit, bounded redirect resolution
    # ---------------------------------------------------------

    def resolve_redirect_url(self, url: str, *, max_hops: int = 3) -> str:
        """Resolve a redirect chain manually, validating every hop.

        Automatic redirects remain disabled globally. This narrowly scoped
        helper is for resolving search-aggregator discovery links only; each
        Location is validated before a request is made to it.
        """
        if not isinstance(max_hops, int) or isinstance(max_hops, bool) or max_hops < 0 or max_hops > 5:
            raise ValueError("max_hops must be an integer between 0 and 5")
        current = url.strip() if isinstance(url, str) else url
        self._validate_url(current)
        seen = {current}
        redirects = {301, 302, 303, 307, 308}

        for hop in range(max_hops + 1):
            request = Request(
                url=current,
                method="GET",
                headers={"User-Agent": self.config.user_agent, "Range": "bytes=0-0"},
            )
            try:
                response = self._opener.open(request, timeout=self.config.timeout_seconds)
            except HTTPError as exc:
                try:
                    if exc.code not in redirects:
                        raise RuntimeError(f"redirect resolution failed with HTTP {exc.code}") from exc
                    location = exc.headers.get("Location") if exc.headers else None
                finally:
                    exc.close()
                if not location:
                    raise RuntimeError("redirect response has no Location header")
                if hop >= max_hops:
                    raise RuntimeError("redirect hop limit exceeded")
                target = urljoin(current, location)
                self._validate_url(target)
                if target in seen:
                    raise RuntimeError("redirect loop detected")
                seen.add(target)
                current = target
                continue
            except (URLError, TimeoutError) as exc:
                raise RuntimeError("redirect resolution request failed") from exc
            else:
                try:
                    # A successful non-redirect response means current is the
                    # validated destination. Never treat its body as evidence.
                    return response.geturl() or current
                finally:
                    response.close()
        raise RuntimeError("redirect hop limit exceeded")

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

    @staticmethod
    def _is_time_sensitive_query(query: str) -> bool:
        text = query.casefold()
        return any(term in text for term in (
            "today", "latest", "current", "recent", "this week", "breaking",
            "आज", "ताज़ा", "ताजा", "नवीनतम", "हालिया", "इस सप्ताह", "अभी", "क्या नया है",
        ))

    @staticmethod
    def _is_recent_publication(published_at: datetime | None, *, days: int = 7) -> bool:
        if not isinstance(published_at, datetime):
            return False
        if published_at.tzinfo is None or published_at.utcoffset() is None:
            return False
        age = datetime.now(timezone.utc) - published_at.astimezone(timezone.utc)
        return timedelta(0) <= age <= timedelta(days=days)

    @staticmethod
    def _is_listing_page(url: str) -> bool:
        path = urlparse(url).path.casefold().rstrip("/")
        return any(segment in path.split("/") for segment in ("section", "category", "categories", "tag", "topic", "topics"))

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

                raw_content = fetched["content"]
                title = self._extract_title(raw_content)
                content_truncated = False
                content_scope = "plain_text"
                if fetched.get("content_type") in {"text/html", "application/xhtml+xml"}:
                    selected_html, content_scope = self._content_fragment(raw_content)
                    content, content_truncated = self._visible_text(selected_html)
                else:
                    content = raw_content[:200_000]
                    content_truncated = len(raw_content) > 200_000

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

                source_id = (
                    f"web_{content_hash}"
                )

                acquired_at = datetime.now(
                    timezone.utc
                ).isoformat()

                published_at = self._extract_published_at(raw_content)
                if self._is_time_sensitive_query(request.query):
                    if self._is_listing_page(fetched["final_url"]):
                        errors.append(f"listing page rejected for time-sensitive research: {fetched['final_url']}")
                        continue
                    if not self._is_recent_publication(published_at, days=7):
                        errors.append(f"publisher publication date is missing or outside the 7-day window: {fetched['final_url']}")
                        continue
                metadata = {
                    "provider": self.provider_name,
                    "acquired_at": acquired_at,
                    "publication_timestamp_source": (
                        "publisher_metadata" if published_at is not None else None
                    ),
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
                    "html_sanitized": fetched.get("content_type") in {"text/html", "application/xhtml+xml"},
                    "content_extraction_scope": content_scope,
                    "content_truncated": content_truncated,
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
                        published_at=published_at,
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
