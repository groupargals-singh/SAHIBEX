"""Unified SAHIBEX command router for phone-local and paired desktop work.

All mutations/OS actions require the Main Brain's permission and explicit
confirmation. Remote mutations additionally require local approval on desktop.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.registry import ReadOnlyTools
from tools.protected_command import ProtectedCommandTool
from tools.protected_files import ProtectedFilesystemTools
from tools.computer_control_tool import ComputerControlTool
from tools.sahibex_desktop_tool import DesktopDeviceControlTool


class SahibexControlBridge:
    def __init__(self, project_root: Path, desktop: DesktopDeviceControlTool | None = None,
                 phone_control: ComputerControlTool | None = None) -> None:
        self.project_root = Path(project_root).resolve()
        self.desktop = desktop
        self.phone_control = phone_control or ComputerControlTool()
        self.readonly = ReadOnlyTools(self.project_root)
        self.files = ProtectedFilesystemTools(self.project_root)
        self.commands = ProtectedCommandTool(self.project_root)

    def execute(self, *, target: str, action: str, parameters: dict[str, Any] | None = None,
                _permission_granted: bool = False, _confirmation_provided: bool = False) -> dict[str, Any]:
        if not _permission_granted:
            return {"success": False, "status": "BLOCKED",
                    "error": "SAHIBEX permission gateway authorization is required"}
        if not isinstance(target, str) or not isinstance(action, str):
            raise TypeError("target and action must be strings")
        if action in {"write_file", "run_command", "computer_control", "open_url"} and not _confirmation_provided:
            return {"success": False, "status": "BLOCKED",
                    "error": "explicit user confirmation is required for this action"}
        params = parameters or {}
        if not isinstance(params, dict):
            raise TypeError("parameters must be an object")
        destination = target.strip().lower()

        if destination in {"laptop", "desktop", "computer", "pc"}:
            if self.desktop is None:
                return {"success": False, "status": "BLOCKED",
                        "error": "no desktop is paired; configure the trusted TLS endpoint first"}
            return self.desktop.execute(action=action, parameters=params,
                                        permission_granted=True, confirmation_provided=_confirmation_provided)

        if destination not in {"phone", "android", "this_phone", "local"}:
            return {"success": False, "status": "BLOCKED",
                    "error": "unknown target; use phone or the currently paired desktop"}
        if action == "device_status":
            return {"success": True, "target": "phone", "platform": "Android/Termux",
                    "project_root": str(self.project_root),
                    "capabilities": ["list_directory", "read_file", "write_file",
                                     "run_command_in_project", "computer_control"]}
        if action == "list_directory":
            return self.readonly.list_directory(params.get("path", "."))
        if action == "read_file":
            return self.readonly.read_file(params.get("path", ""))
        if action == "write_file":
            return self.files.write_file(path=params.get("path", ""),
                                         content=params.get("content", ""),
                                         _permission_granted=True)
        if action == "run_command":
            return self.commands.execute(command=params.get("command", ""),
                                         _permission_granted=True)
        if action == "computer_control":
            return self.phone_control.execute(action=params.get("ui_action", ""),
                                              parameters=params.get("ui_parameters", {}),
                                              _permission_granted=True,
                                              _confirmation_provided=True)
        return {"success": False, "status": "BLOCKED",
                "error": "unsupported action for target; no arbitrary remote shell or out-of-project phone filesystem access"}
