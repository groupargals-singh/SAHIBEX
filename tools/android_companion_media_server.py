from __future__ import annotations

import hmac
import json
import os
import secrets
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from core.brain.master_brain import MasterBrain

HOST = "127.0.0.1"
PORT = 38742
MAX_BODY_BYTES = 16_384
TOKEN_PATH = Path(__file__).resolve().parents[1] / "data" / "android_companion_media_token"


def load_or_create_token(path: Path = TOKEN_PATH) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        token = path.read_text(encoding="utf-8").strip()
        if len(token) >= 40:
            return token
        raise RuntimeError("Media bridge token file exists but is invalid; rotate it deliberately")
    token = secrets.token_urlsafe(48)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(token + "\n")
    return token


class MediaBridgeHandler(BaseHTTPRequestHandler):
    server_version = "SAHIBEX-MediaBridge/1"
    token: str
    _thread_state = threading.local()

    def log_message(self, format: str, *args: Any) -> None:
        # Do not log voice transcripts or authorization headers.
        return

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError, OSError):
            # The Android UI may cancel a slow request. Header writes can fail too;
            # do not leak a handler traceback or attempt a second response.
            return

    def do_GET(self) -> None:
        if self.path != "/health":
            self._send(404, {"success": False, "error": "not_found"})
            return
        self._send(200, {"success": True, "service": "sahibex-media-bridge", "host": HOST, "port": PORT})

    def do_POST(self) -> None:
        if self.path != "/voice":
            self._send(404, {"success": False, "error": "not_found"})
            return
        authorization = self.headers.get("Authorization", "")
        expected = "Bearer " + self.token
        if not hmac.compare_digest(authorization, expected):
            self._send(401, {"success": False, "error": "unauthorized"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send(400, {"success": False, "error": "invalid_content_length"})
            return
        if length <= 0 or length > MAX_BODY_BYTES:
            self._send(413 if length > MAX_BODY_BYTES else 400, {"success": False, "error": "invalid_body_size"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send(400, {"success": False, "error": "invalid_json"})
            return
        text = payload.get("text") if isinstance(payload, dict) else None
        if not isinstance(text, str) or not text.strip() or len(text) > 8192:
            self._send(400, {"success": False, "error": "invalid_text"})
            return
        try:
            # Keep each brain/storage instance confined to the request thread.
            # Tests can inject a fake as a class attribute; production uses thread-local instances.
            brain = getattr(self, "brain", None)
            if brain is None:
                brain = getattr(self._thread_state, "brain", None)
                if brain is None:
                    brain = MasterBrain()
                    self._thread_state.brain = brain
            # Voice input is NOT proof of authorization.
            result = brain.process(text.strip(), user_confirmation=False)
            self._send(200, {
                "success": bool(result.success),
                "message": str(result.message)[:12000],
                "intent": str(result.intent),
                "verification_status": str(result.verification_status),
                "permission_allowed": bool(result.permission_allowed),
                "confirmation_required": bool(result.confirmation_required),
            })
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as exc:
            # Do not return transcript or stack traces to the phone UI.
            print(f"MEDIA_BRAIN_PROCESSING_ERROR={type(exc).__name__}: {exc}", flush=True)
            traceback.print_exc()
            self._send(500, {"success": False, "error": "brain_processing_failed"})


def main() -> None:
    os.environ.setdefault("SAHIBEX_MODEL_PROVIDER", "local")
    os.environ.setdefault("SAHIBEX_SEARCH_BACKEND", "duckduckgo_html")
    token = load_or_create_token()
    handler = type("ConfiguredMediaBridgeHandler", (MediaBridgeHandler,), {"token": token})
    # Each request thread owns its own MasterBrain and SQLite connection.
    server = ThreadingHTTPServer((HOST, PORT), handler)
    server.daemon_threads = True
    print(f"SAHIBEX_MEDIA_BRIDGE=ONLINE host={HOST} port={PORT}", flush=True)
    print(f"PAIRING_TOKEN_FILE={TOKEN_PATH}", flush=True)
    print("Protected actions remain blocked unless separately authorized in the normal SAHIBEX UI.", flush=True)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
