from __future__ import annotations

from pathlib import Path

from core.orchestrator.planner import Plan, PlanStep
from core.policies.approval import PermissionEngine
from core.policies.constitution import ActionClass
from tools.discovery import ToolDiscovery
from tools.executor import SafeToolExecutor
from tools.human_approval import HumanApprovalGateway
from tools.invocation import ToolInvoker
from tools.permission_gateway import ToolPermissionGateway
from tools.planning_integration import ToolPlanningGateway
from tools.registry import ReadOnlyTools, ToolRegistry
from tools.result_handler import ToolResultHandler


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def build_tool_invoker(project_root: Path) -> ToolInvoker:
    registry = ToolRegistry()
    read_only = ReadOnlyTools(project_root)

    registry.register(
        name="read_file",
        description="Read a local project file.",
        handler=read_only.read_file,
        read_only=True,
        requires_confirmation=False,
    )

    discovery = ToolDiscovery(registry)
    permission_gateway = ToolPermissionGateway(
        PermissionEngine(),
        registry,
    )
    executor = SafeToolExecutor(registry)

    return ToolInvoker(
        discovery,
        permission_gateway,
        executor,
    )


def main() -> None:
    project_root = Path.cwd()

    invoker = build_tool_invoker(project_root)

    result_handler = ToolResultHandler()
    human_approval = HumanApprovalGateway()

    gateway = ToolPlanningGateway(
        tool_invoker=invoker,
        result_handler=result_handler,
        human_approval=human_approval,
    )

    # ---------------------------------------------------------
    # 1. Create a real plan.
    # ---------------------------------------------------------
    plan = Plan(
        title="Read project file",
        description="Safely inspect a local file.",
    )

    check(
        plan.plan_id != "",
        "Plan must have a generated plan_id.",
    )

    # ---------------------------------------------------------
    # 2. Read-only planned step should execute through ToolInvoker.
    # ---------------------------------------------------------
    step = PlanStep(
        title="Read project file",
        description="Read a known project file.",
        requires_approval=False,
    )

    result = gateway.execute_step(
        plan,
        step,
        discovery_query="read file",
        path="tools/registry.py",
        max_bytes=5000,
    )

    check(
        result.plan_id == plan.plan_id,
        "Execution result must preserve plan_id.",
    )

    check(
        result.step_title == step.title,
        "Execution result must preserve step title.",
    )

    check(
        result.tool == "read_file",
        "Planning gateway must select read_file.",
    )

    check(
        result.allowed is True,
        "Read-only tool execution must be allowed.",
    )

    check(
        result.success is True,
        "Read-only tool execution must succeed.",
    )

    check(
        result.error is None,
        "Successful execution must not contain an error.",
    )

    # ---------------------------------------------------------
    # 3. Planned approval-required step must stop without
    #    explicit confirmation.
    # ---------------------------------------------------------
    protected_step = PlanStep(
        title="Protected operation",
        description="Operation requiring human approval.",
        requires_approval=True,
    )

    blocked = gateway.execute_step(
        plan,
        protected_step,
        discovery_query="read file",
        path="tools/registry.py",
        max_bytes=5000,
    )

    check(
        blocked.allowed is False,
        "Approval-required step must not execute without approval.",
    )

    check(
        blocked.success is False,
        "Blocked approval step must not report success.",
    )

    check(
        blocked.requires_confirmation is True,
        "Approval-required step must request confirmation.",
    )

    check(
        blocked.tool == "",
        "Blocked step must not execute or select a tool.",
    )

    # ---------------------------------------------------------
    # 4. HumanApprovalGateway itself must preserve root
    #    authority semantics.
    # ---------------------------------------------------------
    approval = human_approval.check(
        ActionClass.WRITE,
        user_confirmation=False,
    )

    check(
        approval.allowed is False,
        "WRITE must require user approval.",
    )

    check(
        approval.requires_confirmation is True,
        "WRITE must require confirmation.",
    )

    approved = human_approval.check(
        ActionClass.WRITE,
        user_confirmation=True,
    )

    check(
        approved.allowed is True,
        "Explicit user authorization must allow WRITE.",
    )

    # ---------------------------------------------------------
    # 5. Planning gateway must not directly expose tool
    #    execution methods.
    # ---------------------------------------------------------
    check(
        not hasattr(gateway, "execute_tool"),
        "Planning gateway must not expose execute_tool.",
    )

    check(
        not hasattr(gateway, "invoke_tool"),
        "Planning gateway must not expose invoke_tool.",
    )

    print("SAHIBEX 6K-9 TOOL-PLANNING INTEGRATION RUNTIME TEST: PASS")


if __name__ == "__main__":
    main()
