from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any

from core.brain.master_brain import BrainResult, MasterBrain
from core.brain.observability_expansion import (
    ObservationEvent,
    ObservabilityEngine,
)
from core.brain.recovery_controller import RecoveryController
from tools.discovery import ToolDiscovery
from tools.executor import SafeToolExecutor
from tools.invocation import ToolInvocationResult, ToolInvoker
from tools.permission_gateway import ToolPermissionGateway
from tools.registry import ToolRegistry, build_default_registry
from tools.result_handler import ToolResult, ToolResultHandler


@dataclass(frozen=True)
class ExecutionLoopResult:
    """Single authoritative result for one SAHIBEX request lifecycle."""

    success: bool
    status: str
    request: str
    brain: BrainResult
    tool: ToolResult | None
    recovery_state: str
    observation_count: int
    response: str
    metadata: dict[str, Any] = field(default_factory=dict)


class SahibexExecutionLoop:
    """
    Commissioned Main-Brain execution loop.

    Lifecycle:
        INPUT
          -> UNDERSTAND / AUTHORIZE / VERIFY / REASON
          -> PLAN
          -> OPTIONAL TOOL DISCOVERY / PERMISSION / EXECUTION
          -> RESULT VERIFICATION
          -> RECOVERY ON SAFE RETRYABLE FAILURE
          -> OBSERVATION
          -> FINAL RESPONSE

    This class is an orchestration boundary. It never grants authority,
    changes the Constitution, or executes protected actions by itself.
    Protected execution remains behind the existing permission gateways.
    """

    VERSION = "1.0"

    def __init__(
        self,
        *,
        brain: MasterBrain | None = None,
        project_root: Path | None = None,
        registry: ToolRegistry | None = None,
    ) -> None:
        self.brain = brain or MasterBrain()
        self.project_root = (
            Path(project_root).resolve()
            if project_root is not None
            else Path.cwd().resolve()
        )
        self.registry = registry or build_default_registry(
            self.project_root,
            include_protected=False,
        )
        self.discovery = ToolDiscovery(self.registry)
        self.tool_permissions = ToolPermissionGateway(
            self.brain.permission,
            self.registry,
        )
        self.executor = SafeToolExecutor(self.registry)
        self.invoker = ToolInvoker(
            self.discovery,
            self.tool_permissions,
            self.executor,
        )
        self.results = ToolResultHandler()
        self.recovery = RecoveryController()
        self.observability = ObservabilityEngine()

    def process(
        self,
        request: str,
        *,
        user_confirmation: bool = False,
    ) -> ExecutionLoopResult:
        if not isinstance(request, str):
            raise TypeError("request must be a string.")
        if not request.strip():
            brain_result = self.brain.process(
                request,
                user_confirmation=user_confirmation,
            )
            self._observe(
                request=request,
                brain=brain_result,
                status="BLOCKED",
            )
            return ExecutionLoopResult(
                success=False,
                status="BLOCKED",
                request=request,
                brain=brain_result,
                tool=None,
                recovery_state=self.recovery.state.value,
                observation_count=len(self.observability.snapshot()),
                response=brain_result.message,
                metadata={"loop_version": self.VERSION},
            )

        brain_result = self.brain.process(
            request,
            user_confirmation=user_confirmation,
        )

        if (
            brain_result.confirmation_required
            and not brain_result.permission_allowed
        ) or not brain_result.success:
            status = (
                "WAITING_APPROVAL"
                if brain_result.confirmation_required
                else "BLOCKED"
            )
            self._observe(
                request=request,
                brain=brain_result,
                status=status,
            )
            return ExecutionLoopResult(
                success=False,
                status=status,
                request=request,
                brain=brain_result,
                tool=None,
                recovery_state=self.recovery.state.value,
                observation_count=len(self.observability.snapshot()),
                response=brain_result.message,
                metadata={
                    "loop_version": self.VERSION,
                    "execution_skipped": True,
                },
            )

        # Only explicit file-operation intent enters the automatic tool
        # execution branch. Cognitive requests stay inside Master Brain.
        if brain_result.action != "read_file":
            self._observe(
                request=request,
                brain=brain_result,
                status="COMPLETED",
            )
            return ExecutionLoopResult(
                success=True,
                status="COMPLETED",
                request=request,
                brain=brain_result,
                tool=None,
                recovery_state=self.recovery.state.value,
                observation_count=len(self.observability.snapshot()),
                response=brain_result.message,
                metadata={
                    "loop_version": self.VERSION,
                    "execution_kind": "cognitive",
                    "plan_created": brain_result.plan_created,
                },
            )

        tool_result, attempts = self._execute_read_only_tool(
            request,
            user_confirmation=user_confirmation,
        )

        if tool_result is None:
            status = "BLOCKED"
            response = "No safe read-only tool matched the request."
            self._observe(
                request=request,
                brain=brain_result,
                status=status,
                error_class="ToolDiscoveryFailure",
            )
            return ExecutionLoopResult(
                success=False,
                status=status,
                request=request,
                brain=brain_result,
                tool=None,
                recovery_state=self.recovery.state.value,
                observation_count=len(self.observability.snapshot()),
                response=response,
                metadata={
                    "loop_version": self.VERSION,
                    "attempts": attempts,
                },
            )

        if tool_result.success:
            response = self._format_tool_response(tool_result)
            self.brain.context.add_turn(
                user=request,
                assistant=response,
                intent=brain_result.intent,
            )
            self._observe(
                request=request,
                brain=brain_result,
                status="COMPLETED",
                tool_id=tool_result.tool,
                result_status="SUCCESS",
                verification_status="VERIFIED",
            )
            return ExecutionLoopResult(
                success=True,
                status="COMPLETED",
                request=request,
                brain=brain_result,
                tool=tool_result,
                recovery_state=self.recovery.state.value,
                observation_count=len(self.observability.snapshot()),
                response=response,
                metadata={
                    "loop_version": self.VERSION,
                    "execution_kind": "read_only_tool",
                    "attempts": attempts,
                    "verified": True,
                },
            )

        self._observe(
            request=request,
            brain=brain_result,
            status="FAILED",
            tool_id=tool_result.tool,
            result_status="FAILED",
            verification_status="NOT_VERIFIED",
            error_class="ToolExecutionFailure",
        )
        return ExecutionLoopResult(
            success=False,
            status="FAILED",
            request=request,
            brain=brain_result,
            tool=tool_result,
            recovery_state=self.recovery.state.value,
            observation_count=len(self.observability.snapshot()),
            response=tool_result.error or tool_result.reason,
            metadata={
                "loop_version": self.VERSION,
                "execution_kind": "read_only_tool",
                "attempts": attempts,
                "verified": False,
            },
        )

    def _execute_read_only_tool(
        self,
        request: str,
        *,
        user_confirmation: bool,
    ) -> tuple[ToolResult | None, int]:
        query, kwargs = self._tool_request(request)

        candidate = self.discovery.select(query)
        if candidate is None:
            return None, 0

        attempts = 0
        last: ToolResult | None = None

        # Read-only operations are safe to retry through the existing
        # permission + sandbox path. No protected operation is retried.
        max_attempts = 2 if candidate.read_only else 1

        while attempts < max_attempts:
            attempts += 1
            invocation: ToolInvocationResult = self.invoker.invoke(
                query,
                user_confirmation=user_confirmation,
                **kwargs,
            )
            normalized = self.results.handle(invocation)
            last = normalized

            if normalized.success:
                if self.recovery.state.value == "recovering":
                    self.recovery.complete(
                        "Read-only execution recovered and verified."
                    )
                return normalized, attempts

            if attempts < max_attempts:
                self.recovery.begin(
                    f"Safe retry after read-only tool failure: "
                    f"{normalized.reason}"
                )
                continue

            if self.recovery.state.value == "recovering":
                self.recovery.fail(
                    f"Read-only recovery exhausted: {normalized.reason}"
                )

        return last, attempts

    @staticmethod
    def _tool_request(request: str) -> tuple[str, dict[str, Any]]:
        normalized = request.strip()

        patterns = (
            (
                r"^(?:please\s+)?(?:read|open|show)\s+(?:the\s+)?file\s+(.+)$",
                "read_file",
                "path",
            ),
            (
                r"^(?:please\s+)?(?:list|show)\s+(?:the\s+)?(?:directory|folder)\s*(.*)$",
                "list_directory",
                "path",
            ),
            (
                r"^(?:please\s+)?(?:inspect|check|show)\s+(?:the\s+)?file\s+info\s+(.+)$",
                "file_info",
                "path",
            ),
            (
                r"^(?:please\s+)?search\s+local\s+files\s+for\s+(.+)$",
                "search_local_files",
                "query",
            ),
        )

        for pattern, tool_name, argument_name in patterns:
            match = re.match(pattern, normalized, flags=re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if tool_name == "list_directory" and not value:
                    value = "."
                return (
                    tool_name,
                    {argument_name: value},
                )

        # Discovery still runs, but no unsafe arguments are invented.
        return normalized, {}

    @staticmethod
    def _format_tool_response(tool: ToolResult) -> str:
        return f"{tool.tool}: {tool.result!r}"

    def _observe(
        self,
        *,
        request: str,
        brain: BrainResult,
        status: str,
        tool_id: str | None = None,
        result_status: str | None = None,
        verification_status: str | None = None,
        error_class: str | None = None,
    ) -> None:
        self.observability.record(
            ObservationEvent(
                event_type="master_execution_loop",
                actor_id=self.brain.root_identity.BRAIN_ID,
                result_status=result_status or status,
                verification_status=verification_status
                or brain.verification_status,
                error_class=error_class,
                tool_id=tool_id,
                metadata={
                    "request": request,
                    "intent": brain.intent,
                    "action": brain.action,
                    "plan_created": brain.plan_created,
                    "goal_id": brain.goal_id,
                    "confirmation_required": (
                        brain.confirmation_required
                    ),
                },
            )
        )
