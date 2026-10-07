from core.brain.child_tool_permission_gateway import (
    ChildToolPermissionGateway,
    ToolAction,
)

from core.brain.child_tool_registry import (
    ChildToolRegistry,
    ToolCapability,
    ToolDefinition,
)

from core.brain.child_tool_execution_boundary import (
    ChildToolExecutionBoundary,
)

from core.brain.child_tool_execution_orchestrator import (
    ChildToolExecutionOrchestrator,
    OrchestratorDecision,
    ToolOrchestrationRequest,
)


def main() -> None:
    permission_gateway = ChildToolPermissionGateway()
    registry = ChildToolRegistry()
    execution_boundary = ChildToolExecutionBoundary()

    orchestrator = ChildToolExecutionOrchestrator(
        permission_gateway=permission_gateway,
        registry=registry,
        execution_boundary=execution_boundary,
    )

    child_id = "child-brain-orchestrator-001"

    # =========================================================
    # 1. Register READ tool
    # =========================================================
    read_tool = ToolDefinition(
        tool_id="tool-read-001",
        tool_name="read_file",
        capability=ToolCapability.READ,
        description="Read approved project file",
    )

    register_result = registry.register(read_tool)

    assert register_result.allowed is True

    # =========================================================
    # 2. Valid autonomous READ request
    # =========================================================
    read_request = ToolOrchestrationRequest(
        request_id="orchestrator-001",
        child_brain_id=child_id,
        tool_id="tool-read-001",
        tool_name="read_file",
        action=ToolAction.READ,
        purpose="read approved project file",
    )

    result = orchestrator.evaluate(read_request)

    assert result.allowed is True
    assert result.decision == OrchestratorDecision.ALLOW

    # =========================================================
    # 3. WRITE blocked without Mother approval
    # =========================================================
    write_tool = ToolDefinition(
        tool_id="tool-write-001",
        tool_name="file_writer",
        capability=ToolCapability.WRITE,
        description="Write approved project data",
    )

    register_result = registry.register(write_tool)

    assert register_result.allowed is True

    write_request = ToolOrchestrationRequest(
        request_id="orchestrator-002",
        child_brain_id=child_id,
        tool_id="tool-write-001",
        tool_name="file_writer",
        action=ToolAction.WRITE,
        purpose="write approved project data",
        mother_approved=False,
    )

    result = orchestrator.evaluate(write_request)

    assert result.allowed is False
    assert result.decision == OrchestratorDecision.BLOCK

    # =========================================================
    # 4. WRITE passes with Mother approval
    # =========================================================
    write_request = ToolOrchestrationRequest(
        request_id="orchestrator-003",
        child_brain_id=child_id,
        tool_id="tool-write-001",
        tool_name="file_writer",
        action=ToolAction.WRITE,
        purpose="write approved project data",
        mother_approved=True,
    )

    result = orchestrator.evaluate(write_request)

    assert result.allowed is True
    assert result.decision == OrchestratorDecision.ALLOW

    # =========================================================
    # 5. Unknown tool blocked
    # =========================================================
    unknown_request = ToolOrchestrationRequest(
        request_id="orchestrator-004",
        child_brain_id=child_id,
        tool_id="unknown-tool",
        tool_name="unknown",
        action=ToolAction.READ,
        purpose="unknown operation",
    )

    result = orchestrator.evaluate(unknown_request)

    assert result.allowed is False
    assert result.decision == OrchestratorDecision.BLOCK

    # =========================================================
    # 6. Tool identity mismatch blocked
    # =========================================================
    mismatch_request = ToolOrchestrationRequest(
        request_id="orchestrator-005",
        child_brain_id=child_id,
        tool_id="tool-read-001",
        tool_name="different_tool",
        action=ToolAction.READ,
        purpose="identity mismatch test",
    )

    result = orchestrator.evaluate(mismatch_request)

    assert result.allowed is False
    assert result.decision == OrchestratorDecision.BLOCK

    # =========================================================
    # 7. Financial action requires Human
    # =========================================================
    financial_tool = ToolDefinition(
        tool_id="tool-financial-001",
        tool_name="financial_tool",
        capability=ToolCapability.FINANCIAL,
        description="Perform approved financial operation",
    )

    register_result = registry.register(financial_tool)

    assert register_result.allowed is True

    financial_request = ToolOrchestrationRequest(
        request_id="orchestrator-006",
        child_brain_id=child_id,
        tool_id="tool-financial-001",
        tool_name="financial_tool",
        action=ToolAction.FINANCIAL,
        purpose="perform approved financial operation",
        mother_approved=True,
        human_approved=False,
    )

    result = orchestrator.evaluate(financial_request)

    assert result.allowed is False
    assert result.decision == OrchestratorDecision.BLOCK

    # =========================================================
    # 8. Financial action passes with Human approval
    # =========================================================
    financial_request = ToolOrchestrationRequest(
        request_id="orchestrator-007",
        child_brain_id=child_id,
        tool_id="tool-financial-001",
        tool_name="financial_tool",
        action=ToolAction.FINANCIAL,
        purpose="perform approved financial operation",
        mother_approved=True,
        human_approved=True,
    )

    result = orchestrator.evaluate(financial_request)

    assert result.allowed is True
    assert result.decision == OrchestratorDecision.ALLOW

    # =========================================================
    # 9. Orchestrator never executes directly
    # =========================================================
    assert not orchestrator.execute_real_tool()
    assert not orchestrator.execute_shell_command()
    assert not orchestrator.execute_network_request()
    assert not orchestrator.execute_filesystem_write()

    # =========================================================
    # 10. Orchestrator cannot grant or bypass authority
    # =========================================================
    assert not orchestrator.grant_authority()
    assert not orchestrator.bypass_permission()

    # =========================================================
    # 11. Security invariants
    # =========================================================
    assert orchestrator.fails_closed()
    assert not orchestrator.capability_is_authority()

    print("SAHIBEX CHILD TOOL EXECUTION ORCHESTRATOR TEST: PASS")


if __name__ == "__main__":
    main()
