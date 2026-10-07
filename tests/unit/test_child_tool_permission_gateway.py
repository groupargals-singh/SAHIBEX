from core.brain.child_tool_permission_gateway import (
    ChildToolPermissionGateway,
    ToolAction,
    ToolPermissionDecision,
    ToolPermissionRequest,
)


def main() -> None:
    gateway = ChildToolPermissionGateway()

    child_id = "child-brain-tool-001"

    # =========================================================
    # 1. Autonomous READ
    # =========================================================
    read_request = ToolPermissionRequest(
        request_id="tool-request-001",
        child_brain_id=child_id,
        tool_name="read_file",
        action=ToolAction.READ,
        purpose="read a project file",
    )

    result = gateway.evaluate(read_request)

    assert result.allowed is True
    assert (
        result.decision
        == ToolPermissionDecision.ALLOW_AUTONOMOUS
    )

    # =========================================================
    # 2. Autonomous RESEARCH
    # =========================================================
    research_request = ToolPermissionRequest(
        request_id="tool-request-002",
        child_brain_id=child_id,
        tool_name="research",
        action=ToolAction.RESEARCH,
        purpose="research AI security",
    )

    result = gateway.evaluate(research_request)

    assert result.allowed is True
    assert (
        result.decision
        == ToolPermissionDecision.ALLOW_AUTONOMOUS
    )

    # =========================================================
    # 3. WRITE requires Mother
    # =========================================================
    write_request = ToolPermissionRequest(
        request_id="tool-request-003",
        child_brain_id=child_id,
        tool_name="file_writer",
        action=ToolAction.WRITE,
        purpose="write approved code",
    )

    result = gateway.evaluate(write_request)

    assert result.allowed is False
    assert (
        result.decision
        == ToolPermissionDecision.REQUIRE_MOTHER
    )

    # =========================================================
    # 4. WRITE with Mother approval
    # =========================================================
    result = gateway.evaluate(
        write_request,
        mother_approved=True,
    )

    assert result.allowed is True
    assert (
        result.decision
        == ToolPermissionDecision.REQUIRE_MOTHER
    )

    # =========================================================
    # 5. EXECUTE requires Mother
    # =========================================================
    execute_request = ToolPermissionRequest(
        request_id="tool-request-004",
        child_brain_id=child_id,
        tool_name="code_executor",
        action=ToolAction.EXECUTE,
        purpose="execute approved test",
    )

    result = gateway.evaluate(execute_request)

    assert result.allowed is False
    assert (
        result.decision
        == ToolPermissionDecision.REQUIRE_MOTHER
    )

    # =========================================================
    # 6. FINANCIAL requires Human
    # =========================================================
    financial_request = ToolPermissionRequest(
        request_id="tool-request-005",
        child_brain_id=child_id,
        tool_name="financial_tool",
        action=ToolAction.FINANCIAL,
        purpose="perform financial operation",
    )

    result = gateway.evaluate(financial_request)

    assert result.allowed is False
    assert (
        result.decision
        == ToolPermissionDecision.REQUIRE_HUMAN
    )

    # =========================================================
    # 7. Financial with Human approval
    # =========================================================
    result = gateway.evaluate(
        financial_request,
        human_approved=True,
    )

    assert result.allowed is True
    assert (
        result.decision
        == ToolPermissionDecision.REQUIRE_HUMAN
    )

    # =========================================================
    # 8. Missing request identity
    # =========================================================
    invalid_request = ToolPermissionRequest(
        request_id="",
        child_brain_id=child_id,
        tool_name="read_file",
        action=ToolAction.READ,
        purpose="read",
    )

    result = gateway.evaluate(invalid_request)

    assert result.allowed is False
    assert result.decision == ToolPermissionDecision.DENY

    # =========================================================
    # 9. Missing tool identity
    # =========================================================
    invalid_request = ToolPermissionRequest(
        request_id="tool-request-006",
        child_brain_id=child_id,
        tool_name="",
        action=ToolAction.READ,
        purpose="read",
    )

    result = gateway.evaluate(invalid_request)

    assert result.allowed is False
    assert result.decision == ToolPermissionDecision.DENY

    # =========================================================
    # 10. Security boundaries
    # =========================================================
    assert not gateway.can_execute_tool()
    assert not gateway.can_tool_grant_authority()
    assert not gateway.can_child_self_authorize()
    assert not gateway.can_bypass_mother()
    assert not gateway.can_bypass_human()
    assert not gateway.can_modify_constitution()
    assert not gateway.can_modify_soul()
    assert not gateway.capability_is_authority()
    assert gateway.fails_closed()

    print("SAHIBEX CHILD TOOL PERMISSION GATEWAY TEST: PASS")


if __name__ == "__main__":
    main()
