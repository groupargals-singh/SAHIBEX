from __future__ import annotations

from pathlib import Path

from core.orchestrator.planner import Plan, PlanStep
from core.policies.approval import ActionType, PermissionEngine
from core.policies.constitution import (
    ActionClass,
    ActionDecision,
    SahibexConstitution,
)
from tools.discovery import ToolDiscovery
from tools.executor import SafeToolExecutor
from tools.failure_recovery import ToolFailureRecovery
from tools.human_approval import HumanApprovalGateway
from tools.intelligence import ToolIntelligence
from tools.invocation import ToolInvoker
from tools.permission_gateway import ToolPermissionGateway
from tools.planning_integration import ToolPlanningGateway
from tools.registry import ReadOnlyTools, ToolRegistry
from tools.result_handler import ToolResultHandler


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def build_system() -> tuple[
    ToolRegistry,
    ToolDiscovery,
    ToolPermissionGateway,
    ToolInvoker,
    ToolResultHandler,
    ToolFailureRecovery,
    ToolIntelligence,
    ToolPlanningGateway,
    HumanApprovalGateway,
]:
    project_root = Path.cwd()

    registry = ToolRegistry()
    read_only = ReadOnlyTools(project_root)

    registry.register(
        name="list_directory",
        description="List a project directory.",
        handler=read_only.list_directory,
        read_only=True,
        requires_confirmation=False,
    )

    registry.register(
        name="read_file",
        description="Read a local project file.",
        handler=read_only.read_file,
        read_only=True,
        requires_confirmation=False,
    )

    registry.register(
        name="file_info",
        description="Inspect local file information.",
        handler=read_only.file_info,
        read_only=True,
        requires_confirmation=False,
    )

    registry.register(
        name="search_local_files",
        description="Search local project files.",
        handler=read_only.search_local_files,
        read_only=True,
        requires_confirmation=False,
    )

    discovery = ToolDiscovery(registry)

    permission_gateway = ToolPermissionGateway(
        PermissionEngine(),
        registry,
    )

    executor = SafeToolExecutor(registry)

    invoker = ToolInvoker(
        discovery,
        permission_gateway,
        executor,
    )

    result_handler = ToolResultHandler()
    recovery = ToolFailureRecovery()

    intelligence = ToolIntelligence(
        tool_invoker=invoker,
        result_handler=result_handler,
        recovery=recovery,
    )

    human_approval = HumanApprovalGateway()

    planning_gateway = ToolPlanningGateway(
        tool_invoker=invoker,
        result_handler=result_handler,
        human_approval=human_approval,
    )

    return (
        registry,
        discovery,
        permission_gateway,
        invoker,
        result_handler,
        recovery,
        intelligence,
        planning_gateway,
        human_approval,
    )


def main() -> None:
    (
        registry,
        discovery,
        permission_gateway,
        invoker,
        result_handler,
        recovery,
        intelligence,
        planning_gateway,
        human_approval,
    ) = build_system()

    # ---------------------------------------------------------
    # 6K-1 — Tool Control / Registry
    # ---------------------------------------------------------
    tools = registry.list_tools()

    check(
        len(tools) == 4,
        "Default regression registry must contain four read-only tools.",
    )

    for tool in tools:
        check(
            tool.read_only is True,
            f"{tool.name} must remain read-only.",
        )
        check(
            tool.requires_confirmation is False,
            f"{tool.name} must not require confirmation.",
        )
        check(
            callable(tool.handler),
            f"{tool.name} handler must remain callable.",
        )

    # ---------------------------------------------------------
    # 6K-2 — Permission Gateway
    # ---------------------------------------------------------
    permission = permission_gateway.check("read_file")

    check(
        permission.allowed is True,
        "read_file must remain allowed.",
    )

    check(
        permission.action == ActionType.READ_FILE,
        "read_file must map to READ_FILE.",
    )

    check(
        permission.requires_confirmation is False,
        "read_file must not require confirmation.",
    )

    # ---------------------------------------------------------
    # 6K-3 — Discovery
    # ---------------------------------------------------------
    candidate = discovery.select("read file")

    check(
        candidate is not None,
        "read file query must discover a tool.",
    )

    check(
        candidate.name == "read_file",
        "read file query must select read_file.",
    )

    # ---------------------------------------------------------
    # 6K-4 — Invocation
    # ---------------------------------------------------------
    invocation = invoker.invoke(
        "read file",
        path="tools/registry.py",
        max_bytes=5000,
    )

    check(
        invocation.allowed is True,
        "read_file invocation must be allowed.",
    )

    check(
        invocation.success is True,
        "read_file invocation must succeed.",
    )

    check(
        invocation.tool == "read_file",
        "Invocation must preserve tool identity.",
    )

    # ---------------------------------------------------------
    # 6K-5 — Result Handling
    # ---------------------------------------------------------
    normalized = result_handler.handle(invocation)

    check(
        normalized.success is True,
        "Successful invocation must normalize successfully.",
    )

    check(
        normalized.tool == "read_file",
        "Normalized result must preserve tool identity.",
    )

    check(
        normalized.error is None,
        "Successful normalized result must have no error.",
    )

    # ---------------------------------------------------------
    # 6K-6 — Failure Recovery
    # ---------------------------------------------------------
    recovery_result = recovery.recover(
        invocation,
        attempts=1,
    )

    check(
        recovery_result.success is True,
        "Successful invocation must produce successful recovery state.",
    )

    check(
        recovery_result.status == "SUCCESS",
        "Successful recovery status must be SUCCESS.",
    )

    # ---------------------------------------------------------
    # 6K-7 — Computer Control Abstraction
    # ---------------------------------------------------------
    from tools.computer_control import (
        ComputerAction,
        ComputerControlProvider,
        ComputerControlRequest,
    )

    computer_provider = ComputerControlProvider()

    computer_request = ComputerControlRequest(
        action=ComputerAction.SCREENSHOT,
        parameters={},
    )

    computer_result = computer_provider.execute(
        computer_request
    )

    check(
        computer_result.success is False,
        "Unconnected computer control must not report success.",
    )

    check(
        computer_result.error is not None,
        "Unconnected computer control must report an error.",
    )

    # ---------------------------------------------------------
    # 6K-8 — Human Approval / Constitution
    # ---------------------------------------------------------
    constitution = SahibexConstitution()

    protected = constitution.decide(
        ActionClass.WRITE,
        user_confirmation=False,
    )

    check(
        protected.decision == ActionDecision.REQUIRE_CONFIRMATION,
        "WRITE must require explicit user authorization.",
    )

    protected_approved = constitution.decide(
        ActionClass.WRITE,
        user_confirmation=True,
    )

    check(
        protected_approved.decision == ActionDecision.ALLOW,
        "Explicit WRITE authorization must be allowed.",
    )

    approval = human_approval.check(
        ActionClass.WRITE,
        user_confirmation=False,
    )

    check(
        approval.allowed is False,
        "Human approval gateway must block WRITE without authorization.",
    )

    # ---------------------------------------------------------
    # 6K-9 — Planning Integration
    # ---------------------------------------------------------
    plan = Plan(
        title="Read project file",
        description="Safely read a project file.",
    )

    step = PlanStep(
        title="Read project file",
        description="Read tools/registry.py.",
        requires_approval=False,
    )

    planned = planning_gateway.execute_step(
        plan,
        step,
        discovery_query="read file",
        path="tools/registry.py",
        max_bytes=5000,
    )

    check(
        planned.success is True,
        "Planned read-only execution must succeed.",
    )

    check(
        planned.tool == "read_file",
        "Planned execution must preserve read_file.",
    )

    # Protected planned step must stop without approval.
    protected_step = PlanStep(
        title="Protected operation",
        description="Operation requiring approval.",
        requires_approval=True,
    )

    blocked = planning_gateway.execute_step(
        plan,
        protected_step,
        discovery_query="read file",
        path="tools/registry.py",
        max_bytes=5000,
    )

    check(
        blocked.success is False,
        "Protected planned step must not execute without approval.",
    )

    check(
        blocked.requires_confirmation is True,
        "Protected planned step must require confirmation.",
    )

    # ---------------------------------------------------------
    # 6K-10 — Tool Intelligence
    # ---------------------------------------------------------
    intelligent = intelligence.execute(
        "read file",
        path="tools/registry.py",
        max_bytes=5000,
    )

    check(
        intelligent.success is True,
        "Tool intelligence must successfully execute read_file.",
    )

    check(
        intelligent.tool == "read_file",
        "Tool intelligence must preserve selected tool.",
    )

    check(
        intelligent.attempts == 1,
        "Successful intelligence execution must use one attempt.",
    )

    check(
        intelligent.recovery_status == "SUCCESS",
        "Successful intelligence execution must report SUCCESS.",
    )

    unknown = intelligence.execute(
        "unknown tool that does not exist",
    )

    check(
        unknown.success is False,
        "Unknown tool must not succeed.",
    )

    check(
        unknown.allowed is False,
        "Unknown tool must not be allowed.",
    )

    check(
        unknown.recovery_status == "BLOCKED",
        "Unknown tool must be classified as BLOCKED.",
    )

    # ---------------------------------------------------------
    # Architecture safety checks
    # ---------------------------------------------------------
    check(
        not hasattr(planning_gateway, "execute_tool"),
        "Planning gateway must not expose direct execute_tool.",
    )

    check(
        not hasattr(planning_gateway, "invoke_tool"),
        "Planning gateway must not expose direct invoke_tool.",
    )

    check(
        not hasattr(discovery, "execute"),
        "Discovery must not execute tools directly.",
    )

    check(
        not hasattr(permission_gateway, "invoke"),
        "Permission gateway must not invoke tools directly.",
    )

    print(
        "SAHIBEX 6K-11 FULL TOOL-CONTROL REGRESSION TEST: PASS"
    )


if __name__ == "__main__":
    main()
