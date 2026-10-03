from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from tools.registry import (
    ToolDefinition,
    ToolRegistry,
    build_default_registry,
)


def check(condition: bool, message: str) -> None:
    assert condition, message
    print(f"[PASS] {message}")


def sample_handler(**kwargs):
    return kwargs


def main() -> None:
    print("=" * 60)
    print("SAHIBEX 6K-3 TOOL DISCOVERY CONTRACT TEST")
    print("=" * 60)

    registry = ToolRegistry()

    registry.register(
        name="sample_read",
        description="Read sample information.",
        handler=sample_handler,
        read_only=True,
        requires_confirmation=False,
    )

    registry.register(
        name="sample_search",
        description="Search sample information.",
        handler=sample_handler,
        read_only=True,
        requires_confirmation=False,
    )

    tools = registry.list_tools()

    check(
        len(tools) == 2,
        "registry exposes registered tools",
    )

    check(
        all(
            isinstance(tool, ToolDefinition)
            for tool in tools
        ),
        "registered entries are ToolDefinition objects",
    )

    names = {tool.name for tool in tools}

    check(
        names == {
            "sample_read",
            "sample_search",
        },
        "registered tool identities are preserved",
    )

    check(
        all(tool.description for tool in tools),
        "registered tools have descriptions",
    )

    check(
        all(callable(tool.handler) for tool in tools),
        "registered tools have callable handlers",
    )

    check(
        all(tool.read_only for tool in tools),
        "read-only metadata is preserved",
    )

    check(
        all(
            tool.requires_confirmation is False
            for tool in tools
        ),
        "confirmation metadata is preserved",
    )

    default_registry = build_default_registry(
        PROJECT_ROOT
    )

    default_tools = default_registry.list_tools()

    check(
        len(default_tools) == 4,
        "default registry exposes four tools",
    )

    default_names = {
        tool.name
        for tool in default_tools
    }

    check(
        default_names == {
            "list_directory",
            "read_file",
            "file_info",
            "search_local_files",
        },
        "default tool identities are preserved",
    )

    print("=" * 60)
    print("SAHIBEX 6K-3 TOOL DISCOVERY CONTRACT TEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
