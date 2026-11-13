from __future__ import annotations

"""Bounded local engineering operations for the SAHIBEX repository.

V1 runs fixed, non-destructive commands only. It does not accept arbitrary
shell text, edit files, install packages, or publish to remotes.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import os
import re
import subprocess
from typing import Sequence


class EngineeringAction(str, Enum):
    REPOSITORY_STATUS = "repository_status"
    DIFF_CHECK = "diff_check"
    COMPILE_CHECK = "compile_check"
    TEST_FILE = "test_file"


@dataclass(frozen=True)
class EngineeringResult:
    action: str
    success: bool
    return_code: int | None
    command: tuple[str, ...]
    output: str
    error: str | None = None
    timed_out: bool = False


class EngineeringPolicyError(PermissionError):
    """Raised when an operation is outside the v1 engineering allowlist."""


class AutonomousEngineeringController:
    """Run bounded, auditable, read-only engineering checks in one repo."""

    VERSION = "1.0"
    MAX_TIMEOUT_SECONDS = 900
    MAX_OUTPUT_CHARS = 20_000
    _REDACTIONS = (
        (re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)\S+"), r"\1[REDACTED]"),
        (re.compile(r"(?i)(token|password|secret|api[_-]?key)(\s*[:=]\s*)\S+"), r"\1\2[REDACTED]"),
    )

    def __init__(self, project_root: str | Path, *, timeout_seconds: int = 300) -> None:
        root = Path(project_root).expanduser().resolve(strict=True)
        if not root.is_dir() or not (root / ".git").exists():
            raise ValueError("project_root must be an existing Git repository")
        if not (root / "app").is_dir() or not (root / "core").is_dir():
            raise ValueError("project_root does not look like a SAHIBEX source tree")
        if not 1 <= int(timeout_seconds) <= self.MAX_TIMEOUT_SECONDS:
            raise ValueError("timeout_seconds is outside the permitted range")
        self.root = root
        self.timeout_seconds = int(timeout_seconds)
        self.python = str(root / ".venv" / "bin" / "python")
        if not Path(self.python).is_file():
            raise ValueError("project virtual-environment Python is missing")

    @classmethod
    def _redact(cls, text: str) -> str:
        for pattern, replacement in cls._REDACTIONS:
            text = pattern.sub(replacement, text)
        if len(text) > cls.MAX_OUTPUT_CHARS:
            text = text[: cls.MAX_OUTPUT_CHARS] + "\n[OUTPUT TRUNCATED]"
        return text

    def _run(self, action: EngineeringAction, argv: Sequence[str]) -> EngineeringResult:
        command = tuple(str(part) for part in argv)
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "LANG": "C.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUNBUFFERED": "1",
        }
        try:
            completed = subprocess.run(
                command, cwd=self.root, env=env, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                encoding="utf-8", errors="replace", timeout=self.timeout_seconds,
                check=False, shell=False,
            )
            return EngineeringResult(
                action.value, completed.returncode == 0, completed.returncode,
                command, self._redact(completed.stdout),
            )
        except subprocess.TimeoutExpired as exc:
            raw = exc.stdout or ""
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="replace")
            return EngineeringResult(
                action.value, False, None, command, self._redact(str(raw)),
                "Command timed out.", True,
            )
        except OSError as exc:
            return EngineeringResult(
                action.value, False, None, command, "",
                f"Command could not start: {exc.__class__.__name__}",
            )

    def run(self, action: EngineeringAction | str, *, test_file: str | None = None) -> EngineeringResult:
        try:
            selected = EngineeringAction(action)
        except ValueError as exc:
            raise EngineeringPolicyError("Unknown engineering action.") from exc

        if selected is EngineeringAction.REPOSITORY_STATUS:
            argv = ("git", "status", "--short", "--branch")
        elif selected is EngineeringAction.DIFF_CHECK:
            argv = ("git", "diff", "--check")
        elif selected is EngineeringAction.COMPILE_CHECK:
            argv = (self.python, "-m", "compileall", "-q", "app", "core", "agents")
        elif selected is EngineeringAction.TEST_FILE:
            if not test_file:
                raise EngineeringPolicyError("A specific test_file is required.")
            candidate = (self.root / test_file).resolve()
            tests_root = (self.root / "tests").resolve()
            if tests_root not in candidate.parents or not candidate.is_file():
                raise EngineeringPolicyError("Tests must be an existing file under tests/.")
            if candidate.suffix != ".py":
                raise EngineeringPolicyError("Only Python test files are accepted.")
            argv = (self.python, "-m", "pytest", "-q", str(candidate.relative_to(self.root)))
        else:  # pragma: no cover
            raise EngineeringPolicyError("Action is not implemented.")
        return self._run(selected, argv)

    @staticmethod
    def protected_capabilities() -> dict[str, bool]:
        """Capabilities explicitly not granted by the v1 controller."""
        return {
            "arbitrary_shell": False,
            "file_write_or_delete": False,
            "package_install": False,
            "credential_access": False,
            "github_commit_or_push": False,
            "cloud_deploy": False,
            "android_ui_control": False,
            "permission_grant": False,
        }
