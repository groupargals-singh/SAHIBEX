from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from core.policies.approval import ActionType


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    handler: Callable[..., Any]
    read_only: bool
    requires_confirmation: bool
    protected_action: ActionType | None = None


class ToolRegistry:
    """
    Central registry for SAHIBEX tools.

    The registry only stores and resolves tools.
    It does not decide whether a user is allowed
    to execute a tool. Permission remains outside
    this layer.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        *,
        name: str,
        description: str,
        handler: Callable[..., Any],
        read_only: bool,
        requires_confirmation: bool,
        protected_action: ActionType | None = None,
    ) -> None:

        if not name.strip():
            raise ValueError("Tool name cannot be empty.")

        if name in self._tools:
            raise ValueError(
                f"Tool already registered: {name}"
            )

        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            handler=handler,
            read_only=read_only,
            requires_confirmation=requires_confirmation,
            protected_action=protected_action,
        )

    def get(self, name: str) -> ToolDefinition:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown SAHIBEX tool: {name}"
            ) from exc

    def has(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())


class ReadOnlyTools:
    """
    Safe filesystem inspection tools.

    These tools never write, modify or delete files.
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root).resolve()

    def _safe_path(self, requested: str) -> Path:
        """
        Resolve a path and ensure it stays inside
        the SAHIBEX project directory.
        """

        candidate = (self.project_root / requested).resolve()

        try:
            candidate.relative_to(self.project_root)
        except ValueError as exc:
            raise PermissionError(
                "Path is outside the SAHIBEX project boundary."
            ) from exc

        return candidate

    def list_directory(
        self,
        path: str = ".",
    ) -> dict[str, Any]:

        target = self._safe_path(path)

        if not target.exists():
            raise FileNotFoundError(
                f"Directory does not exist: {path}"
            )

        if not target.is_dir():
            raise NotADirectoryError(
                f"Not a directory: {path}"
            )

        entries = []

        for item in sorted(
            target.iterdir(),
            key=lambda value: value.name.lower(),
        ):
            entries.append(
                {
                    "name": item.name,
                    "type": (
                        "directory"
                        if item.is_dir()
                        else "file"
                    ),
                }
            )

        return {
            "path": str(
                target.relative_to(self.project_root)
            ),
            "entries": entries,
            "count": len(entries),
        }

    def read_file(
        self,
        path: str,
        max_bytes: int = 100_000,
    ) -> dict[str, Any]:

        if max_bytes <= 0:
            raise ValueError(
                "max_bytes must be greater than zero."
            )

        target = self._safe_path(path)

        if not target.exists():
            raise FileNotFoundError(
                f"File does not exist: {path}"
            )

        if not target.is_file():
            raise IsADirectoryError(
                f"Not a file: {path}"
            )

        data = target.read_bytes()

        truncated = len(data) > max_bytes

        if truncated:
            data = data[:max_bytes]

        return {
            "path": str(
                target.relative_to(self.project_root)
            ),
            "content": data.decode(
                "utf-8",
                errors="replace",
            ),
            "bytes_read": len(data),
            "truncated": truncated,
        }

    def file_info(
        self,
        path: str,
    ) -> dict[str, Any]:

        target = self._safe_path(path)

        if not target.exists():
            raise FileNotFoundError(
                f"Path does not exist: {path}"
            )

        stat = target.stat()

        return {
            "path": str(
                target.relative_to(self.project_root)
            ),
            "type": (
                "directory"
                if target.is_dir()
                else "file"
            ),
            "size": stat.st_size,
            "modified": stat.st_mtime,
        }

    def search_local_files(
        self,
        query: str,
        path: str = ".",
        max_results: int = 50,
    ) -> dict[str, Any]:

        query = query.strip()

        if not query:
            raise ValueError(
                "Search query cannot be empty."
            )

        if max_results <= 0:
            raise ValueError(
                "max_results must be greater than zero."
            )

        root = self._safe_path(path)

        if not root.exists():
            raise FileNotFoundError(
                f"Search path does not exist: {path}"
            )

        results: list[dict[str, Any]] = []

        for item in root.rglob("*"):

            if len(results) >= max_results:
                break

            if not item.is_file():
                continue

            try:
                text = item.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            except OSError:
                continue

            if query.lower() not in text.lower():
                continue

            results.append(
                {
                    "path": str(
                        item.relative_to(
                            self.project_root
                        )
                    ),
                }
            )

        return {
            "query": query,
            "results": results,
            "count": len(results),
            "limit_reached": (
                len(results) >= max_results
            ),
        }


def build_default_registry(
    project_root: Path,
    *,
    include_protected: bool = False,
) -> ToolRegistry:

    registry = ToolRegistry()
    tools = ReadOnlyTools(project_root)

    registry.register(
        name="list_directory",
        description="List files and directories.",
        handler=tools.list_directory,
        read_only=True,
        requires_confirmation=False,
    )

    registry.register(
        name="read_file",
        description="Read a text file.",
        handler=tools.read_file,
        read_only=True,
        requires_confirmation=False,
    )

    registry.register(
        name="file_info",
        description="Inspect file metadata.",
        handler=tools.file_info,
        read_only=True,
        requires_confirmation=False,
    )

    registry.register(
        name="search_local_files",
        description="Search text inside project files.",
        handler=tools.search_local_files,
        read_only=True,
        requires_confirmation=False,
    )

    if include_protected:
        # Protected computer/UI control is opt-in. Permission remains the
        # responsibility of ToolPermissionGateway.
        from tools.computer_control_tool import ComputerControlTool
        computer_tool = ComputerControlTool()
        registry.register(
            name="computer_control",
            description="Control Android UI: click, swipe, type text, press keys, screenshot.",
            handler=computer_tool.execute,
            read_only=False,
            requires_confirmation=True,
            protected_action=ActionType.RUN_COMMAND,
        )

    return registry


def build_runtime_registry(project_root: Path) -> ToolRegistry:
    """Build the full runtime registry, including protected UI control."""
    return build_default_registry(
        project_root,
        include_protected=True,
    )
