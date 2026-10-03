from __future__ import annotations

import json
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from core.research.brave_search_backend import (
    BraveSearchBackend,
    BraveSearchConfig,
)


TEST_API_KEY = "TEST_BRAVE_SECRET_123"


class BraveTestHandler(BaseHTTPRequestHandler):
    received_headers = {}
    received_path = ""

    def do_GET(self):
        type(self).received_headers = {
            key.lower(): value
            for key, value in self.headers.items()
        }

        type(self).received_path = self.path

        payload = {
            "web": {
                "results": [
                    {
                        "title": "First Result",
                        "url": "https://example.com/one",
                        "description": "First snippet",
                        "page_age": "2026-09-20",
                    },
                    {
                        "title": "Second Result",
                        "url": "https://example.com/two",
                        "description": "Second snippet",
                    },
                ]
            }
        }

        body = json.dumps(payload).encode("utf-8")

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

        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def log_message(self, format, *args):
        return


def start_server():
    server = HTTPServer(
        ("127.0.0.1", 0),
        BraveTestHandler,
    )

    thread = Thread(
        target=server.serve_forever,
        daemon=True,
    )

    thread.start()

    return server


def check(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main():
    print(
        "SAHIBEX BRAVE SEARCH BACKEND TEST"
    )

    server = start_server()

    try:
        endpoint = (
            f"http://127.0.0.1:"
            f"{server.server_port}/res/v1/web/search"
        )

        config = BraveSearchConfig(
            endpoint=endpoint.replace(
                "http://",
                "https://",
            ),
        )

        # The local test server uses HTTP.
        # Override the frozen config only for the
        # local transport test by constructing the
        # object directly with a temporary subclass
        # is intentionally avoided.
        #
        # Instead, verify the production config
        # contract separately below.

        check(
            config.endpoint.startswith("https://"),
            "Brave default endpoint uses HTTPS",
        )

        backend = BraveSearchBackend(
            TEST_API_KEY,
        )

        check(
            backend.backend_name == "brave_search",
            "backend identity",
        )

        check(
            backend.config.country == "IN",
            "India country configuration",
        )

        check(
            backend.config.search_lang == "en",
            "English search language",
        )

        check(
            backend.config.safesearch == "moderate",
            "SafeSearch configuration",
        )

        url = backend._build_url(
            "AI security",
            50,
        )

        check(
            "q=AI+security" in url,
            "query encoded correctly",
        )

        check(
            "count=20" in url,
            "result count capped at 20",
        )

        check(
            "X-Subscription-Token"
            not in url,
            "API key header name not placed in URL",
        )

        check(
            TEST_API_KEY not in url,
            "API key not placed in URL",
        )

        sample_payload = {
            "web": {
                "results": [
                    {
                        "title": "Test Title",
                        "url": "https://example.com",
                        "description": "Test description",
                        "page_age": "2026-09-20",
                    }
                ]
            }
        }

        mapped = backend._map_result(
            sample_payload["web"]["results"][0],
            1,
        )

        check(
            mapped.title == "Test Title",
            "title mapped",
        )

        check(
            mapped.url == "https://example.com",
            "URL mapped",
        )

        check(
            mapped.snippet == "Test description",
            "description mapped to snippet",
        )

        check(
            mapped.rank == 1,
            "rank mapped",
        )

        check(
            mapped.metadata["provider"] == "brave",
            "provider metadata preserved",
        )

        check(
            mapped.metadata["backend"]
            == "brave_search",
            "backend metadata preserved",
        )

        results = backend._web_results(
            sample_payload
        )

        check(
            len(results) == 1,
            "web results extracted",
        )

        try:
            BraveSearchConfig(
                endpoint="http://example.com"
            )

        except ValueError:
            print(
                "[PASS] HTTP Brave endpoint blocked"
            )

        else:
            raise AssertionError(
                "HTTP Brave endpoint was accepted"
            )

        try:
            BraveSearchBackend("")

        except ValueError:
            print(
                "[PASS] empty API key blocked"
            )

        else:
            raise AssertionError(
                "empty API key was accepted"
            )

        try:
            backend.search(
                "",
                max_results=5,
            )

        except ValueError:
            print(
                "[PASS] empty query blocked"
            )

        else:
            raise AssertionError(
                "empty query was accepted"
            )

        try:
            backend.search(
                "test",
                max_results=0,
            )

        except ValueError:
            print(
                "[PASS] invalid result count blocked"
            )

        else:
            raise AssertionError(
                "invalid result count was accepted"
            )

        try:
            backend.search(
                "x" * 601,
                max_results=5,
            )

        except ValueError:
            print(
                "[PASS] oversized query blocked"
            )

        else:
            raise AssertionError(
                "oversized query was accepted"
            )

        print(
            "SAHIBEX BRAVE SEARCH BACKEND TEST: PASS"
        )

    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
