from core.brain.child_tool_permission_gateway import (
    ChildToolPermissionGateway,
    ToolAction,
    ToolPermissionRequest,
    ToolPermissionDecision,
)

from core.brain.child_tool_registry import (
    ChildToolRegistry,
    ToolCapability,
    ToolDefinition,
    ToolRegistryDecision,
)

from core.brain.child_tool_execution_boundary import (
    ChildToolExecutionBoundary,
    ExecutionDecision,
    ToolExecutionRequest,
)


def main() -> None:
    permission_gateway = ChildToolPermissionGateway()
    registry = ChildToolRegistry()
    execution_boundary = ChildToolExecutionBoundary()

    child_id = "child-brain-tool-pipeline-001"

    # =========================================================
    # 1. Register approved tool
    # =========================================================
    tool = ToolDefinition(
        tool_id="tool-read-001",
        tool_name="read_file",
        capability=ToolCapability.READ,
        description="Read an approved file",
    )

    registry_result = registry.register(tool)

    assert registry_result.allowed is True
    assert (
        registry_result.decision
        == ToolRegistryDecision.REGISTERED
    )

    # =========================================================
    # 2. Child requests READ permission
    # =========================================================
    permission_request = ToolPermissionRequest(
        request_id="pipeline-001",
        child_brain_id=child_id,
        tool_name="read_file",
        action=ToolAction.READ,
        purpose="read approved project file",
    )

    permission_result = permission_gateway.evaluate(
        permission_request
    )

    assert permission_result.allowed is True
    assert (
        permission_result.decision
        == ToolPermissionDecision.ALLOW_AUTONOMOUS
    )

    # =========================================================
    # 3. Registry confirms tool identity
    # =========================================================
    registered_tool = registry.get("tool-read-001")

    assert registered_tool.allowed is True
    assert registered_tool.tool is not None
    assert registered_tool.tool.tool_name == "read_file"

    # =========================================================
    # 4. Execution boundary receives permission
    # =========================================================
    execution_request = ToolExecutionRequest(
        request_id="pipeline-001",
        child_brain_id=child_id,
        tool_id=registered_tool.tool.tool_id,
        tool_name=registered_tool.tool.tool_name,
        permission_granted=permission_result.allowed,
        purpose="read approved project file",
    )

    execution_result = execution_boundary.evaluate(
        execution_request
    )

    assert execution_result.allowed is True
    assert (
        execution_result.decision
        == ExecutionDecision.ALLOW
    )

    # =========================================================
    # 5. Protected WRITE must stop without Mother approval
    # =========================================================
    write_permission_request = ToolPermissionRequest(
        request_id="pipeline-002",
        child_brain_id=child_id,
        tool_name="file_writer",
        action=ToolAction.WRITE,
        purpose="write approved file",
    )

    write_permission = permission_gateway.evaluate(
        write_permission_request
    )

    assert write_permission.allowed is False
    assert (
        write_permission.decision
        == ToolPermissionDecision.REQUIRE_MOTHER
    )

    # =========================================================
    # 6. Therefore execution permission must remain blocked
    # =========================================================
    blocked_execution = ToolExecutionRequest(
        request_id="pipeline-002",
        child_brain_id=child_id,
        tool_id="tool-write-001",
        tool_name="file_writer",
        permission_granted=write_permission.allowed,
        purpose="write approved file",
    )

    blocked_result = execution_boundary.evaluate(
        blocked_execution
    )

    assert blocked_result.allowed is False
    assert (
        blocked_result.decision
        == ExecutionDecision.REQUIRE_PERMISSION
    )

    # =========================================================
    # 7. Unknown tool must fail closed
    # =========================================================
    unknown_tool = registry.get("unknown-tool")

    assert unknown_tool.allowed is False
    assert (
        unknown_tool.decision
        == ToolRegistryDecision.NOT_FOUND
    )

    # =========================================================
    # 8. Registry and execution cannot grant authority
    # =========================================================
    assert not registry.can_execute_tool()
    assert not registry.can_grant_authority()

    assert not execution_boundary.grant_permission()
    assert not execution_boundary.grant_authority()

    # =========================================================
    # 9. No direct execution
    # =========================================================
    assert not execution_boundary.execute_tool()
    assert not execution_boundary.execute_shell_command()
    assert not execution_boundary.execute_unknown_tool()

    # =========================================================
    # 10. Constitutional protection
    # =========================================================
    assert not permission_gateway.can_modify_constitution()
    assert not permission_gateway.can_modify_soul()
    assert not registry.can_modify_constitution()
    assert not registry.can_modify_soul()
    assert not execution_boundary.modify_constitution()
    assert not execution_boundary.modify_soul()

    # =========================================================
    # 11. Fail-closed guarantees
    # =========================================================
    assert permission_gateway.fails_closed()
    assert registry.unknown_tool_fails_closed()
    assert execution_boundary.fails_closed()

    # =========================================================
    # FINAL RESULT
    # =========================================================
    print("SAHIBEX CHILD TOOL SECURITY PIPELINE TEST: PASS")


if __name__ == "__main__":
    main()
