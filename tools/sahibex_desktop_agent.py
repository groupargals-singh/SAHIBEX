"""Cross-platform SAHIBEX Desktop Agent (Windows/macOS/Linux).

Default is loopback-only. LAN exposure requires TLS certificate/key and a
shared high-entropy SAHIBEX_DEVICE_TOKEN. File writes, allowlisted argv-based
program launches and browser opening require local console approval. Shell
interpolation and unrestricted shell execution are never exposed.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import secrets
import ssl
import subprocess
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from tools.sahibex_device_fabric import ReplayGuard, safe_json_object


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def _local_approval(action: str, detail: str) -> bool:
    if not sys.stdin or not sys.stdin.isatty():
        print("BLOCKED: no interactive local console for approval", flush=True)
        return False
    try:
        answer = input(f"\nSAHIBEX request: {action} — {detail}\nApprove on this computer? Type YES: ")
    except (EOFError, KeyboardInterrupt):
        return False
    return answer.strip() == "YES"


def make_handler(token: str, roots: dict[str, Path], replay_guard: ReplayGuard):
    class Handler(BaseHTTPRequestHandler):
        server_version = "SAHIBEX-Desktop-Agent/1"

        def log_message(self, fmt, *args):
            # Do not log request bodies, credentials, or authorization headers.
            print("SAHIBEX desktop agent:", fmt % args, flush=True)

        def _send(self, status: int, payload: dict):
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _authorized(self, body: bytes) -> bool:
            from tools.sahibex_device_fabric import sign_request
            timestamp = self.headers.get("X-Sahibex-Timestamp", "")
            nonce = self.headers.get("X-Sahibex-Nonce", "")
            signature = self.headers.get("X-Sahibex-Signature", "")
            return replay_guard.accept(
                token=token, method=self.command, path=self.path,
                timestamp=timestamp, nonce=nonce, body=body,
                signature=signature,
            )

        def do_GET(self):
            if self.path == "/health":
                return self._send(200, {"success": True, "service": "sahibex-desktop-agent"})
            if self.path != "/v1/device":
                return self._send(404, {"success": False, "error": "not found"})
            if not self._authorized(b""):
                return self._send(401, {"success": False, "error": "authentication failed"})
            return self._send(200, {
                "success": True, "device_id": os.environ.get("SAHIBEX_DEVICE_ID", platform.node()),
                "platform": platform.system(), "platform_release": platform.release(),
                "agent_version": "1.0.0",
                "capabilities": ["device_status", "list_directory", "read_file", "write_file_with_local_approval", "run_allowlisted_command_with_local_approval", "open_url_with_local_approval"],
                "file_roots": sorted(roots.keys()),
                "arbitrary_shell": False,
            })

        def do_POST(self):
            if self.path != "/v1/action":
                return self._send(404, {"success": False, "error": "not found"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size < 0 or size > 65536:
                    return self._send(413, {"success": False, "error": "invalid body size"})
                body = self.rfile.read(size)
                if not self._authorized(body):
                    return self._send(401, {"success": False, "error": "authentication failed"})
                request = safe_json_object(body)
                action = request.get("action")
                params = request.get("parameters", {})
                if not isinstance(params, dict):
                    return self._send(400, {"success": False, "error": "parameters must be an object"})
                if action == "list_directory":
                    root_name = params.get("root")
                    relative = params.get("path", ".")
                    if root_name not in roots or not isinstance(relative, str) or len(relative) > 512:
                        return self._send(400, {"success": False, "error": "unknown root or invalid path"})
                    root = roots[root_name]
                    target = (root / relative).resolve()
                    if not _inside(target, root) or not target.is_dir():
                        return self._send(403, {"success": False, "error": "path is outside an allowed root or not a directory"})
                    entries = []
                    for item in sorted(target.iterdir(), key=lambda p: p.name.casefold())[:100]:
                        try:
                            entries.append({"name": item.name, "type": "directory" if item.is_dir() else "file"})
                        except OSError:
                            entries.append({"name": item.name, "type": "unknown"})
                    return self._send(200, {"success": True, "action": action, "root": root_name, "path": str(target), "entries": entries})
                if action == "read_file":
                    root_name = params.get("root")
                    relative = params.get("path")
                    if root_name not in roots or not isinstance(relative, str) or not relative or len(relative) > 512:
                        return self._send(400, {"success": False, "error": "unknown root or invalid path"})
                    root = roots[root_name]
                    target = (root / relative).resolve()
                    if not _inside(target, root) or not target.is_file():
                        return self._send(403, {"success": False, "error": "path is outside the approved workspace or not a file"})
                    try:
                        if target.stat().st_size > 48 * 1024:
                            return self._send(413, {"success": False, "error": "file exceeds 48 KiB read limit"})
                        content = target.read_text(encoding="utf-8")
                    except UnicodeError:
                        return self._send(415, {"success": False, "error": "only UTF-8 text files can be read"})
                    except OSError:
                        return self._send(404, {"success": False, "error": "file could not be read"})
                    return self._send(200, {"success": True, "action": action, "path": str(target), "content": content})
                if action == "write_file":
                    root_name = params.get("root")
                    relative = params.get("path")
                    content = params.get("content")
                    if root_name not in roots or not isinstance(relative, str) or not relative or len(relative) > 512:
                        return self._send(400, {"success": False, "error": "unknown root or invalid path"})
                    if not isinstance(content, str) or len(content.encode("utf-8")) > 48 * 1024:
                        return self._send(400, {"success": False, "error": "file content must be text and at most 48 KiB"})
                    root = roots[root_name]
                    target = (root / relative).resolve()
                    if not _inside(target, root) or target == root:
                        return self._send(403, {"success": False, "error": "path is outside the approved workspace"})
                    if not _local_approval("write_file", str(target)):
                        return self._send(403, {"success": False, "status": "BLOCKED", "error": "local user approval denied or unavailable"})
                    try:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text(content, encoding="utf-8")
                    except OSError:
                        return self._send(500, {"success": False, "error": "file write failed"})
                    return self._send(200, {"success": True, "action": action, "path": str(target), "bytes_written": len(content.encode("utf-8"))})
                if action == "run_command":
                    root_name = params.get("root")
                    cwd_rel = params.get("cwd", ".")
                    argv = params.get("argv")
                    timeout = params.get("timeout_seconds", 30)
                    if root_name not in roots or not isinstance(cwd_rel, str) or not isinstance(argv, list) or not argv or len(argv) > 32:
                        return self._send(400, {"success": False, "error": "invalid workspace, cwd or argv"})
                    if not all(isinstance(arg, str) and len(arg) <= 2048 and "\\x00" not in arg for arg in argv):
                        return self._send(400, {"success": False, "error": "argv must be a list of bounded strings"})
                    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1 or timeout > 60:
                        return self._send(400, {"success": False, "error": "timeout_seconds must be between 1 and 60"})
                    allowed_programs = {"python", "python3", "py", "node", "npm", "npx", "git", "pytest", "pip", "pip3", "go", "cargo", "rustc", "javac", "java", "dotnet", "cmake", "make"}
                    program = Path(argv[0]).name.lower()
                    if program not in allowed_programs:
                        return self._send(403, {"success": False, "status": "BLOCKED", "error": "program is not in the desktop agent allowlist"})
                    root = roots[root_name]
                    cwd = (root / cwd_rel).resolve()
                    if not _inside(cwd, root) or not cwd.is_dir():
                        return self._send(403, {"success": False, "error": "working directory is outside the approved workspace"})
                    detail = json.dumps({"cwd": str(cwd), "argv": argv, "timeout_seconds": timeout}, ensure_ascii=False)
                    if not _local_approval("run_command", detail):
                        return self._send(403, {"success": False, "status": "BLOCKED", "error": "local user approval denied or unavailable"})
                    try:
                        completed = subprocess.run(argv, cwd=str(cwd), shell=False, capture_output=True, text=True, timeout=timeout, check=False)
                        stdout = (completed.stdout or "")[-12000:]
                        stderr = (completed.stderr or "")[-12000:]
                        return self._send(200, {"success": completed.returncode == 0, "action": action, "returncode": completed.returncode, "stdout": stdout, "stderr": stderr, "truncated": len(completed.stdout or "") > 12000 or len(completed.stderr or "") > 12000})
                    except subprocess.TimeoutExpired as exc:
                        return self._send(200, {"success": False, "action": action, "status": "TIMEOUT", "stdout": str(exc.stdout or "")[-12000:], "stderr": str(exc.stderr or "")[-12000:]})
                    except OSError:
                        return self._send(200, {"success": False, "action": action, "status": "FAILED", "error": "program could not be started"})
                if action == "open_url":
                    url = params.get("url")
                    if not isinstance(url, str) or len(url) > 2048:
                        return self._send(400, {"success": False, "error": "invalid URL"})
                    parsed = urlparse(url)
                    if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username or parsed.password:
                        return self._send(400, {"success": False, "error": "only ordinary HTTP(S) URLs are allowed"})
                    if not _local_approval("open_url", url):
                        return self._send(403, {"success": False, "status": "BLOCKED", "error": "local user approval denied or unavailable"})
                    opened = webbrowser.open(url, new=2, autoraise=True)
                    return self._send(200 if opened else 502, {"success": bool(opened), "action": action, "status": "EXECUTED" if opened else "FAILED"})
                return self._send(400, {"success": False, "error": "unsupported action; arbitrary commands are disabled"})
            except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
                return self._send(400, {"success": False, "error": str(exc)})
            except Exception:
                return self._send(500, {"success": False, "error": "internal agent error"})

    return Handler


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the SAHIBEX cross-platform Desktop Agent")
    parser.add_argument("--host", default="127.0.0.1", help="default loopback; LAN requires TLS")
    parser.add_argument("--port", type=int, default=38743)
    parser.add_argument("--tls-cert", help="TLS certificate for remote/LAN binding")
    parser.add_argument("--tls-key", help="TLS private key for remote/LAN binding")
    parser.add_argument("--root", action="append", default=[], metavar="NAME=PATH", help="allowed directory root; repeatable")
    args = parser.parse_args(argv)
    token = os.environ.get("SAHIBEX_DEVICE_TOKEN", "")
    if len(token) < 32:
        print("ERROR: set SAHIBEX_DEVICE_TOKEN to a private random secret of at least 32 characters.", file=sys.stderr)
        return 2
    if not (1 <= args.port <= 65535):
        print("ERROR: invalid port", file=sys.stderr)
        return 2
    host_is_loopback = args.host in ("127.0.0.1", "::1", "localhost")
    if not host_is_loopback and not (args.tls_cert and args.tls_key):
        print("ERROR: non-loopback binding requires --tls-cert and --tls-key; refusing unsafe network exposure.", file=sys.stderr)
        return 2
    # No filesystem root is exposed until the owner explicitly allowlists one.
    roots = {}
    for item in args.root:
        if "=" not in item:
            print(f"ERROR: invalid root {item!r}; expected NAME=PATH", file=sys.stderr)
            return 2
        name, raw_path = item.split("=", 1)
        path = Path(raw_path).expanduser().resolve()
        if not name or not name.replace("_", "").isalnum() or not path.is_dir():
            print(f"ERROR: invalid root {item!r}", file=sys.stderr)
            return 2
        roots[name] = path
    server = ThreadingHTTPServer((args.host, args.port), make_handler(token, roots, ReplayGuard()))
    if not host_is_loopback:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(args.tls_cert, args.tls_key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
    print(f"SAHIBEX Desktop Agent online at {args.host}:{args.port}; TLS={'on' if not host_is_loopback else 'local-only'}", flush=True)
    print("Actions: status, allowlisted directory listing, and locally-approved URL opening. Arbitrary shell is disabled.", flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("SAHIBEX Desktop Agent stopping.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
