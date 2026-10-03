from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from core.policies.approval import PermissionEngine
from tools.discovery import ToolDiscovery
from tools.executor import SafeToolExecutor
from tools.invocation import ToolInvoker
from tools.permission_gateway import ToolPermissionGateway
from tools.registry import ReadOnlyTools, ToolRegistry


def build_runtime() -> tuple[
    ToolInvoker,
    ToolRegistry,
    TemporaryDirectory[str],
]:
    temp_dir = TemporaryDirectory()
    project_root = Path(temp_dir.name)

    (project_root / "app").mkdir()

    (project_root / "app" / "main.py").write_text(
        "print('SAHIBEX')\n",
        encoding="utf-8",
    )

    (project_root / "app" / "config.txt").write_text(
        "SAHIBEX configuration\n",
        encoding="utf-8",
    )

    tools = ReadOnlyTools(project_root)

    registry = ToolRegistry()

    registry.register(
        name="list_directory",
        description="List files and directories.",
        handler=tools.list_directory,
        read_only=True,
        requires_confirmation=False,
    )

    registry.register(
        name="read_file",
        description="Read a file.",
        handler=tools.read_file,
        read_only=True,
        requires_confirmation=False,
    )

    registry.register(
        name="file_info",
        description="Get file information.",
        handler=tools.file_info,
        read_only=True,
        requires_confirmation=False,
    )

    registry.register(
        name="search_local_files",
        description="Search text inside local files.",
        handler=tools.search_local_files,
        read_only=True,
        requires_confirmation=False,
    )

    discovery = ToolDiscovery(registry)

    permission_engine = PermissionEngine()

    permission_gateway = ToolPermissionGateway(
        permission_engine,
        registry,
    )

    executor = SafeToolExecutor(registry)

    invoker = ToolInvoker(
        discovery,
        permission_gateway,
        executor,
    )

    return (
        invoker,
        registry,
        temp_dir,
    )


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    invoker, registry, temp_dir = build_runtime()

    try:
        # -------------------------------------------------
        # 1. Runtime dependencies
        # -------------------------------------------------

        check(
            invoker.discovery is not None,
            "Invoker must preserve discovery.",
        )

        check(
            invoker.permission_gateway is not None,
            "Invoker must preserve permission gateway.",
        )

        check(
            invoker.executor is not None,
            "Invoker must preserve executor.",
        )

        # -------------------------------------------------
        # 2. Registered tools
        # -------------------------------------------------

        check(
            registry.has("list_directory"),
            "list_directory must be registered.",
        )

        check(
            registry.has("read_file"),
            "read_file must be registered.",
        )

        check(
            registry.has("file_info"),
            "file_info must be registered.",
        )

        check(
            registry.has("search_local_files"),
            "search_local_files must be registered.",
        )

        # -------------------------------------------------
        # 3. list_directory invocation
        # -------------------------------------------------

        result = invoker.invoke(
            "list files",
            path="app",
        )

        check(
            result.tool == "list_directory",
            "list_directory should be selected.",
        )

        check(
            result.allowed is True,
            "list_directory should be allowed.",
        )

        check(
            result.success is True,
            "list_directory should execute successfully.",
        )

        check(
            result.error is None,
            "Successful execution should have no error.",
        )

        # -------------------------------------------------
        # 4. read_file invocation
        # -------------------------------------------------

        result = invoker.invoke(
            "read file",
            path="app/main.py",
        )

        check(
            result.tool == "read_file",
            "read_file should be selected.",
        )

        check(
            result.allowed is True,
            "read_file should be allowed.",
        )

        check(
            result.success is True,
            "read_file should execute successfully.",
        )

        check(
            "SAHIBEX" in result.result["content"],
            "read_file should return expected content.",
        )

        # -------------------------------------------------
        # 5. search_local_files invocation
        # -------------------------------------------------

        result = invoker.invoke(
            "search text",
            query="SAHIBEX",
            path="app",
        )

        check(
            result.tool == "search_local_files",
            "search_local_files should be selected.",
        )

        check(
            result.allowed is True,
            "search_local_files should be allowed.",
        )

        check(
            result.success is True,
            "search_local_files should execute successfully.",
        )

        check(
            isinstance(result.result, dict),
            "Search result must be a dictionary.",
        )

        check(
            result.result["query"] == "SAHIBEX",
            "Search result must preserve the query.",
        )

        check(
            "results" in result.result,
            "Search result must contain results.",
        )

        check(
            len(result.result["results"]) >= 1,
            "Search should return at least one result.",
        )

        check(
            result.result["count"] >= 1,
            "Search result count should be at least one.",
        )

        # -------------------------------------------------
        # 6. file_info invocation
        # -------------------------------------------------

        result = invoker.invoke(
            "file information",
            path="app/main.py",
        )

        check(
            result.tool == "file_info",
            "file_info should be selected.",
        )

        check(
            result.allowed is True,
            "file_info should be allowed.",
        )

        check(
            result.success is True,
            "file_info should execute successfully.",
        )

        # -------------------------------------------------
        # 7. Unknown discovery query
        # -------------------------------------------------

        result = invoker.invoke(
            "completely unknown operation",
        )

        check(
            result.allowed is False,
            "Unknown discovery query must not be allowed.",
        )

        check(
            result.success is False,
            "Unknown discovery query must not execute.",
        )

        check(
            result.tool == "",
            "Unknown discovery query must have empty tool.",
        )

        check(
            result.error is not None,
            "Unknown discovery query must return an error.",
        )

        # -------------------------------------------------
        # 8. Invocation metadata
        # -------------------------------------------------

        result = invoker.invoke(
            "read file",
            path="app/config.txt",
        )

        check(
            result.risk == "low",
            "Read-only tool invocation should be low risk.",
        )

        check(
            result.requires_confirmation is False,
            "Read-only tool should not require confirmation.",
        )

        check(
            result.reason != "",
            "Invocation must provide a reason.",
        )

        print(
            "SAHIBEX 6K-4 TOOL INVOCATION RUNTIME TEST: PASS"
        )

    finally:
        temp_dir.cleanup()


if __name__ == "__main__":
    main()
