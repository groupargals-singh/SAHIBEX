from __future__ import annotations

import socket
import threading
import time

from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer

from core.research.acquisition import (
    AcquisitionRequest,
)
from core.research.rss_provider import (
    RSSAtomProviderConfig,
    RSSAtomResearchProvider,
)


RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Test News</title>
    <link>https://example.com/</link>
    <description>Test feed</description>

    <item>
      <title>First Test Article</title>
      <link>https://example.com/article-1</link>
      <guid>article-1</guid>
      <pubDate>Mon, 21 Sep 2026 10:00:00 GMT</pubDate>
      <description><![CDATA[
        First article description.
      ]]></description>
      <content:encoded><![CDATA[
        <p>First article full content.</p>
      ]]></content:encoded>
    </item>

    <item>
      <title>Second Test Article</title>
      <link>https://example.com/article-2</link>
      <guid>article-2</guid>
      <description>
        Second article description.
      </description>
    </item>
  </channel>
</rss>
"""


ATOM_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test Atom Feed</title>

  <entry>
    <title>Atom Test Article</title>
    <id>https://example.com/atom-1</id>
    <link href="https://example.com/atom-1"/>
    <updated>2026-09-21T10:00:00Z</updated>
    <summary>Atom article summary.</summary>
    <content>Atom article full content.</content>
  </entry>
</feed>
"""


MALFORMED_XML = """<rss>
  <channel>
    <item>
"""


DOCTYPE_XML = """<?xml version="1.0"?>
<!DOCTYPE rss [
  <!ELEMENT rss ANY>
]>
<rss>
  <channel>
    <item>
      <title>Unsafe</title>
      <link>https://example.com/unsafe</link>
    </item>
  </channel>
</rss>
"""


ENTITY_XML = """<?xml version="1.0"?>
<!DOCTYPE rss [
  <!ENTITY test "unsafe">
]>
<rss>
  <channel>
    <item>
      <title>&test;</title>
      <link>https://example.com/unsafe</link>
    </item>
  </channel>
</rss>
"""


class TestHandler(
    BaseHTTPRequestHandler
):
    response_body = RSS_XML.encode(
        "utf-8"
    )

    response_type = (
        "application/rss+xml"
    )

    status_code = 200

    delay_seconds = 0.0

    def do_GET(self):
        try:
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header(
                    "Location",
                    "/feed",
                )
                self.end_headers()
                return

            if self.path == "/large":
                body = (
                    b"x"
                    * 4096
                )
            else:
                body = self.response_body

            if self.delay_seconds > 0:
                time.sleep(
                    self.delay_seconds
                )

            self.send_response(
                self.status_code
            )

            self.send_header(
                "Content-Type",
                self.response_type,
            )

            self.send_header(
                "Content-Length",
                str(len(body)),
            )

            self.end_headers()

            try:
                self.wfile.write(
                    body
                )
            except (
                BrokenPipeError,
                ConnectionResetError,
            ):
                pass

        except (
            BrokenPipeError,
            ConnectionResetError,
        ):
            pass

    def log_message(
        self,
        format,
        *args,
    ):
        pass


class TestServer:
    def __init__(self):
        self.server = HTTPServer(
            (
                "127.0.0.1",
                0,
            ),
            TestHandler,
        )

        self.thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )

        self.thread.start()

    @property
    def url(self):
        host, port = (
            self.server.server_address
        )

        return (
            f"http://{host}:{port}"
        )

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(
            timeout=2
        )


def local_provider(
    *,
    max_sources=10,
    max_response_bytes=2_000_000,
    timeout_seconds=5.0,
):
    return RSSAtomResearchProvider(
        RSSAtomProviderConfig(
            max_sources=max_sources,
            max_response_bytes=(
                max_response_bytes
            ),
            timeout_seconds=(
                timeout_seconds
            ),
            allow_private_hosts=True,
        )
    )


def run_test(
    name,
    function,
):
    try:
        function()
        print(
            f"[PASS] {name}"
        )
    except Exception as exc:
        print(
            f"[FAIL] {name}: {exc}"
        )
        raise


def test_provider_identity():
    provider = RSSAtomResearchProvider()

    assert (
        provider.provider_name
        == "rss_atom"
    )

    assert (
        provider.requires_network
        is True
    )


def test_default_private_hosts_are_blocked():
    provider = RSSAtomResearchProvider()

    request = AcquisitionRequest(
        query="private host",
        metadata={
            "url": (
                "http://127.0.0.1:8000/feed"
            )
        },
    )

    try:
        provider.acquire(request)
    except ValueError as exc:
        assert (
            "private"
            in str(exc).lower()
            or "localhost"
            in str(exc).lower()
        )
    else:
        raise AssertionError(
            "private host was not blocked"
        )


def test_rss_parsing():
    TestHandler.response_body = (
        RSS_XML.encode("utf-8")
    )

    TestHandler.response_type = (
        "application/rss+xml"
    )

    server = TestServer()

    try:
        provider = local_provider()

        request = AcquisitionRequest(
            query="test rss",
            metadata={
                "url": (
                    f"{server.url}/feed"
                )
            },
        )

        result = provider.acquire(
            request
        )

        assert result.completed is True
        assert (
            result.status
            == "completed"
        )

        assert (
            len(result.sources)
            == 2
        )

        first = result.sources[0]

        assert (
            first.title
            == "First Test Article"
        )

        assert (
            first.source_type
            == "rss"
        )

        assert (
            first.locator
            == "https://example.com/article-1"
        )

        assert (
            "First article full content."
            in first.content
        )

        assert (
            first.metadata["provider"]
            == "RSSAtomResearchProvider"
        )

        assert (
            first.metadata["feed_format"]
            == "rss"
        )

        assert (
            first.metadata["discovery_only"]
            is True
        )

        assert (
            first.metadata[
                "content_is_feed_item"
            ]
            is True
        )

        assert (
            first.metadata[
                "content_type"
            ]
            == "application/rss+xml"
        )

    finally:
        server.close()


def test_atom_parsing():
    TestHandler.response_body = (
        ATOM_XML.encode("utf-8")
    )

    TestHandler.response_type = (
        "application/atom+xml"
    )

    server = TestServer()

    try:
        provider = local_provider()

        request = AcquisitionRequest(
            query="test atom",
            metadata={
                "url": (
                    f"{server.url}/feed"
                )
            },
        )

        result = provider.acquire(
            request
        )

        assert result.completed is True

        assert (
            len(result.sources)
            == 1
        )

        source = result.sources[0]

        assert (
            source.title
            == "Atom Test Article"
        )

        assert (
            source.source_type
            == "rss"
        )

        assert (
            source.locator
            == "https://example.com/atom-1"
        )

        assert (
            "Atom article full content."
            in source.content
        )

        assert (
            source.metadata[
                "feed_format"
            ]
            == "atom"
        )

    finally:
        server.close()

        TestHandler.response_body = (
            RSS_XML.encode("utf-8")
        )

        TestHandler.response_type = (
            "application/rss+xml"
        )


def test_stable_source_id():
    provider = RSSAtomResearchProvider()

    first = (
        provider._stable_source_id(
            "https://example.com/article-1"
        )
    )

    second = (
        provider._stable_source_id(
            "https://example.com/article-1"
        )
    )

    assert first == second

    assert first.startswith(
        "rss_"
    )

    assert len(first) == 68


def test_different_urls_have_different_ids():
    provider = RSSAtomResearchProvider()

    first = (
        provider._stable_source_id(
            "https://example.com/a"
        )
    )

    second = (
        provider._stable_source_id(
            "https://example.com/b"
        )
    )

    assert first != second


def test_duplicate_feed_urls_handled():
    TestHandler.response_body = (
        RSS_XML.encode("utf-8")
    )

    TestHandler.response_type = (
        "application/rss+xml"
    )

    server = TestServer()

    try:
        provider = local_provider()

        request = AcquisitionRequest(
            query="duplicate test",
            metadata={
                "urls": [
                    f"{server.url}/feed",
                    f"{server.url}/feed",
                ]
            },
        )

        result = provider.acquire(
            request
        )

        source_ids = [
            source.source_id
            for source in result.sources
        ]

        # The same feed URL may be requested more than
        # once, but the resulting source identities must
        # remain unique.
        assert len(source_ids) == len(
            set(source_ids)
        )

        assert len(result.sources) == 2

    finally:
        server.close()


def test_max_sources_limit():
    TestHandler.response_body = (
        RSS_XML.encode("utf-8")
    )

    server = TestServer()

    try:
        provider = local_provider(
            max_sources=1
        )

        request = AcquisitionRequest(
            query="limit test",
            metadata={
                "url": (
                    f"{server.url}/feed"
                )
            },
        )

        result = provider.acquire(
            request
        )

        assert (
            len(result.sources)
            == 1
        )

    finally:
        server.close()


def test_request_max_sources_limit():
    TestHandler.response_body = (
        RSS_XML.encode("utf-8")
    )

    server = TestServer()

    try:
        provider = local_provider(
            max_sources=10
        )

        request = AcquisitionRequest(
            query="request limit",
            max_sources=1,
            metadata={
                "url": (
                    f"{server.url}/feed"
                )
            },
        )

        result = provider.acquire(
            request
        )

        assert (
            len(result.sources)
            == 1
        )

    finally:
        server.close()


def test_malformed_xml_blocked():
    TestHandler.response_body = (
        MALFORMED_XML.encode("utf-8")
    )

    server = TestServer()

    try:
        provider = local_provider()

        request = AcquisitionRequest(
            query="malformed",
            metadata={
                "url": (
                    f"{server.url}/feed"
                )
            },
        )

        try:
            provider.acquire(
                request
            )
        except ValueError as exc:
            assert (
                "valid XML"
                in str(exc)
            )
        else:
            raise AssertionError(
                "malformed XML was not blocked"
            )

    finally:
        server.close()


def test_doctype_blocked():
    TestHandler.response_body = (
        DOCTYPE_XML.encode("utf-8")
    )

    server = TestServer()

    try:
        provider = local_provider()

        request = AcquisitionRequest(
            query="doctype",
            metadata={
                "url": (
                    f"{server.url}/feed"
                )
            },
        )

        try:
            provider.acquire(
                request
            )
        except ValueError as exc:
            assert (
                "DOCTYPE"
                in str(exc)
            )
        else:
            raise AssertionError(
                "DOCTYPE was not blocked"
            )

    finally:
        server.close()


def test_entity_blocked():
    TestHandler.response_body = (
        ENTITY_XML.encode("utf-8")
    )

    server = TestServer()

    try:
        provider = local_provider()

        request = AcquisitionRequest(
            query="entity",
            metadata={
                "url": (
                    f"{server.url}/feed"
                )
            },
        )

        try:
            provider.acquire(
                request
            )
        except ValueError as exc:
            assert (
                "ENTITY"
                in str(exc)
            )
        else:
            raise AssertionError(
                "ENTITY was not blocked"
            )

    finally:
        server.close()


def test_localhost_blocked_by_default():
    provider = RSSAtomResearchProvider()

    request = AcquisitionRequest(
        query="localhost",
        metadata={
            "url": (
                "http://localhost:8000/feed"
            )
        },
    )

    try:
        provider.acquire(
            request
        )
    except ValueError as exc:
        assert (
            "localhost"
            in str(exc).lower()
        )
    else:
        raise AssertionError(
            "localhost was not blocked"
        )


def test_private_ip_blocked_by_default():
    provider = RSSAtomResearchProvider()

    request = AcquisitionRequest(
        query="private ip",
        metadata={
            "url": (
                "http://127.0.0.1:8000/feed"
            )
        },
    )

    try:
        provider.acquire(
            request
        )
    except ValueError as exc:
        assert (
            "private"
            in str(exc).lower()
        )
    else:
        raise AssertionError(
            "private IP was not blocked"
        )


def test_credentials_in_url_blocked():
    provider = RSSAtomResearchProvider()

    request = AcquisitionRequest(
        query="credentials",
        metadata={
            "url": (
                "https://user:password@"
                "example.com/feed"
            )
        },
    )

    try:
        provider.acquire(
            request
        )
    except ValueError as exc:
        assert (
            "credentials"
            in str(exc).lower()
        )
    else:
        raise AssertionError(
            "credential URL was not blocked"
        )


def test_invalid_scheme_blocked():
    provider = RSSAtomResearchProvider()

    request = AcquisitionRequest(
        query="invalid scheme",
        metadata={
            "url": (
                "ftp://example.com/feed"
            )
        },
    )

    try:
        provider.acquire(
            request
        )
    except ValueError as exc:
        assert (
            "http"
            in str(exc).lower()
        )
    else:
        raise AssertionError(
            "invalid scheme was not blocked"
        )


def test_empty_url_blocked():
    provider = RSSAtomResearchProvider()

    request = AcquisitionRequest(
        query="empty",
        metadata={
            "url": ""
        },
    )

    try:
        provider.acquire(
            request
        )
    except ValueError as exc:
        assert (
            "empty"
            in str(exc).lower()
        )
    else:
        raise AssertionError(
            "empty URL was not blocked"
        )


def test_missing_url_blocked():
    provider = RSSAtomResearchProvider()

    request = AcquisitionRequest(
        query="missing",
        metadata={}
    )

    try:
        provider.acquire(
            request
        )
    except ValueError as exc:
        assert (
            "url"
            in str(exc).lower()
        )
    else:
        raise AssertionError(
            "missing URL was not blocked"
        )


def test_urls_must_be_list():
    provider = RSSAtomResearchProvider()

    request = AcquisitionRequest(
        query="urls type",
        metadata={
            "urls": (
                "https://example.com/feed"
            )
        },
    )

    try:
        provider.acquire(
            request
        )
    except ValueError as exc:
        assert (
            "list"
            in str(exc).lower()
        )
    else:
        raise AssertionError(
            "non-list urls were not blocked"
        )


def test_empty_urls_list_blocked():
    provider = RSSAtomResearchProvider()

    request = AcquisitionRequest(
        query="empty urls",
        metadata={
            "urls": []
        },
    )

    try:
        provider.acquire(
            request
        )
    except ValueError as exc:
        assert (
            "empty"
            in str(exc).lower()
        )
    else:
        raise AssertionError(
            "empty urls list was not blocked"
        )


def test_redirect_blocked():
    TestHandler.response_body = (
        RSS_XML.encode("utf-8")
    )

    server = TestServer()

    try:
        provider = local_provider()

        request = AcquisitionRequest(
            query="redirect",
            metadata={
                "url": (
                    f"{server.url}/redirect"
                )
            },
        )

        try:
            provider.acquire(
                request
            )
        except RuntimeError as exc:
            assert (
                "HTTP 302"
                in str(exc)
                or "302"
                in str(exc)
            )
        else:
            raise AssertionError(
                "redirect was not blocked"
            )

    finally:
        server.close()


def test_response_size_limit():
    TestHandler.response_body = (
        b"x" * 4096
    )

    TestHandler.response_type = (
        "application/rss+xml"
    )

    server = TestServer()

    try:
        provider = local_provider(
            max_response_bytes=1024
        )

        request = AcquisitionRequest(
            query="size limit",
            metadata={
                "url": (
                    f"{server.url}/large"
                )
            },
        )

        try:
            provider.acquire(
                request
            )
        except ValueError as exc:
            assert (
                "size"
                in str(exc).lower()
            )
        else:
            raise AssertionError(
                "response size limit was not enforced"
            )

    finally:
        server.close()

        TestHandler.response_body = (
            RSS_XML.encode("utf-8")
        )


def test_timeout():
    TestHandler.response_body = (
        RSS_XML.encode("utf-8")
    )

    TestHandler.delay_seconds = 0.5

    server = TestServer()

    try:
        provider = local_provider(
            timeout_seconds=0.05
        )

        request = AcquisitionRequest(
            query="timeout",
            metadata={
                "url": (
                    f"{server.url}/feed"
                )
            },
        )

        try:
            provider.acquire(
                request
            )
        except (
            RuntimeError,
            TimeoutError,
        ) as exc:
            message = str(
                exc
            ).lower()

            assert (
                "tim"
                in message
                or "timeout"
                in message
                or "failed"
                in message
            )
        except OSError:
            # Socket timeout behavior can surface as
            # an OSError depending on the Python/Termux
            # networking stack.
            pass
        else:
            raise AssertionError(
                "timeout was not enforced"
            )

    finally:
        TestHandler.delay_seconds = 0.0
        server.close()


def test_http_can_be_disabled():
    config = RSSAtomProviderConfig(
        allow_http=False
    )

    provider = RSSAtomResearchProvider(
        config
    )

    request = AcquisitionRequest(
        query="http disabled",
        metadata={
            "url": (
                "http://example.com/feed"
            )
        },
    )

    try:
        provider.acquire(
            request
        )
    except ValueError as exc:
        assert (
            "HTTP"
            in str(exc)
        )
    else:
        raise AssertionError(
            "HTTP was not disabled"
        )


def test_https_can_be_disabled():
    config = RSSAtomProviderConfig(
        allow_https=False
    )

    provider = RSSAtomResearchProvider(
        config
    )

    request = AcquisitionRequest(
        query="https disabled",
        metadata={
            "url": (
                "https://example.com/feed"
            )
        },
    )

    try:
        provider.acquire(
            request
        )
    except ValueError as exc:
        assert (
            "HTTPS"
            in str(exc)
        )
    else:
        raise AssertionError(
            "HTTPS was not disabled"
        )


def test_private_hosts_can_be_explicitly_enabled():
    config = RSSAtomProviderConfig(
        allow_private_hosts=True
    )

    provider = RSSAtomResearchProvider(
        config
    )

    assert (
        provider._validate_url(
            "http://127.0.0.1:8000/feed"
        )
        == "http://127.0.0.1:8000/feed"
    )


def main():
    tests = [
        (
            "provider identity",
            test_provider_identity,
        ),
        (
            "private hosts blocked by default",
            test_default_private_hosts_are_blocked,
        ),
        (
            "RSS 2.x parsing",
            test_rss_parsing,
        ),
        (
            "Atom parsing",
            test_atom_parsing,
        ),
        (
            "stable source identity",
            test_stable_source_id,
        ),
        (
            "different URLs get different IDs",
            test_different_urls_have_different_ids,
        ),
        (
            "duplicate feed URLs handled",
            test_duplicate_feed_urls_handled,
        ),
        (
            "maximum source limit",
            test_max_sources_limit,
        ),
        (
            "request source limit",
            test_request_max_sources_limit,
        ),
        (
            "malformed XML blocked",
            test_malformed_xml_blocked,
        ),
        (
            "DOCTYPE blocked",
            test_doctype_blocked,
        ),
        (
            "ENTITY blocked",
            test_entity_blocked,
        ),
        (
            "localhost blocked by default",
            test_localhost_blocked_by_default,
        ),
        (
            "private IP blocked by default",
            test_private_ip_blocked_by_default,
        ),
        (
            "credentials in URL blocked",
            test_credentials_in_url_blocked,
        ),
        (
            "invalid scheme blocked",
            test_invalid_scheme_blocked,
        ),
        (
            "empty URL blocked",
            test_empty_url_blocked,
        ),
        (
            "missing URL blocked",
            test_missing_url_blocked,
        ),
        (
            "urls must be a list",
            test_urls_must_be_list,
        ),
        (
            "empty urls list blocked",
            test_empty_urls_list_blocked,
        ),
        (
            "redirect blocked",
            test_redirect_blocked,
        ),
        (
            "response size limit",
            test_response_size_limit,
        ),
        (
            "timeout enforced",
            test_timeout,
        ),
        (
            "HTTP can be disabled",
            test_http_can_be_disabled,
        ),
        (
            "HTTPS can be disabled",
            test_https_can_be_disabled,
        ),
        (
            "private hosts require explicit opt-in",
            test_private_hosts_can_be_explicitly_enabled,
        ),
    ]

    for name, test in tests:
        run_test(
            name,
            test,
        )

    print()
    print(
        "SAHIBEX RSS/ATOM PROVIDER TEST: PASS"
    )


if __name__ == "__main__":
    main()
