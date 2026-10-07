from core.brain.child_tool_execution_boundary import (
    ChildToolExecutionBoundary,
    ExecutionDecision,
    ToolExecutionRequest,
)


def main() -> None:
    boundary = ChildToolExecutionBoundary()

    child_id = "child-brain-execution-001"

    # =========================================================
    # 1. Valid permission-gated execution request
    # =========================================================
    request = ToolExecutionRequest(
        request_id="execution-001",
        child_brain_id=child_id,
        tool_id="tool-001",
        tool_name="approved_tool",
        permission_granted=True,
        purpose="perform approved operation",
    )

    result = boundary.evaluate(request)

    assert result.allowed is True
    assert result.decision == ExecutionDecision.ALLOW

    # =========================================================
    # 2. Permission missing
    # =========================================================
    request = ToolExecutionRequest(
        request_id="execution-002",
        child_brain_id=child_id,
        tool_id="tool-001",
        tool_name="approved_tool",
        permission_granted=False,
        purpose="perform operation",
    )

    result = boundary.evaluate(request)

    assert result.allowed is False
    assert (
        result.decision
        == ExecutionDecision.REQUIRE_PERMISSION
    )

    # =========================================================
    # 3. Missing request identity
    # =========================================================
    request = ToolExecutionRequest(
        request_id="",
        child_brain_id=child_id,
        tool_id="tool-001",
        tool_name="approved_tool",
        permission_granted=True,
        purpose="test",
    )

    result = boundary.evaluate(request)

    assert result.allowed is False
    assert result.decision == ExecutionDecision.DENY

    # =========================================================
    # 4. Missing child identity
    # =========================================================
    request = ToolExecutionRequest(
        request_id="execution-003",
        child_brain_id="",
        tool_id="tool-001",
        tool_name="approved_tool",
        permission_granted=True,
        purpose="test",
    )

    result = boundary.evaluate(request)

    assert result.allowed is False
    assert result.decision == ExecutionDecision.DENY

    # =========================================================
    # 5. Missing tool identity
    # =========================================================
    request = ToolExecutionRequest(
        request_id="execution-004",
        child_brain_id=child_id,
        tool_id="",
        tool_name="approved_tool",
        permission_granted=True,
        purpose="test",
    )

    result = boundary.evaluate(request)

    assert result.allowed is False
    assert result.decision == ExecutionDecision.DENY

    # =========================================================
    # 6. Missing purpose
    # =========================================================
    request = ToolExecutionRequest(
        request_id="execution-005",
        child_brain_id=child_id,
        tool_id="tool-001",
        tool_name="approved_tool",
        permission_granted=True,
        purpose="",
    )

    result = boundary.evaluate(request)

    assert result.allowed is False
    assert result.decision == ExecutionDecision.DENY

    # =========================================================
    # 7. Boundary must never execute directly
    # =========================================================
    assert not boundary.execute_tool()
    assert not boundary.execute_shell_command()
    assert not boundary.execute_unknown_tool()

    # =========================================================
    # 8. Boundary cannot grant authority
    # =========================================================
    assert not boundary.bypass_permission()
    assert not boundary.grant_permission()
    assert not boundary.grant_authority()

    # =========================================================
    # 9. Constitutional / soul protection
    # =========================================================
    assert not boundary.modify_constitution()
    assert not boundary.modify_soul()

    # =========================================================
    # 10. Security invariants
    # =========================================================
    assert boundary.fails_closed()
    assert not boundary.capability_is_authority()

    print("SAHIBEX CHILD TOOL EXECUTION BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
