from __future__ import annotations

import json
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from tools.sahibex_device_fabric import ReplayGuard, SahibexDeviceClient, sign_request
from tools.sahibex_desktop_agent import make_handler


TOKEN = "test-only-secret-token-with-32-chars-minimum"


def start_agent(tmp_path):
    (tmp_path / "visible.txt").write_text("safe", encoding="utf-8")
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(TOKEN, {"workspace": tmp_path.resolve()}, ReplayGuard()))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_hmac_signature_changes_with_body_and_rejects_wrong_token():
    signature = sign_request(TOKEN, "POST", "/v1/action", "1000", "nonce_abcdefghijkl", b'{"action":"list_directory"}')
    assert len(signature) == 64
    assert signature != sign_request(TOKEN, "POST", "/v1/action", "1000", "nonce_abcdefghijkl", b'{"action":"open_url"}')
    assert signature != sign_request("another-secret-token-with-32-chars", "POST", "/v1/action", "1000", "nonce_abcdefghijkl", b'{"action":"list_directory"}')


def test_replay_guard_rejects_replay_and_stale_timestamp():
    guard = ReplayGuard()
    kwargs = dict(token=TOKEN, method="GET", path="/v1/device", timestamp="1000", nonce="nonce_abcdefghijkl", body=b"")
    signature = sign_request(**kwargs)
    assert guard.accept(**kwargs, signature=signature, now=1000)
    assert not guard.accept(**kwargs, signature=signature, now=1000)
    fresh = dict(kwargs, nonce="nonce_abcdefghijkm")
    fresh_sig = sign_request(**fresh)
    assert not ReplayGuard().accept(**fresh, signature=fresh_sig, now=1200)


def test_loopback_client_status_and_directory_listing(tmp_path):
    server = start_agent(tmp_path)
    try:
        client = SahibexDeviceClient(f"http://127.0.0.1:{server.server_port}", TOKEN)
        status = client.device_status()
        assert status["success"] is True
        assert "list_directory" in status["capabilities"]
        assert status["arbitrary_shell"] is False
        listing = client.list_directory()
        assert listing["success"] is True
        assert [item["name"] for item in listing["entries"]] == ["visible.txt"]
    finally:
        server.shutdown()
        server.server_close()


def test_directory_traversal_is_blocked(tmp_path):
    server = start_agent(tmp_path)
    try:
        client = SahibexDeviceClient(f"http://127.0.0.1:{server.server_port}", TOKEN)
        result = client.list_directory(path="../")
        assert result["success"] is False
        assert result.get("http_status") == 403
    finally:
        server.shutdown()
        server.server_close()


def test_client_refuses_plain_http_to_non_loopback():
    with pytest.raises(ValueError, match="require HTTPS"):
        SahibexDeviceClient("http://192.168.1.50:38743", TOKEN)


def test_client_rejects_short_token():
    with pytest.raises(ValueError, match="32 characters"):
        SahibexDeviceClient("http://127.0.0.1:38743", "short")

def test_wrong_pairing_secret_is_rejected(tmp_path):
    server = start_agent(tmp_path)
    try:
        client = SahibexDeviceClient(
            f"http://127.0.0.1:{server.server_port}",
            "different-secret-token-with-32-chars",
        )
        result = client.device_status()
        assert result["success"] is False
        assert result["http_status"] == 401
    finally:
        server.shutdown()
        server.server_close()


def test_desktop_tool_requires_permission_and_confirmation():
    from tools.sahibex_desktop_tool import DesktopDeviceControlTool

    class FakeClient:
        def device_status(self):
            return {"success": True, "device_id": "test-desktop"}

    tool = DesktopDeviceControlTool(client=FakeClient())
    blocked = tool.execute(action="device_status")
    assert blocked["status"] == "BLOCKED"
    accepted_read = tool.execute(action="device_status", permission_granted=True)
    assert accepted_read["success"] is True
    blocked_write = tool.execute(action="write_file", permission_granted=True)
    assert blocked_write["status"] == "BLOCKED"
    accepted = tool.execute(
        action="device_status",
        permission_granted=True,
        confirmation_provided=True,
    )
    assert accepted["success"] is True
    assert accepted["device_id"] == "test-desktop"

def test_runtime_registry_adds_desktop_tool_only_when_configured(monkeypatch):
    from pathlib import Path
    from tools.registry import build_runtime_registry
    monkeypatch.setenv("SAHIBEX_DESKTOP_AGENT_URL", "https://desktop.example:38743")
    monkeypatch.setenv("SAHIBEX_DEVICE_TOKEN", TOKEN)
    registry = build_runtime_registry(Path.cwd())
    assert registry.has("desktop_device_control")
    definition = registry.get("desktop_device_control")
    assert definition.read_only is False
    assert definition.requires_confirmation is True

def test_agent_refuses_non_loopback_without_tls(monkeypatch, capsys):
    from tools.sahibex_desktop_agent import main
    monkeypatch.setenv("SAHIBEX_DEVICE_TOKEN", TOKEN)
    result = main(["--host", "0.0.0.0", "--port", "38743"])
    assert result == 2
    assert "requires --tls-cert and --tls-key" in capsys.readouterr().err


def test_agent_refuses_missing_pairing_secret(monkeypatch, capsys):
    from tools.sahibex_desktop_agent import main
    monkeypatch.delenv("SAHIBEX_DEVICE_TOKEN", raising=False)
    result = main(["--host", "127.0.0.1", "--port", "38743"])
    assert result == 2
    assert "SAHIBEX_DEVICE_TOKEN" in capsys.readouterr().err


def test_desktop_agent_write_file_requires_local_approval_and_confines_path(tmp_path, monkeypatch):
    import tools.sahibex_desktop_agent as agent_module
    monkeypatch.setattr(agent_module, "_local_approval", lambda action, detail: True)
    server = start_agent(tmp_path)
    try:
        client = SahibexDeviceClient(f"http://127.0.0.1:{server.server_port}", TOKEN)
        written = client.write_file(root="workspace", path="generated/hello.txt", content="hello sahibex")
        assert written["success"] is True
        assert (tmp_path / "generated" / "hello.txt").read_text(encoding="utf-8") == "hello sahibex"
        read_back = client.read_file(root="workspace", path="generated/hello.txt")
        assert read_back["success"] is True
        assert read_back["content"] == "hello sahibex"
        blocked = client.write_file(root="workspace", path="../outside.txt", content="no")
        assert blocked["success"] is False
        assert blocked.get("http_status") == 403
    finally:
        server.shutdown()
        server.server_close()


def test_desktop_agent_runs_approved_allowlisted_command_without_shell(tmp_path, monkeypatch):
    import tools.sahibex_desktop_agent as agent_module
    monkeypatch.setattr(agent_module, "_local_approval", lambda action, detail: True)
    server = start_agent(tmp_path)
    try:
        client = SahibexDeviceClient(f"http://127.0.0.1:{server.server_port}", TOKEN)
        import sys
        result = client.run_command(root="workspace", argv=[sys.executable, "-c", "print('sahibex-ok')"])
        assert result["success"] is True
        assert "sahibex-ok" in result["stdout"]
        blocked = client.run_command(root="workspace", argv=["sh", "-c", "echo unsafe"])
        assert blocked["success"] is False
        assert blocked.get("http_status") == 403
    finally:
        server.shutdown()
        server.server_close()


def test_unified_control_bridge_routes_phone_and_blocks_unpaired_desktop(tmp_path):
    from tools.sahibex_control_bridge import SahibexControlBridge
    bridge = SahibexControlBridge(tmp_path)
    blocked = bridge.execute(target="laptop", action="device_status",
                             _permission_granted=True, _confirmation_provided=True)
    assert blocked["status"] == "BLOCKED"
    status = bridge.execute(target="phone", action="device_status",
                            _permission_granted=True, _confirmation_provided=True)
    assert status["success"] is True
    assert status["target"] == "phone"


def test_runtime_registry_registers_unified_control_bridge(monkeypatch):
    from pathlib import Path
    from tools.registry import build_runtime_registry
    monkeypatch.delenv("SAHIBEX_DESKTOP_AGENT_URL", raising=False)
    monkeypatch.delenv("SAHIBEX_DEVICE_TOKEN", raising=False)
    registry = build_runtime_registry(Path.cwd())
    assert registry.has("sahibex_control_bridge")
    definition = registry.get("sahibex_control_bridge")
    assert definition.read_only is False
    assert definition.requires_confirmation is True


def test_control_bridge_permission_classification_is_action_specific():
    from core.policies.approval import ActionType, PermissionEngine
    from tools.permission_gateway import ToolPermissionGateway
    from tools.registry import build_runtime_registry

    registry = build_runtime_registry(Path.cwd())
    gateway = ToolPermissionGateway(PermissionEngine(), registry)
    read = gateway.check("sahibex_control_bridge", request={"action": "read_file"})
    assert read.action is ActionType.READ_FILE
    assert read.allowed is True
    write_without_confirmation = gateway.check(
        "sahibex_control_bridge",
        request={"action": "write_file"},
        confirmation=False,
    )
    assert write_without_confirmation.action is ActionType.WRITE_FILE
    assert write_without_confirmation.allowed is False
    command = gateway.check(
        "sahibex_control_bridge",
        request={"action": "run_command"},
        confirmation=True,
    )
    assert command.action is ActionType.RUN_COMMAND
    assert command.allowed is True
    network = gateway.check(
        "sahibex_control_bridge",
        request={"action": "open_url"},
        confirmation=False,
    )
    assert network.action is ActionType.NETWORK_ACCESS
    assert network.allowed is False


def test_safe_executor_applies_action_specific_bridge_permissions(tmp_path, monkeypatch):
    from core.policies.approval import PermissionEngine
    from tools.executor import SafeToolExecutor
    from tools.permission_gateway import ToolPermissionGateway
    from tools.registry import build_runtime_registry

    monkeypatch.delenv("SAHIBEX_DESKTOP_AGENT_URL", raising=False)
    monkeypatch.delenv("SAHIBEX_DEVICE_TOKEN", raising=False)
    registry = build_runtime_registry(tmp_path)
    gateway = ToolPermissionGateway(PermissionEngine(), registry)
    executor = SafeToolExecutor(registry, permission_gateway=gateway)

    status = executor.execute("sahibex_control_bridge", target="phone", action="device_status")
    assert status.success is True
    assert status.result["target"] == "phone"

    blocked = executor.execute(
        "sahibex_control_bridge", target="phone", action="write_file",
        parameters={"path": "must_not_exist.txt", "content": "no"},
    )
    assert blocked.success is False
    assert not (tmp_path / "must_not_exist.txt").exists()

    written = executor.execute(
        "sahibex_control_bridge", target="phone", action="write_file",
        parameters={"path": "approved.txt", "content": "approved"},
        _confirmation_provided=True,
    )
    assert written.success is True
    assert (tmp_path / "approved.txt").read_text(encoding="utf-8") == "approved"
