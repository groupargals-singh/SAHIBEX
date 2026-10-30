"""Permission-gated tool for a paired SAHIBEX Desktop Agent."""
from __future__ import annotations
import os
from typing import Any
from tools.sahibex_device_fabric import SahibexDeviceClient

class DesktopDeviceControlTool:
    """Remote operations remain behind SAHIBEX's canonical permission gateway."""
    def __init__(self, client: SahibexDeviceClient | None = None) -> None:
        if client is None:
            base_url = os.environ.get("SAHIBEX_DESKTOP_AGENT_URL", "").strip()
            token = os.environ.get("SAHIBEX_DEVICE_TOKEN", "")
            if not base_url or not token:
                raise ValueError("desktop agent URL/token are not configured")
            client = SahibexDeviceClient(base_url, token)
        self.client = client

    def execute(self, *, action: str, parameters: dict[str, Any] | None = None,
                permission_granted: bool = False, confirmation_provided: bool = False) -> dict[str, Any]:
        if not permission_granted:
            return {"success": False, "status": "BLOCKED", "error": "permission gateway authorization is required"}
        if not isinstance(action, str):
            raise TypeError("action must be a string")
        if action in {"write_file", "run_command", "open_url"} and not confirmation_provided:
            return {"success": False, "status": "BLOCKED", "error": "explicit confirmation is required for this action"}
        params = parameters or {}
        if not isinstance(params, dict):
            raise TypeError("parameters must be an object")
        if action == "device_status":
            return self.client.device_status()
        if action == "list_directory":
            return self.client.list_directory(root=params.get("root", "workspace"), path=params.get("path", "."))
        if action == "read_file":
            return self.client.read_file(root=params.get("root", "workspace"), path=params.get("path", ""))
        if action == "write_file":
            return self.client.write_file(root=params.get("root", "workspace"), path=params.get("path", ""), content=params.get("content", ""))
        if action == "run_command":
            return self.client.run_command(root=params.get("root", "workspace"), argv=params.get("argv", []), cwd=params.get("cwd", "."), timeout_seconds=params.get("timeout_seconds", 30))
        if action == "open_url":
            return self.client.open_url(params.get("url", ""))
        return {"success": False, "status": "BLOCKED", "error": "unsupported desktop action"}
