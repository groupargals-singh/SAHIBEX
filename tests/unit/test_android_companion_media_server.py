from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from tools.android_companion_media_server import MediaBridgeHandler, load_or_create_token


class FakeBrain:
    def __init__(self):
        self.calls = []

    def process(self, text, *, user_confirmation=False):
        self.calls.append((text, user_confirmation))
        return type("Result", (), {
            "success": True,
            "message": "response for " + text,
            "intent": "general_request",
            "verification_status": "VERIFIED",
            "permission_allowed": True,
            "confirmation_required": False,
        })()


class AndroidCompanionMediaServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brain = FakeBrain()
        cls.token = "T" * 64
        handler = type("TestHandler", (MediaBridgeHandler,), {"brain": cls.brain, "token": cls.token})
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def post(self, payload, token=None):
        data = json.dumps(payload).encode()
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        req = urllib.request.Request(self.base + "/voice", data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=3) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read())

    def test_health_is_loopback_service(self):
        with urllib.request.urlopen(self.base + "/health", timeout=3) as response:
            body = json.loads(response.read())
        self.assertTrue(body["success"])
        self.assertEqual(body["service"], "sahibex-media-bridge")

    def test_voice_request_requires_bearer_token(self):
        status, body = self.post({"text": "hello"}, token="wrong")
        self.assertEqual(status, 401)
        self.assertEqual(body["error"], "unauthorized")

    def test_voice_request_reaches_brain_without_granting_confirmation(self):
        status, body = self.post({"text": "hello Sahibex"}, token=self.token)
        self.assertEqual(status, 200)
        self.assertEqual(body["message"], "response for hello Sahibex")
        self.assertEqual(self.brain.calls[-1], ("hello Sahibex", False))

    def test_invalid_or_oversized_text_is_rejected(self):
        status, _ = self.post({"text": " "}, token=self.token)
        self.assertEqual(status, 400)
        status, _ = self.post({"text": "x" * 8193}, token=self.token)
        self.assertEqual(status, 400)

    def test_token_is_created_once_with_private_permissions(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "token"
            token = load_or_create_token(path)
            self.assertGreaterEqual(len(token), 40)
            self.assertEqual(load_or_create_token(path), token)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()


def test_client_disconnect_while_sending_headers_is_handled():
    class DisconnectedHandler:
        def send_response(self, status):
            pass

        def send_header(self, name, value):
            pass

        def end_headers(self):
            raise BrokenPipeError("client closed socket")

        class Writer:
            def write(self, data):
                raise BrokenPipeError("client closed socket")

        wfile = Writer()

    # A cancelled slow voice request must not leak a handler traceback.
    MediaBridgeHandler._send(DisconnectedHandler(), 200, {"success": True})
