from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
from typing import Any
from tools.android_bridge_protocol import BridgeSession, DEFAULT_PORT
from tools.android_bridge_client import AndroidBridgeClient
from tools.computer_control import ComputerAction, ComputerControlRequest, ComputerControlResult

@dataclass(frozen=True)
class AndroidControlConfig:
    token_path: str = str(Path(__file__).resolve().parents[1] / "data" / "android_companion_control_token")
    max_text_length: int = 4096
    timeout_seconds: float = 7.0

class AndroidComputerControlProvider:
    """Permission-gated Android UI control via the Companion Accessibility service."""
    def __init__(self, *, config: AndroidControlConfig | None = None, client_factory=None) -> None:
        self.config = config or AndroidControlConfig()
        self._client_factory = client_factory or (lambda session: AndroidBridgeClient(session, timeout_seconds=self.config.timeout_seconds))

    def execute(self, request: ComputerControlRequest, *, authorized: bool = False) -> ComputerControlResult:
        if not isinstance(request, ComputerControlRequest): raise TypeError("request must be ComputerControlRequest")
        if not authorized: return ComputerControlResult(request.action, False, None, "Computer control requires explicit authorization.")
        try:
            path = Path(self.config.token_path)
            if not path.is_file(): raise FileNotFoundError("Companion token not configured. Save the private token locally to data/android_companion_control_token; never paste it into chat or logs.")
            if os.name != "nt" and path.stat().st_mode & 0o077: raise PermissionError("Companion token file must have mode 0600.")
            token = path.read_text(encoding="utf-8").strip()
            if not token: raise ValueError("Companion token file is empty.")
            action, payload = self._translate(request)
            response = self._client_factory(BridgeSession(token=token, port=DEFAULT_PORT)).call(action, payload)
            if not response.success: return ComputerControlResult(request.action, False, None, response.error or "Companion rejected the action")
            result = response.result or {}
            if action in {"tap", "swipe", "type_text", "keyevent"} and result.get("completed") is not True:
                return ComputerControlResult(request.action, False, result, "Companion did not confirm action completion")
            if action == "ui_tree" and "tree" not in result:
                return ComputerControlResult(request.action, False, result, "Companion response lacks UI-tree evidence")
            return ComputerControlResult(request.action, True, result, None)
        except Exception as exc:
            return ComputerControlResult(request.action, False, None, str(exc))

    def _translate(self, request: ComputerControlRequest) -> tuple[str, dict[str, Any]]:
        p = request.parameters
        if request.action == ComputerAction.CLICK:
            return "tap", {"x": self._int(p, "x"), "y": self._int(p, "y")}
        if request.action == ComputerAction.MOVE_MOUSE:
            x, y = self._int(p, "x"), self._int(p, "y")
            return "swipe", {"x": x, "y": y, "end_x": self._int(p, "end_x", x), "end_y": self._int(p, "end_y", y), "duration_ms": self._int(p, "duration_ms", 250)}
        if request.action == ComputerAction.TYPE_TEXT:
            value = p.get("text")
            if not isinstance(value, str) or not value: raise ValueError("text must be a non-empty string")
            if len(value) > self.config.max_text_length: raise ValueError("text exceeds configured length limit")
            return "type_text", {"text": value}
        if request.action == ComputerAction.PRESS_KEY:
            key = p.get("key")
            if not isinstance(key, str) or not key.strip(): raise ValueError("key must be a non-empty string")
            codes = {"BACK": 4, "HOME": 3, "APP_SWITCH": 187, "RECENTS": 187}
            k = key.strip().upper()
            code = codes.get(k)
            if code is None: raise ValueError("unsupported key; only BACK, HOME, and APP_SWITCH are allowed")
            return "keyevent", {"keycode": code}
        if request.action == ComputerAction.SCREENSHOT:
            return "screenshot", {"include_base64": True}
        if request.action == ComputerAction.UI_TREE:
            return "ui_tree", {}
        raise ValueError(f"Unsupported computer action: {request.action.value}")

    @staticmethod
    def _int(p: dict[str, Any], name: str, default: int | None = None) -> int:
        value = p.get(name, default)
        if value is None or isinstance(value, bool): raise ValueError(f"{name} must be an integer")
        try: return int(value)
        except (TypeError, ValueError) as exc: raise ValueError(f"{name} must be an integer") from exc
