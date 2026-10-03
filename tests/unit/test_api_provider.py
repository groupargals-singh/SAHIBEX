from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from core.research.acquisition import AcquisitionRequest
from core.research.api_provider import (
    RESTJSONProviderConfig,
    RESTJSONResearchProvider,
)


class _TestAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/data":
            payload = {
                "results": [
                    {
                        "title": "First Result",
                        "url": "https://example.com/first",
                        "content": "First API result",
                        "author": "Author One",
                        "published_at": "2026-01-01",
                    },
                    {
                        "title": "Second Result",
                        "url": "https://example.com/second",
                        "content": "Second API result",
                        "author": "Author Two",
                        "published_at": "2026-01-02",
                    },
                ]
            }

            self._send_json(payload)
            return

        if self.path == "/object":
            payload = {
                "title": "Single Object",
                "url": "https://example.com/object",
                "content": "Object result",
            }

            self._send_json(payload)
            return

        if self.path == "/duplicates":
            payload = {
                "results": [
                    {
                        "title": "Duplicate",
                        "url": "https://example.com/same",
                        "content": "Same content",
                    },
                    {
                        "title": "Duplicate",
                        "url": "https://example.com/same",
                        "content": "Same content",
                    },
                ]
            }

            self._send_json(payload)
            return

        if self.path == "/headers":
            if self.headers.get("X-Test-Key") != "test-value":
                self.send_response(403)
                self.end_headers()
                return

            self._send_json(
                {
                    "results": [
                        {
                            "title": "Header Test",
                            "url": "https://example.com/header",
                            "content": "Header accepted",
                        }
                    ]
                }
            )
            return

        if self.path == "/invalid-json":
            body = b"{invalid json"

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json",
            )
            self.send_header(
                "Content-Length",
                str(len(body)),
            )
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/wrong-content-type":
            body = b"<html>not json</html>"

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/html",
            )
            self.send_header(
                "Content-Length",
                str(len(body)),
            )
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/redirect":
            self.send_response(302)
            self.send_header(
                "Location",
                "/data",
            )
            self.end_headers()
            return

        if self.path == "/error":
            self.send_response(500)
            self.end_headers()
            return

        self.send_response(404)
        self.end_headers()

    def log_message(
        self,
        format: str,
        *args,
    ) -> None:
        return

    def _send_json(
        self,
        payload,
    ) -> None:
        body = json.dumps(
            payload
        ).encode("utf-8")

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "application/json",
        )
        self.send_header(
            "Content-Length",
            str(len(body)),
        )
        self.end_headers()
        self.wfile.write(body)


class _TestServer:
    def __init__(self) -> None:
        self.server = HTTPServer(
            ("127.0.0.1", 0),
            _TestAPIHandler,
        )

        self.thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )

    @property
    def base_url(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}"

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


def _provider(
    **kwargs,
) -> RESTJSONResearchProvider:
    config = RESTJSONProviderConfig(
        allow_private_hosts=True,
        **kwargs,
    )

    return RESTJSONResearchProvider(
        config=config
    )


def test_provider_identity() -> None:
    provider = RESTJSONResearchProvider()

    assert (
        provider.provider_name
        == "rest_json_api"
    )

    assert provider.requires_network is True

    print(
        "[PASS] provider identity"
    )


def test_private_hosts_blocked_by_default() -> None:
    provider = RESTJSONResearchProvider()

    try:
        provider._validate_url(
            "http://127.0.0.1:8000/data"
        )
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

    print(
        "[PASS] private hosts blocked by default"
    )


def test_private_hosts_require_explicit_opt_in() -> None:
    provider = _provider()

    result = provider._validate_url(
        "http://127.0.0.1:8000/data"
    )

    assert (
        result
        == "http://127.0.0.1:8000/data"
    )

    print(
        "[PASS] private hosts require explicit opt-in"
    )


def test_invalid_scheme_blocked() -> None:
    provider = RESTJSONResearchProvider()

    try:
        provider._validate_url(
            "ftp://example.com/data"
        )
    except ValueError as exc:
        assert "HTTP/HTTPS" in str(exc)
    else:
        raise AssertionError(
            "invalid scheme was not blocked"
        )

    print(
        "[PASS] invalid scheme blocked"
    )


def test_credentials_in_url_blocked() -> None:
    provider = RESTJSONResearchProvider()

    try:
        provider._validate_url(
            "https://user:password@example.com/data"
        )
    except ValueError as exc:
        assert (
            "credentials"
            in str(exc).lower()
        )
    else:
        raise AssertionError(
            "credentials in URL were not blocked"
        )

    print(
        "[PASS] credentials in URL blocked"
    )


def test_http_can_be_disabled() -> None:
    provider = RESTJSONResearchProvider(
        RESTJSONProviderConfig(
            allow_http=False
        )
    )

    try:
        provider._validate_url(
            "http://example.com/data"
        )
    except ValueError as exc:
        assert (
            "HTTP URLs are disabled"
            in str(exc)
        )
    else:
        raise AssertionError(
            "HTTP disable policy failed"
        )

    print(
        "[PASS] HTTP can be disabled"
    )


def test_https_can_be_disabled() -> None:
    provider = RESTJSONResearchProvider(
        RESTJSONProviderConfig(
            allow_https=False
        )
    )

    try:
        provider._validate_url(
            "https://example.com/data"
        )
    except ValueError as exc:
        assert (
            "HTTPS URLs are disabled"
            in str(exc)
        )
    else:
        raise AssertionError(
            "HTTPS disable policy failed"
        )

    print(
        "[PASS] HTTPS can be disabled"
    )


def test_results_path_parsing() -> None:
    server = _TestServer()
    server.start()

    try:
        provider = _provider()

        request = AcquisitionRequest(
            query="API test",
            metadata={
                "url": (
                    server.base_url
                    + "/data"
                ),
                "results_path": "results",
            },
        )

        result = provider.acquire(
            request
        )

        assert result.completed is True
        assert result.status == "completed"
        assert len(result.sources) == 2

        assert (
            result.sources[0].title
            == "First Result"
        )

        assert (
            result.sources[1].title
            == "Second Result"
        )

        print(
            "[PASS] results path parsing"
        )

    finally:
        server.stop()


def test_object_result_is_supported() -> None:
    server = _TestServer()
    server.start()

    try:
        provider = _provider()

        request = AcquisitionRequest(
            query="object test",
            metadata={
                "url": (
                    server.base_url
                    + "/object"
                )
            },
        )

        result = provider.acquire(
            request
        )

        assert result.completed is True
        assert len(result.sources) == 1
        assert (
            result.sources[0].title
            == "Single Object"
        )

        print(
            "[PASS] single object result"
        )

    finally:
        server.stop()


def test_custom_field_paths() -> None:
    server = _TestServer()
    server.start()

    try:
        provider = _provider()

        request = AcquisitionRequest(
            query="custom paths",
            metadata={
                "url": (
                    server.base_url
                    + "/data"
                ),
                "results_path": "results",
                "title_path": "title",
                "locator_path": "url",
                "content_path": "content",
                "author_path": "author",
                "published_at_path": (
                    "published_at"
                ),
            },
        )

        result = provider.acquire(
            request
        )

        assert result.completed is True
        assert len(result.sources) == 2

        source = result.sources[0]

        assert source.author == "Author One"
        assert (
            source.published_at
            == "2026-01-01"
        )
        assert (
            source.locator
            == "https://example.com/first"
        )

        print(
            "[PASS] custom field paths"
        )

    finally:
        server.stop()


def test_duplicate_results_are_deduplicated() -> None:
    server = _TestServer()
    server.start()

    try:
        provider = _provider()

        request = AcquisitionRequest(
            query="duplicate test",
            metadata={
                "url": (
                    server.base_url
                    + "/duplicates"
                ),
                "results_path": "results",
            },
        )

        result = provider.acquire(
            request
        )

        assert result.completed is True
        assert len(result.sources) == 1

        print(
            "[PASS] duplicate results handled"
        )

    finally:
        server.stop()


def test_source_ids_are_stable() -> None:
    server = _TestServer()
    server.start()

    try:
        provider = _provider()

        request = AcquisitionRequest(
            query="stable ID test",
            metadata={
                "url": (
                    server.base_url
                    + "/data"
                ),
                "results_path": "results",
            },
        )

        first = provider.acquire(
            request
        )

        second = provider.acquire(
            request
        )

        first_ids = [
            source.source_id
            for source in first.sources
        ]

        second_ids = [
            source.source_id
            for source in second.sources
        ]

        assert first_ids == second_ids

        print(
            "[PASS] stable source identity"
        )

    finally:
        server.stop()


def test_request_source_limit() -> None:
    server = _TestServer()
    server.start()

    try:
        provider = _provider()

        request = AcquisitionRequest(
            query="limit test",
            max_sources=1,
            metadata={
                "url": (
                    server.base_url
                    + "/data"
                ),
                "results_path": "results",
            },
        )

        result = provider.acquire(
            request
        )

        assert len(result.sources) == 1

        print(
            "[PASS] request source limit"
        )

    finally:
        server.stop()


def test_provider_source_limit() -> None:
    server = _TestServer()
    server.start()

    try:
        provider = _provider(
            max_sources=1
        )

        request = AcquisitionRequest(
            query="provider limit test",
            max_sources=10,
            metadata={
                "url": (
                    server.base_url
                    + "/data"
                ),
                "results_path": "results",
            },
        )

        result = provider.acquire(
            request
        )

        assert len(result.sources) == 1

        print(
            "[PASS] provider source limit"
        )

    finally:
        server.stop()


def test_custom_headers() -> None:
    server = _TestServer()
    server.start()

    try:
        provider = _provider()

        request = AcquisitionRequest(
            query="header test",
            metadata={
                "url": (
                    server.base_url
                    + "/headers"
                ),
                "headers": {
                    "X-Test-Key": "test-value"
                },
            },
        )

        result = provider.acquire(
            request
        )

        assert result.completed is True
        assert len(result.sources) == 1

        print(
            "[PASS] custom headers"
        )

    finally:
        server.stop()


def test_redirect_is_blocked() -> None:
    server = _TestServer()
    server.start()

    try:
        provider = _provider()

        request = AcquisitionRequest(
            query="redirect test",
            metadata={
                "url": (
                    server.base_url
                    + "/redirect"
                )
            },
        )

        result = provider.acquire(
            request
        )

        assert result.completed is False
        assert result.status == "failed"
        assert result.sources == []

        assert any(
            "redirects are not allowed"
            in error.lower()
            for error in result.metadata[
                "errors"
            ]
        )

        print(
            "[PASS] redirect blocked"
        )

    finally:
        server.stop()


def test_wrong_content_type_is_blocked() -> None:
    server = _TestServer()
    server.start()

    try:
        provider = _provider()

        request = AcquisitionRequest(
            query="content type test",
            metadata={
                "url": (
                    server.base_url
                    + "/wrong-content-type"
                )
            },
        )

        result = provider.acquire(
            request
        )

        assert result.completed is False
        assert result.sources == []

        assert any(
            "content type"
            in error.lower()
            for error in result.metadata[
                "errors"
            ]
        )

        print(
            "[PASS] unsupported content type blocked"
        )

    finally:
        server.stop()


def test_invalid_json_is_blocked() -> None:
    server = _TestServer()
    server.start()

    try:
        provider = _provider()

        request = AcquisitionRequest(
            query="invalid JSON test",
            metadata={
                "url": (
                    server.base_url
                    + "/invalid-json"
                )
            },
        )

        result = provider.acquire(
            request
        )

        assert result.completed is False
        assert result.sources == []

        assert any(
            "not valid JSON"
            in error
            for error in result.metadata[
                "errors"
            ]
        )

        print(
            "[PASS] invalid JSON blocked"
        )

    finally:
        server.stop()


def test_http_error_is_captured() -> None:
    server = _TestServer()
    server.start()

    try:
        provider = _provider()

        request = AcquisitionRequest(
            query="HTTP error test",
            metadata={
                "url": (
                    server.base_url
                    + "/error"
                )
            },
        )

        result = provider.acquire(
            request
        )

        assert result.completed is False
        assert result.sources == []

        assert any(
            "HTTP 500"
            in error
            for error in result.metadata[
                "errors"
            ]
        )

        print(
            "[PASS] HTTP error handling"
        )

    finally:
        server.stop()


def test_missing_url_is_blocked() -> None:
    provider = _provider()

    request = AcquisitionRequest(
        query="missing URL"
    )

    try:
        provider.acquire(
            request
        )
    except ValueError as exc:
        assert (
            "requires"
            in str(exc)
        )
    else:
        raise AssertionError(
            "missing URL was not rejected"
        )

    print(
        "[PASS] missing URL blocked"
    )


def test_urls_must_be_list_or_tuple() -> None:
    provider = _provider()

    request = AcquisitionRequest(
        query="URL type test",
        metadata={
            "urls": "https://example.com"
        },
    )

    try:
        provider.acquire(
            request
        )
    except ValueError as exc:
        assert (
            "list or tuple"
            in str(exc)
        )
    else:
        raise AssertionError(
            "invalid urls type was not rejected"
        )

    print(
        "[PASS] urls must be list or tuple"
    )


def test_empty_urls_list_is_blocked() -> None:
    provider = _provider()

    request = AcquisitionRequest(
        query="empty URL list",
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
            "cannot be empty"
            in str(exc)
        )
    else:
        raise AssertionError(
            "empty URL list was not rejected"
        )

    print(
        "[PASS] empty URL list blocked"
    )


def test_provider_metadata() -> None:
    server = _TestServer()
    server.start()

    try:
        provider = _provider()

        request = AcquisitionRequest(
            query="metadata test",
            metadata={
                "url": (
                    server.base_url
                    + "/data"
                ),
                "results_path": "results",
            },
        )

        result = provider.acquire(
            request
        )

        assert result.completed is True

        source = result.sources[0]

        assert (
            source.source_type == "api"
        )

        assert (
            source.metadata["provider"]
            == "RESTJSONResearchProvider"
        )

        assert (
            source.metadata["provider_name"]
            == "rest_json_api"
        )

        assert (
            source.metadata[
                "content_is_api_result"
            ]
            is True
        )

        assert (
            source.metadata[
                "discovery_only"
            ]
            is True
        )

        print(
            "[PASS] provider metadata"
        )

    finally:
        server.stop()


if __name__ == "__main__":
    test_provider_identity()
    test_private_hosts_blocked_by_default()
    test_private_hosts_require_explicit_opt_in()
    test_invalid_scheme_blocked()
    test_credentials_in_url_blocked()
    test_http_can_be_disabled()
    test_https_can_be_disabled()
    test_results_path_parsing()
    test_object_result_is_supported()
    test_custom_field_paths()
    test_duplicate_results_are_deduplicated()
    test_source_ids_are_stable()
    test_request_source_limit()
    test_provider_source_limit()
    test_custom_headers()
    test_redirect_is_blocked()
    test_wrong_content_type_is_blocked()
    test_invalid_json_is_blocked()
    test_http_error_is_captured()
    test_missing_url_is_blocked()
    test_urls_must_be_list_or_tuple()
    test_empty_urls_list_is_blocked()
    test_provider_metadata()

    print(
        "\nSAHIBEX REST/JSON API PROVIDER TEST: PASS"
    )
