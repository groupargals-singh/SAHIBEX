"""SAHIBEX multi-device authenticated request helpers."""
from __future__ import annotations
import hashlib
import hmac
import json
import os
import re
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

MAX_CLOCK_SKEW_SECONDS = 90
MAX_BODY_BYTES = 64 * 1024


def canonical_request(method: str, path: str, timestamp: str, nonce: str, body: bytes) -> bytes:
    if not method or not path.startswith("/") or not timestamp or not nonce:
        raise ValueError("method, absolute path, timestamp and nonce are required")
    body_hash = hashlib.sha256(body).hexdigest()
    return "\n".join((method.upper(), path, timestamp, nonce, body_hash)).encode("utf-8")


def sign_request(token: str, method: str, path: str, timestamp: str, nonce: str, body: bytes = b"") -> str:
    if not isinstance(token, str) or len(token) < 32:
        raise ValueError("device token must contain at least 32 characters")
    return hmac.new(token.encode("utf-8"), canonical_request(method, path, timestamp, nonce, body), hashlib.sha256).hexdigest()


@dataclass
class ReplayGuard:
    max_clock_skew_seconds: int = MAX_CLOCK_SKEW_SECONDS
    _seen: dict[str, float] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def accept(self, *, token: str, method: str, path: str, timestamp: str, nonce: str, body: bytes, signature: str, now: float | None = None) -> bool:
        if len(body) > MAX_BODY_BYTES or not re.fullmatch(r"[A-Za-z0-9_-]{16,96}", nonce or ""):
            return False
        try:
            issued = int(timestamp)
        except (TypeError, ValueError):
            return False
        current = time.time() if now is None else now
        if abs(current - issued) > self.max_clock_skew_seconds:
            return False
        try:
            expected = sign_request(token, method, path, timestamp, nonce, body)
        except (TypeError, ValueError):
            return False
        if not hmac.compare_digest(expected, signature or ""):
            return False
        with self._lock:
            self._seen = {key: expiry for key, expiry in self._seen.items() if expiry >= current}
            replay_key = f"{token[:8]}:{nonce}"
            if replay_key in self._seen:
                return False
            self._seen[replay_key] = current + self.max_clock_skew_seconds * 2
        return True


def safe_json_object(body: bytes) -> dict[str, Any]:
    if len(body) > MAX_BODY_BYTES:
        raise ValueError("request body too large")
    value = json.loads(body.decode("utf-8") or "{}")
    if not isinstance(value, dict):
        raise ValueError("request JSON must be an object")
    return value

class SahibexDeviceClient:
    """Signed HTTPS client for a paired Desktop Agent; never downgrades to HTTP."""
    def __init__(self, base_url: str, token: str, *, timeout: float = 8.0):
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        if parsed.scheme not in ("https", "http") or not parsed.hostname:
            raise ValueError("base_url must be an absolute HTTP(S) URL")
        if parsed.scheme != "https" and parsed.hostname not in ("127.0.0.1", "::1", "localhost"):
            raise ValueError("non-loopback device connections require HTTPS")
        if len(token) < 32:
            raise ValueError("device token must contain at least 32 characters")
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def request(self, method: str, path: str, payload: dict | None = None) -> dict:
        import secrets
        import urllib.error
        import urllib.request
        body = b"" if payload is None else json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        timestamp = str(int(time.time()))
        nonce = secrets.token_urlsafe(24)
        signature = sign_request(self.token, method, path, timestamp, nonce, body)
        headers = {
            "X-Sahibex-Timestamp": timestamp,
            "X-Sahibex-Nonce": nonce,
            "X-Sahibex-Signature": signature,
            "Accept": "application/json",
        }
        if body:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(self.base_url + path, data=body if method.upper() != "GET" else None, headers=headers, method=method.upper())
        tls_context = None
        if self.base_url.startswith("https://"):
            import ssl
            ca_file = os.environ.get("SAHIBEX_DESKTOP_CA", "").strip()
            tls_context = ssl.create_default_context(cafile=ca_file or None)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout, context=tls_context) as response:
                result = json.loads(response.read(MAX_BODY_BYTES + 1).decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                result = json.loads(exc.read(MAX_BODY_BYTES + 1).decode("utf-8"))
            except Exception:
                result = {"success": False, "error": "remote agent returned an unreadable error"}
            result.setdefault("http_status", exc.code)
        if not isinstance(result, dict):
            raise ValueError("device agent returned an invalid response")
        return result

    def device_status(self) -> dict:
        return self.request("GET", "/v1/device")

    def list_directory(self, root: str = "workspace", path: str = ".") -> dict:
        return self.request("POST", "/v1/action", {"action": "list_directory", "parameters": {"root": root, "path": path}})

    def open_url(self, url: str) -> dict:
        return self.request("POST", "/v1/action", {"action": "open_url", "parameters": {"url": url}})

    def read_file(self, *, root: str, path: str) -> dict:
        return self.request("POST", "/v1/action", {"action": "read_file", "parameters": {"root": root, "path": path}})

    def write_file(self, *, root: str, path: str, content: str) -> dict:
        return self.request("POST", "/v1/action", {"action": "write_file", "parameters": {"root": root, "path": path, "content": content}})

    def run_command(self, *, root: str, argv: list[str], cwd: str = ".", timeout_seconds: int = 30) -> dict:
        return self.request("POST", "/v1/action", {"action": "run_command", "parameters": {"root": root, "argv": argv, "cwd": cwd, "timeout_seconds": timeout_seconds}})
