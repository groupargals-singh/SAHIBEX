from __future__ import annotations

from pathlib import Path
from typing import Any


class ProtectedFilesystemTools:
    """Permission-gated project filesystem mutation tools.

    The registry/permission gateway is authoritative. These handlers also
    enforce the SAHIBEX project-root boundary so a protected request cannot
    escape the project directory.
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root).resolve()

    def _safe_path(self, requested: str) -> Path:
        if not isinstance(requested, str) or not requested.strip():
            raise ValueError("path must be a non-empty string.")
        candidate = (self.project_root / requested.strip()).resolve()
        try:
            candidate.relative_to(self.project_root)
        except ValueError as exc:
            raise PermissionError(
                "Path is outside the SAHIBEX project boundary."
            ) from exc
        return candidate

    def write_file(
        self,
        *,
        path: str,
        content: str,
        _permission_granted: bool = False,
        **_: Any,
    ) -> dict[str, Any]:
        if not _permission_granted:
            raise PermissionError("Protected write requires permission.")
        if not isinstance(content, str):
            raise TypeError("content must be a string.")
        target = self._safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {
            "path": str(target.relative_to(self.project_root)),
            "bytes_written": len(content.encode("utf-8")),
            "success": True,
        }

    def delete_file(
        self,
        *,
        path: str,
        _permission_granted: bool = False,
        **_: Any,
    ) -> dict[str, Any]:
        if not _permission_granted:
            raise PermissionError("Protected delete requires permission.")
        target = self._safe_path(path)
        if not target.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        if target.is_dir():
            raise IsADirectoryError(
                "Directory deletion is not supported by this tool."
            )
        target.unlink()
        return {
            "path": str(target.relative_to(self.project_root)),
            "deleted": True,
            "success": True,
        }
