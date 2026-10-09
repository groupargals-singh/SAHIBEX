from __future__ import annotations

from pathlib import Path
import shlex
import subprocess
from typing import Any


class ProtectedCommandTool:
    """Permission-gated command execution inside the SAHIBEX project root.

    Commands run with a bounded timeout and no credential/environment export.
    The PermissionEngine remains the authority gate; this handler cannot
    self-authorize.
    """

    def __init__(self, project_root: Path, *, timeout_seconds: int = 30) -> None:
        self.project_root = Path(project_root).resolve()
        self.timeout_seconds = timeout_seconds

    def execute(
        self,
        *,
        command: str,
        _permission_granted: bool = False,
        **_: Any,
    ) -> dict[str, Any]:
        if not _permission_granted:
            raise PermissionError("Protected command requires permission.")
        if not isinstance(command, str) or not command.strip():
            raise ValueError("command must be a non-empty string.")

        argv = shlex.split(command)
        if not argv:
            raise ValueError("command must not be empty.")

        # Provide only non-secret runtime variables needed by normal
        # command-line programs. Credentials/tokens from the parent process
        # are deliberately not inherited.
        safe_env = {
            key: value
            for key in ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "TERM")
            if (value := __import__("os").environ.get(key))
        }

        completed = subprocess.run(
            argv,
            cwd=self.project_root,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            env=safe_env,
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout[-20000:],
            "stderr": completed.stderr[-20000:],
            "success": completed.returncode == 0,
        }
