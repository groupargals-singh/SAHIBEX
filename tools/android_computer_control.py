from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import base64
import os
import shutil
import subprocess
from typing import Any, Callable

from tools.computer_control import (
    ComputerAction,
    ComputerControlRequest,
    ComputerControlResult,
)


CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class AndroidControlConfig:
    input_command: str = "input"
    screencap_command: str = "screencap"
    screenshot_path: str = "/sdcard/SAHIBEX/screenshot.png"
    max_text_length: int = 4096


class AndroidComputerControlProvider:
    """
    Permission-gated Android UI control adapter.

    The adapter is intentionally separate from the legacy provider contract.
    It performs OS actions only when explicitly authorized by the caller.

    Supported actions:
      - MOVE_MOUSE -> swipe from x,y to x,y2 (Android touch equivalent)
      - CLICK -> input tap
      - TYPE_TEXT -> input text
      - PRESS_KEY -> input keyevent
      - SCREENSHOT -> screencap + bounded base64 result

    This provider never grants permission itself.
    """

    def __init__(
        self,
        *,
        config: AndroidControlConfig | None = None,
        command_runner: CommandRunner | None = None,
    ) -> None:
        self.config = config or AndroidControlConfig()
        self._run = command_runner or self._subprocess_run

    @staticmethod
    def _subprocess_run(command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )

    def _available(self, command: str) -> bool:
        return bool(shutil.which(command))

    def execute(
        self,
        request: ComputerControlRequest,
        *,
        authorized: bool = False,
    ) -> ComputerControlResult:
        if not isinstance(request, ComputerControlRequest):
            raise TypeError("request must be ComputerControlRequest")

        if not authorized:
            return ComputerControlResult(
                action=request.action,
                success=False,
                result=None,
                error="Computer control requires explicit authorization.",
            )

        if request.action == ComputerAction.SCREENSHOT:
            return self._screenshot(request)

        if not self._available(self.config.input_command):
            return ComputerControlResult(
                action=request.action,
                success=False,
                result=None,
                error=(
                    "Android input command is unavailable on this runtime."
                ),
            )

        try:
            command = self._build_input_command(request)
        except (TypeError, ValueError) as exc:
            return ComputerControlResult(
                action=request.action,
                success=False,
                result=None,
                error=str(exc),
            )

        completed = self._run(command)

        if completed.returncode != 0:
            error = (completed.stderr or completed.stdout or "input command failed").strip()
            return ComputerControlResult(
                action=request.action,
                success=False,
                result=None,
                error=error,
            )

        return ComputerControlResult(
            action=request.action,
            success=True,
            result={
                "command": command[1:],
                "returncode": completed.returncode,
            },
            error=None,
        )

    def _build_input_command(
        self,
        request: ComputerControlRequest,
    ) -> list[str]:
        params = request.parameters

        if request.action == ComputerAction.CLICK:
            x = self._int_param(params, "x")
            y = self._int_param(params, "y")
            return [self.config.input_command, "tap", str(x), str(y)]

        if request.action == ComputerAction.MOVE_MOUSE:
            x = self._int_param(params, "x")
            y = self._int_param(params, "y")
            end_x = self._int_param(params, "end_x", x)
            end_y = self._int_param(params, "end_y", y)
            duration = self._int_param(params, "duration_ms", 100)
            if duration < 0:
                raise ValueError("duration_ms must be non-negative")
            return [
                self.config.input_command,
                "swipe",
                str(x),
                str(y),
                str(end_x),
                str(end_y),
                str(duration),
            ]

        if request.action == ComputerAction.TYPE_TEXT:
            text = params.get("text")
            if not isinstance(text, str):
                raise TypeError("text must be a string")
            if not text:
                raise ValueError("text cannot be empty")
            if len(text) > self.config.max_text_length:
                raise ValueError("text exceeds configured length limit")
            # Android input text uses %s for spaces.
            encoded = text.replace("%", "%25").replace(" ", "%s")
            return [self.config.input_command, "text", encoded]

        if request.action == ComputerAction.PRESS_KEY:
            key = params.get("key")
            if not isinstance(key, str) or not key.strip():
                raise ValueError("key must be a non-empty string")
            return [self.config.input_command, "keyevent", key.strip()]

        raise ValueError(f"Unsupported computer action: {request.action.value}")

    @staticmethod
    def _int_param(
        params: dict[str, Any],
        name: str,
        default: int | None = None,
    ) -> int:
        value = params.get(name, default)
        if value is None:
            raise ValueError(f"{name} is required")
        if isinstance(value, bool):
            raise TypeError(f"{name} must be an integer")
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise TypeError(f"{name} must be an integer") from exc

    def _screenshot(
        self,
        request: ComputerControlRequest,
    ) -> ComputerControlResult:
        if not self._available(self.config.screencap_command):
            return ComputerControlResult(
                action=request.action,
                success=False,
                result=None,
                error="Android screencap command is unavailable on this runtime.",
            )

        path = Path(self.config.screenshot_path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return ComputerControlResult(
                action=request.action,
                success=False,
                result=None,
                error=f"Cannot prepare screenshot path: {exc}",
            )

        completed = self._run(
            [self.config.screencap_command, "-p", str(path)]
        )
        if completed.returncode != 0 or not path.exists():
            error = (completed.stderr or completed.stdout or "screencap failed").strip()
            return ComputerControlResult(
                action=request.action,
                success=False,
                result=None,
                error=error,
            )

        data = path.read_bytes()
        return ComputerControlResult(
            action=request.action,
            success=True,
            result={
                "path": str(path),
                "bytes": len(data),
                "sha256": __import__("hashlib").sha256(data).hexdigest(),
                "base64": base64.b64encode(data).decode("ascii"),
            },
            error=None,
        )
