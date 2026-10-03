from __future__ import annotations

import json
import socket
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from core.research.http_search_backend import (
    HTTPJsonSearchBackend,
    HTTPJsonSearchConfig,
)


SECRET = "SUPER_SECRET_TEST_KEY_123"


class SecurityHandler(BaseHTTPRequestHandler):
    mode = "normal"
    received_headers = {}
    received_path = ""

    def do_GET(self):
        type(self).received_headers = {
            key.lower(): value
            for key, value in self.headers.items()
        }

        type(self).received_path = self.path

        if self.mode == "normal":
            body = json.dumps(
                {
                    "results": [
                        {
                            "title": "Valid Result",
                            "url": "https://example.com",
                            "snippet": "Valid snippet",
                        }
                    ]
                }
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

            try:
                self.wfile.write(body)
            except BrokenPipeError:
                pass

            return

        if self.mode == "slow":
            time.sleep(2)

            body = b'{"results": []}'

            try:
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

            except BrokenPipeError:
                pass

            return

        self.send_response(500)
        self.end_headers()

    def log_message(self, format, *args):
        return


def start_server():
    server = HTTPServer(
        ("127.0.0.1", 0),
        SecurityHandler,
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
        "SAHIBEX HTTP JSON SEARCH "
        "CREDENTIAL/TIMEOUT SECURITY TEST"
    )

    server = start_server()

    try:
        endpoint = (
            f"http://127.0.0.1:"
            f"{server.server_port}/search"
        )

        config = HTTPJsonSearchConfig(
            endpoint=endpoint,
            allow_http=True,
            timeout_seconds=1.0,
        )

        backend = HTTPJsonSearchBackend(
            config,
            headers={
                "Authorization": (
                    f"Bearer {SECRET}"
                ),
                "X-API-Key": SECRET,
            },
        )

        SecurityHandler.mode = "normal"

        results = backend.search(
            "security test",
            max_results=5,
        )

        check(
            len(results) == 1,
            "authenticated request succeeded",
        )

        headers = SecurityHandler.received_headers

        check(
            headers.get("authorization")
            == f"Bearer {SECRET}",
            "Authorization credential sent through header",
        )

        check(
            headers.get("x-api-key") == SECRET,
            "API key sent through header",
        )

        check(
            SECRET not in SecurityHandler.received_path,
            "secret not placed in request URL",
        )

        check(
            "api_key"
            not in SecurityHandler.received_path.lower(),
            "API key parameter not placed in URL",
        )

        check(
            "apikey"
            not in SecurityHandler.received_path.lower(),
            "apikey parameter not placed in URL",
        )

        SecurityHandler.mode = "slow"

        timeout_config = HTTPJsonSearchConfig(
            endpoint=endpoint,
            allow_http=True,
            timeout_seconds=0.2,
        )

        timeout_backend = HTTPJsonSearchBackend(
            timeout_config
        )

        try:
            timeout_backend.search(
                "timeout test",
                max_results=5,
            )

        except (
            TimeoutError,
            socket.timeout,
            OSError,
        ):
            print(
                "[PASS] request timeout enforced"
            )

        except Exception as exc:
            raise AssertionError(
                "unexpected timeout exception: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        else:
            raise AssertionError(
                "timeout request unexpectedly succeeded"
            )

        test_url = (
            "https://search.example/api"
            "?q=test"
            "&api_key="
            f"{SECRET}"
        )

        redacted = (
            HTTPJsonSearchBackend._redact_url(
                test_url
            )
        )

        check(
            SECRET not in redacted,
            "secret removed from redacted URL",
        )

        check(
            "[REDACTED]" in redacted,
            "redacted URL contains placeholder",
        )

        redacted_headers = (
            HTTPJsonSearchBackend._redact_headers(
                {
                    "Authorization": (
                        f"Bearer {SECRET}"
                    ),
                    "X-API-Key": SECRET,
                    "User-Agent": "SAHIBEX-Test",
                }
            )
        )

        check(
            SECRET not in str(redacted_headers),
            "secret removed from redacted headers",
        )

        check(
            redacted_headers["Authorization"]
            == "[REDACTED]",
            "Authorization header redacted",
        )

        check(
            redacted_headers["X-API-Key"]
            == "[REDACTED]",
            "API key header redacted",
        )

        check(
            redacted_headers["User-Agent"]
            == "SAHIBEX-Test",
            "non-sensitive header preserved",
        )

        print(
            "SAHIBEX HTTP JSON SEARCH "
            "CREDENTIAL/TIMEOUT SECURITY TEST: PASS"
        )

    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
