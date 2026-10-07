from core.brain.child_tool_registry import (
    ChildToolRegistry,
    ToolCapability,
    ToolDefinition,
    ToolRegistryDecision,
)


def main() -> None:
    registry = ChildToolRegistry()

    # =========================================================
    # 1. Register READ tool
    # =========================================================
    read_tool = ToolDefinition(
        tool_id="tool-001",
        tool_name="read_file",
        capability=ToolCapability.READ,
        description="Read an approved file",
    )

    result = registry.register(read_tool)

    assert result.allowed is True
    assert result.decision == ToolRegistryDecision.REGISTERED
    assert result.tool is not None

    # =========================================================
    # 2. Retrieve registered tool
    # =========================================================
    result = registry.get("tool-001")

    assert result.allowed is True
    assert result.tool is not None
    assert result.tool.tool_name == "read_file"
    assert result.tool.capability == ToolCapability.READ

    # =========================================================
    # 3. Register EXECUTE capability
    # =========================================================
    execute_tool = ToolDefinition(
        tool_id="tool-002",
        tool_name="code_executor",
        capability=ToolCapability.EXECUTE,
        description="Execute approved code",
    )

    result = registry.register(execute_tool)

    assert result.allowed is True
    assert result.tool is not None
    assert result.tool.capability == ToolCapability.EXECUTE

    # =========================================================
    # 4. Unknown tool must fail closed
    # =========================================================
    result = registry.get("unknown-tool")

    assert result.allowed is False
    assert result.decision == ToolRegistryDecision.NOT_FOUND
    assert result.tool is None

    # =========================================================
    # 5. Duplicate tool identity denied
    # =========================================================
    duplicate_tool = ToolDefinition(
        tool_id="tool-001",
        tool_name="another_tool",
        capability=ToolCapability.WRITE,
        description="Duplicate identity test",
    )

    result = registry.register(duplicate_tool)

    assert result.allowed is False
    assert result.decision == ToolRegistryDecision.DENIED

    # =========================================================
    # 6. Disabled tool denied
    # =========================================================
    disabled_tool = ToolDefinition(
        tool_id="tool-003",
        tool_name="disabled_tool",
        capability=ToolCapability.WRITE,
        description="Disabled tool",
        enabled=False,
    )

    result = registry.register(disabled_tool)

    assert result.allowed is True

    result = registry.get("tool-003")

    assert result.allowed is False
    assert result.decision == ToolRegistryDecision.DENIED

    # =========================================================
    # 7. Missing identity denied
    # =========================================================
    invalid_tool = ToolDefinition(
        tool_id="",
        tool_name="invalid",
        capability=ToolCapability.READ,
        description="Invalid identity",
    )

    result = registry.register(invalid_tool)

    assert result.allowed is False
    assert result.decision == ToolRegistryDecision.DENIED

    # =========================================================
    # 8. Registry must never become authority
    # =========================================================
    assert not registry.can_execute_tool()
    assert not registry.can_grant_authority()
    assert not registry.can_modify_constitution()
    assert not registry.can_modify_soul()
    assert not registry.capability_is_authority()

    # =========================================================
    # 9. Fail-closed guarantees
    # =========================================================
    assert registry.unknown_tool_fails_closed()
    assert registry.duplicate_identity_fails_closed()

    # =========================================================
    # 10. Registry contains expected tools
    # =========================================================
    tools = registry.list_tools()

    assert len(tools) == 3
    assert tools[0].tool_id == "tool-001"
    assert tools[1].tool_id == "tool-002"
    assert tools[2].tool_id == "tool-003"

    print("SAHIBEX CHILD TOOL REGISTRY TEST: PASS")


if __name__ == "__main__":
    main()
