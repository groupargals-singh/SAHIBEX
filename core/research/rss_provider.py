from __future__ import annotations

import hashlib
import html
import ipaddress
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from core.research.acquisition import (
    AcquiredSource,
    AcquisitionRequest,
    AcquisitionResult,
    ResearchAcquisitionProvider,
)


@dataclass
class RSSAtomProviderConfig:
    timeout_seconds: float = 15.0
    max_response_bytes: int = 2_000_000
    max_sources: int = 10
    user_agent: str = "SAHIBEX-Research-RSS/0.1"
    allow_http: bool = True
    allow_https: bool = True
    allow_private_hosts: bool = False

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be positive"
            )

        if self.max_response_bytes <= 0:
            raise ValueError(
                "max_response_bytes must be positive"
            )

        if self.max_sources <= 0:
            raise ValueError(
                "max_sources must be positive"
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


class RSSAtomResearchProvider(
    ResearchAcquisitionProvider
):
    provider_name = "rss_atom"
    requires_network = True

    RSS_NAMESPACES = {
        "atom": "http://www.w3.org/2005/Atom",
        "dc": "http://purl.org/dc/elements/1.1/",
        "content": (
            "http://purl.org/rss/1.0/modules/content/"
        ),
    }

    def __init__(
        self,
        config: Optional[
            RSSAtomProviderConfig
        ] = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else RSSAtomProviderConfig()
        )

        self._opener = urllib.request.build_opener(
            _NoRedirectHandler()
        )

    # ---------------------------------------------------------
    # Security
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

        if normalized == "localhost":
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
            resolved_address = address_info[4][0]

            if self._is_unsafe_ip(
                resolved_address
            ):
                raise ValueError(
                    "hostname resolves to a "
                    "private/reserved address"
                )

    def _validate_url(
        self,
        url: str,
    ) -> urllib.parse.ParseResult:
        if not isinstance(url, str):
            raise ValueError(
                "URL must be a string"
            )

        normalized = url.strip()

        if not normalized:
            raise ValueError(
                "source URL cannot be empty"
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

        if (
            parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError(
                "credentials in URL are not allowed"
            )

        hostname = parsed.hostname

        if not hostname:
            raise ValueError(
                "URL hostname cannot be empty"
            )

        self._validate_hostname(hostname)

        return normalized

    # ---------------------------------------------------------
    # HTTP
    # ---------------------------------------------------------

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
                    "response exceeds configured "
                    "size limit"
                )

        chunks: list[bytes] = []
        total = 0

        while True:
            chunk = response.read(65536)

            if not chunk:
                break

            total += len(chunk)

            if (
                total
                > self.config.max_response_bytes
            ):
                raise ValueError(
                    "response exceeds configured "
                    "size limit"
                )

            chunks.append(chunk)

        return b"".join(chunks)

    def _fetch_feed(
        self,
        url: str,
    ) -> tuple[bytes, str]:
        self._validate_url(url)

        request = urllib.request.Request(
            url=url,
            method="GET",
            headers={
                "User-Agent": self.config.user_agent,
                "Accept": (
                    "application/rss+xml, "
                    "application/atom+xml, "
                    "application/xml, "
                    "text/xml, "
                    "text/plain;q=0.8, "
                    "*/*;q=0.1"
                ),
            },
        )

        try:
            response = self._opener.open(
                request,
                timeout=self.config.timeout_seconds,
            )

            try:
                payload = self._read_limited(
                    response
                )

                content_type = (
                    response.headers.get(
                        "Content-Type",
                        "",
                    )
                    or ""
                )
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
        "HTTP "
        f"{exc.code}: redirects are not allowed"
    ) from exc

            raise ValueError(
                "HTTP error while fetching feed: "
                f"{exc.code}"
            ) from exc

        except urllib.error.URLError as exc:
            raise ValueError(
                "URL error while fetching feed"
            ) from exc

        except TimeoutError as exc:
            raise RuntimeError(
                "feed request timed out"
            ) from exc

        return (
            payload,
            content_type,
        )

    # ---------------------------------------------------------
    # XML security
    # ---------------------------------------------------------

    @staticmethod
    def _reject_unsafe_xml(
        payload: bytes,
    ) -> None:
        sample = payload[:100_000]
        upper_sample = sample.upper()

        if b"<!ENTITY" in upper_sample:
            raise ValueError(
                "ENTITY declarations are not allowed"
            )

        if b"<!DOCTYPE" in upper_sample:
            raise ValueError(
                "DOCTYPE declarations are not allowed"
            )

    def _parse_xml(
        self,
        payload: bytes,
    ) -> ET.Element:
        if not payload:
            raise ValueError(
                "feed response is empty"
            )

        self._reject_unsafe_xml(payload)

        try:
            return ET.fromstring(payload)
        except ET.ParseError as exc:
            raise ValueError(
                "invalid XML feed: not valid XML"
            ) from exc

    # ---------------------------------------------------------
    # XML helpers
    # ---------------------------------------------------------

    @staticmethod
    def _local_name(
        tag: str,
    ) -> str:
        if "}" in tag:
            return tag.rsplit(
                "}",
                1,
            )[1]

        return tag

    @classmethod
    def _children(
        cls,
        element: ET.Element,
        name: str,
    ) -> list[ET.Element]:
        wanted = name.lower()

        return [
            child
            for child in list(element)
            if cls._local_name(
                child.tag
            ).lower()
            == wanted
        ]

    @classmethod
    def _child(
        cls,
        element: Optional[ET.Element],
        name: str,
    ) -> Optional[ET.Element]:
        if element is None:
            return None

        children = cls._children(
            element,
            name,
        )

        if not children:
            return None

        return children[0]

    @staticmethod
    def _text(
        element: Optional[ET.Element],
    ) -> str:
        if element is None:
            return ""

        text = "".join(
            element.itertext()
        )

        return html.unescape(
            re.sub(
                r"\s+",
                " ",
                text,
            ).strip()
        )

    @classmethod
    def _atom_link(
        cls,
        element: ET.Element,
    ) -> str:
        links = cls._children(
            element,
            "link",
        )

        if not links:
            return ""

        fallback = ""

        for link in links:
            href = (
                link.attrib.get(
                    "href",
                    "",
                )
                or ""
            ).strip()

            if not href:
                continue

            if not fallback:
                fallback = href

            rel = (
                link.attrib.get(
                    "rel",
                    "",
                )
                or ""
            ).lower()

            if rel == "alternate":
                return href

        return fallback

    @staticmethod
    def _clean_content(
        value: str,
    ) -> str:
        if not value:
            return ""

        return re.sub(
            r"\s+",
            " ",
            html.unescape(value).strip(),
        )

    @staticmethod
    def _resolve_url(
        base_url: str,
        value: str,
    ) -> str:
        return urllib.parse.urljoin(
            base_url,
            value.strip(),
        )

    @classmethod
    def _stable_source_id(
        cls,
        url: str,
    ) -> str:
        normalized = url.strip()

        if not normalized:
            raise ValueError(
                "source URL cannot be empty"
            )

        digest = hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()

        return f"rss_{digest}"

    # ---------------------------------------------------------
    # RSS parser
    # ---------------------------------------------------------

    def _parse_rss(
        self,
        root: ET.Element,
        feed_url: str,
        acquired_at: str,
        limit: int,
        content_type: str,
    ) -> list[AcquiredSource]:
        channel = self._child(
            root,
            "channel",
        )

        if channel is None:
            raise ValueError(
                "RSS feed has no channel"
            )

        feed_title = self._text(
            self._child(
                channel,
                "title",
            )
        )

        feed_link = self._text(
            self._child(
                channel,
                "link",
            )
        )

        sources: list[AcquiredSource] = []

        for item in self._children(
            channel,
            "item",
        ):
            if len(sources) >= limit:
                break

            title = self._text(
                self._child(
                    item,
                    "title",
                )
            )

            raw_link = self._text(
                self._child(
                    item,
                    "link",
                )
            )

            if not raw_link:
                continue

            link = self._resolve_url(
                feed_url,
                raw_link,
            )

            guid = self._text(
                self._child(
                    item,
                    "guid",
                )
            )

            description = self._text(
                self._child(
                    item,
                    "description",
                )
            )

            encoded = self._text(
                self._child(
                    item,
                    "encoded",
                )
            )

            content = (
                encoded
                or description
            )

            published_at = self._text(
                self._child(
                    item,
                    "pubDate",
                )
            )

            author = self._text(
                self._child(
                    item,
                    "author",
                )
            )

            if not author:
                author = self._text(
                    self._child(
                        item,
                        "creator",
                    )
                )

            source_id = self._stable_source_id(
                link
            )

            sources.append(
                AcquiredSource(
                    source_id=source_id,
                    title=(
                        title
                        or feed_title
                    ),
                    source_type="rss",
                    locator=link,
                    publisher=(
                        feed_title
                        or None
                    ),
                    author=(
                        author
                        or None
                    ),
                    published_at=(
                        published_at
                        or None
                    ),
                    content=self._clean_content(
                        content
                    ),
                    metadata={
                        "provider": (
                            self.__class__.__name__
                        ),
                        "feed_url": feed_url,
                        "feed_format": "rss",
                        "content_type": (
                            content_type
                            or "application/rss+xml"
                        ),
                        "feed_title": feed_title,
                        "feed_link": feed_link,
                        "guid": guid,
                        "acquired_at": acquired_at,
                        "discovery_only": True,
                        "content_is_feed_item": True,
                        "reliability": 0.6,
                    },
                )
            )

        return sources

    # ---------------------------------------------------------
    # Atom parser
    # ---------------------------------------------------------

    def _parse_atom(
        self,
        root: ET.Element,
        feed_url: str,
        acquired_at: str,
        limit: int,
        content_type: str,
    ) -> list[AcquiredSource]:
        feed_title = self._text(
            self._child(
                root,
                "title",
            )
        )

        sources: list[AcquiredSource] = []

        for entry in self._children(
            root,
            "entry",
        ):
            if len(sources) >= limit:
                break

            title = self._text(
                self._child(
                    entry,
                    "title",
                )
            )

            raw_link = self._atom_link(
                entry
            )

            if not raw_link:
                continue

            link = self._resolve_url(
                feed_url,
                raw_link,
            )

            summary = self._text(
                self._child(
                    entry,
                    "summary",
                )
            )

            content = self._text(
                self._child(
                    entry,
                    "content",
                )
            )

            entry_content = (
                content
                or summary
            )

            published_at = self._text(
                self._child(
                    entry,
                    "published",
                )
            )

            if not published_at:
                published_at = self._text(
                    self._child(
                        entry,
                        "updated",
                    )
                )

            author_element = self._child(
                entry,
                "author",
            )

            author = self._text(
                self._child(
                    author_element,
                    "name",
                )
            )

            source_id = self._stable_source_id(
                link
            )

            sources.append(
                AcquiredSource(
                    source_id=source_id,
                    title=(
                        title
                        or feed_title
                    ),
                    source_type="rss",
                    locator=link,
                    publisher=(
                        feed_title
                        or None
                    ),
                    author=(
                        author
                        or None
                    ),
                    published_at=(
                        published_at
                        or None
                    ),
                    content=self._clean_content(
                        entry_content
                    ),
                    metadata={
                        "provider": (
                            self.__class__.__name__
                        ),
                        "feed_url": feed_url,
                        "feed_format": "atom",
                        "content_type": (
                            content_type
                            or "application/atom+xml"
                        ),
                        "feed_title": feed_title,
                        "acquired_at": acquired_at,
                        "discovery_only": True,
                        "content_is_feed_item": True,
                        "reliability": 0.6,
                    },
                )
            )

        return sources

    # ---------------------------------------------------------
    # Public acquisition
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
                    "RSS/Atom acquisition requires "
                    "request.metadata['url'] or "
                    "request.metadata['urls']"
                )

            urls = [url]

        if not isinstance(
            urls,
            list,
        ):
            raise ValueError(
                "metadata['urls'] must be a list"
            )

        if not urls:
            raise ValueError(
                "metadata['urls'] cannot be empty"
            )

        limit = min(
            request.max_sources,
            self.config.max_sources,
        )

        sources: list[AcquiredSource] = []
        seen_source_ids: set[str] = set()
        seen_feed_urls: set[str] = set()

        acquired_at = datetime.now(
            timezone.utc
        ).isoformat()

        for feed_url in urls:
            if len(sources) >= limit:
                break

            if not isinstance(
                feed_url,
                str,
            ):
                raise ValueError(
                    "RSS/Atom feed URL must be a string"
                )

            normalized_feed_url = (
                feed_url.strip()
            )

            if not normalized_feed_url:
                raise ValueError(
                    "RSS/Atom feed URL cannot be empty"
                )

            if (
                normalized_feed_url
                in seen_feed_urls
            ):
                continue

            seen_feed_urls.add(
                normalized_feed_url
            )

            payload, content_type = (
                self._fetch_feed(
                    normalized_feed_url
                )
            )

            root = self._parse_xml(
                payload
            )

            root_name = self._local_name(
                root.tag
            ).lower()

            remaining = (
                limit
                - len(sources)
            )

            if root_name == "rss":
                parsed_sources = (
                    self._parse_rss(
                        root,
                        normalized_feed_url,
                        acquired_at,
                        remaining,
                        content_type,
                    )
                )

            elif root_name == "feed":
                parsed_sources = (
                    self._parse_atom(
                        root,
                        normalized_feed_url,
                        acquired_at,
                        remaining,
                        content_type,
                    )
                )

            else:
                raise ValueError(
                    "unsupported XML feed root: "
                    f"{root_name}"
                )

            for source in parsed_sources:
                if len(sources) >= limit:
                    break

                if (
                    source.source_id
                    in seen_source_ids
                ):
                    continue

                seen_source_ids.add(
                    source.source_id
                )

                sources.append(
                    source
                )

        return AcquisitionResult(
            query=request.query,
            sources=sources,
            completed=True,
            status="completed",
            metadata={
                "provider": self.provider_name,
                "network_capable": (
                    self.requires_network
                ),
                "feed_count": len(
                    seen_feed_urls
                ),
                "source_count": len(
                    sources
                ),
                "content_type_recorded": True,
            },
        )
