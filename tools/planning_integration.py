from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.orchestrator.planner import Plan, PlanStep
from tools.human_approval import HumanApprovalGateway
from tools.invocation import ToolInvoker
from tools.result_handler import ToolResult, ToolResultHandler


@dataclass(frozen=True)
class PlannedToolExecutionResult:
    plan_id: str
    step_title: str
    tool: str
    allowed: bool
    success: bool
    requires_confirmation: bool
    result: Any
    error: str | None
    risk: str
    reason: str


class ToolPlanningGateway:
    """
    Connects planning to the existing tool-control pipeline.

    Planning describes the intended operation.
    ToolInvoker remains responsible for discovery, permission,
    and actual tool execution.
    ToolResultHandler normalizes the execution result.

    This gateway does not execute tools directly.
    """

    def __init__(
        self,
        tool_invoker: ToolInvoker,
        result_handler: ToolResultHandler,
        human_approval: HumanApprovalGateway | None = None,
    ) -> None:
        self.tool_invoker = tool_invoker
        self.result_handler = result_handler
        self.human_approval = human_approval or HumanApprovalGateway()

    def execute_step(
        self,
        plan: Plan,
        step: PlanStep,
        *,
        discovery_query: str,
        user_confirmation: bool = False,
        **kwargs: Any,
    ) -> PlannedToolExecutionResult:
        if not isinstance(plan, Plan):
            raise TypeError("plan must be a Plan.")

        if not isinstance(step, PlanStep):
            raise TypeError("step must be a PlanStep.")

        if not discovery_query.strip():
            raise ValueError("discovery_query cannot be empty.")

        # A planning step may require human approval.
        # The actual protected action mapping must be supplied by
        # the higher-level action classification layer. This gateway
        # therefore does not invent a protected action mapping.
        if step.requires_approval and not user_confirmation:
            return PlannedToolExecutionResult(
                plan_id=plan.plan_id,
                step_title=step.title,
                tool="",
                allowed=False,
                success=False,
                requires_confirmation=True,
                result=None,
                error=None,
                risk="unknown",
                reason="Planned step requires explicit user confirmation.",
            )

        invocation = self.tool_invoker.invoke(
            discovery_query,
            **kwargs,
        )

        normalized: ToolResult = self.result_handler.handle(invocation)

        return PlannedToolExecutionResult(
            plan_id=plan.plan_id,
            step_title=step.title,
            tool=normalized.tool,
            allowed=normalized.allowed,
            success=normalized.success,
            requires_confirmation=normalized.requires_confirmation,
            result=normalized.result,
            error=normalized.error,
            risk=normalized.risk,
            reason=normalized.reason,
        )
