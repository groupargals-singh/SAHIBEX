from pathlib import Path

from tools.registry import (
    ToolDefinition,
    ToolRegistry,
    build_default_registry,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def tool_handler(value: str = "ok") -> dict:
    return {
        "value": value,
    }


def test_tool_handler_contract() -> None:
    assert tool_handler() == {"value": "ok"}


def main() -> None:
    print("SAHIBEX 6K-1 TOOL CONTROL CONTRACT TEST")

    # ==================================================
    # ToolDefinition contract
    # ==================================================

    tool = ToolDefinition(
        name="test_tool",
        description="Tool control contract test tool",
        handler=tool_handler,
        read_only=True,
        requires_confirmation=False,
    )

    check(
        tool.name == "test_tool",
        "tool name is preserved",
    )

    check(
        tool.description
        == "Tool control contract test tool",
        "tool description is preserved",
    )

    check(
        callable(tool.handler),
        "tool handler is callable",
    )

    check(
        tool.read_only is True,
        "tool read-only flag is preserved",
    )

    check(
        tool.requires_confirmation is False,
        "tool confirmation flag is preserved",
    )

    # ==================================================
    # ToolRegistry contract
    # ==================================================

    registry = ToolRegistry()

    registry.register(
        name="test_tool",
        description="Tool control contract test tool",
        handler=tool_handler,
        read_only=True,
        requires_confirmation=False,
    )

    check(
        registry.has("test_tool"),
        "registered tool can be detected",
    )

    resolved = registry.get("test_tool")

    check(
        resolved.name == "test_tool",
        "registry preserves tool name",
    )

    check(
        resolved.description
        == "Tool control contract test tool",
        "registry preserves tool description",
    )

    check(
        resolved.handler is tool_handler,
        "registry preserves handler identity",
    )

    check(
        resolved.read_only is True,
        "registry preserves read-only state",
    )

    check(
        resolved.requires_confirmation is False,
        "registry preserves confirmation state",
    )

    check(
        len(registry.list_tools()) == 1,
        "registry contains registered tool",
    )

    # ==================================================
    # Duplicate protection
    # ==================================================

    duplicate_blocked = False

    try:
        registry.register(
            name="test_tool",
            description="Duplicate tool",
            handler=tool_handler,
            read_only=True,
            requires_confirmation=False,
        )
    except ValueError:
        duplicate_blocked = True

    check(
        duplicate_blocked,
        "duplicate tool registration is blocked",
    )

    # ==================================================
    # Empty-name protection
    # ==================================================

    empty_name_blocked = False

    try:
        registry.register(
            name="",
            description="Invalid tool",
            handler=tool_handler,
            read_only=True,
            requires_confirmation=False,
        )
    except ValueError:
        empty_name_blocked = True

    check(
        empty_name_blocked,
        "empty tool name is blocked",
    )

    # ==================================================
    # Unknown-tool protection
    # ==================================================

    unknown_tool_blocked = False

    try:
        registry.get("unknown_tool")
    except KeyError:
        unknown_tool_blocked = True

    check(
        unknown_tool_blocked,
        "unknown tool lookup is rejected",
    )

    check(
        registry.has("unknown_tool") is False,
        "unknown tool is reported as unavailable",
    )

    # ==================================================
    # Default SAHIBEX tool registry
    # ==================================================

    project_root = Path(__file__).resolve().parents[2]

    default_registry = build_default_registry(
        project_root
    )

    expected_tools = {
        "list_directory",
        "read_file",
        "file_info",
        "search_local_files",
    }

    actual_tools = {
        item.name
        for item in default_registry.list_tools()
    }

    check(
        actual_tools == expected_tools,
        "default SAHIBEX tool set is preserved",
    )

    # ==================================================
    # Default tool safety contract
    # ==================================================

    for item in default_registry.list_tools():

        check(
            item.read_only is True,
            f"{item.name} is read-only",
        )

        check(
            item.requires_confirmation is False,
            f"{item.name} does not require confirmation",
        )

        check(
            callable(item.handler),
            f"{item.name} has a callable handler",
        )

        check(
            bool(item.description.strip()),
            f"{item.name} has a non-empty description",
        )

    # ==================================================
    # Final
    # ==================================================

    print(
        "SAHIBEX 6K-1 TOOL CONTROL CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
