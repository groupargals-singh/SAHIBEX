from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from core.research.http_search_backend import (
    HTTPJsonSearchBackend,
    HTTPJsonSearchConfig,
)


class LocalHTTPHandler(BaseHTTPRequestHandler):
    payload = {
        "results": [
            {
                "title": "AI Security",
                "url": "https://example.com/security",
                "snippet": "AI security research",
                "publisher": "Example",
            },
            {
                "title": "Research",
                "url": "https://example.com/research",
                "snippet": "Research result",
            },
        ]
    }

    def do_GET(self):
        body = json.dumps(self.payload).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def start_server():
    server = HTTPServer(("127.0.0.1", 0), LocalHTTPHandler)

    thread = Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    return server


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    print("SAHIBEX HTTP JSON SEARCH BACKEND TEST")

    server = start_server()

    try:
        endpoint = f"http://127.0.0.1:{server.server_port}/search"

        config = HTTPJsonSearchConfig(
            endpoint=endpoint,
            allow_http=True,
            max_response_bytes=100_000,
        )

        backend = HTTPJsonSearchBackend(config)

        check(
            backend.backend_name == "http_json",
            "backend identity",
        )

        results = backend.search(
            "AI security",
            max_results=10,
        )

        check(
            len(results) == 2,
            "JSON results parsed",
        )

        check(
            results[0].title == "AI Security",
            "title mapped",
        )

        check(
            results[0].url == "https://example.com/security",
            "URL mapped",
        )

        check(
            results[0].snippet == "AI security research",
            "snippet mapped",
        )

        check(
            results[0].publisher == "Example",
            "publisher mapped",
        )

        check(
            results[0].rank == 1,
            "first result ranked correctly",
        )

        check(
            results[1].rank == 2,
            "second result ranked correctly",
        )

        print(
            "SAHIBEX HTTP JSON SEARCH BACKEND TEST: PASS"
        )

    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
