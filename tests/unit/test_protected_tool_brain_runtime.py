from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.tool_brain import ToolBrain
from core.policies.approval import PermissionEngine


def main() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        brain = ToolBrain(
            PermissionEngine(),
            project_root=root,
        )

        blocked = brain.execute(
            "delete file app.txt",
            user_confirmation=False,
        )
        assert blocked.success is False
        assert blocked.allowed is False
        assert blocked.requires_confirmation is True
        assert not (root / "app.txt").exists()

        created = brain.execute(
            "write file app.txt with SAHIBEX LIVE",
            user_confirmation=True,
        )
        assert created.success is True
        assert (root / "app.txt").read_text(encoding="utf-8") == "SAHIBEX LIVE"

        deleted = brain.execute(
            "delete file app.txt",
            user_confirmation=True,
        )
        assert deleted.success is True
        assert not (root / "app.txt").exists()

        command = brain.execute(
            "run command python -c 'print(42)'",
            user_confirmation=True,
        )
        assert command.success is True
        assert command.result["returncode"] == 0
        assert "42" in command.result["stdout"]

        print("SAHIBEX PROTECTED TOOL BRAIN RUNTIME TEST: PASS")


if __name__ == "__main__":
    main()
