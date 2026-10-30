from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import json
import re
from typing import Any
from uuid import uuid4

from core.brain.master_brain import BrainResult, MasterBrain
from core.brain.operational_verification import OperationalVerificationRecovery
from security.audit.execution_evidence import ExecutionEvidenceRecorder
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
        evidence_recorder: ExecutionEvidenceRecorder | None = None,
        verifier: OperationalVerificationRecovery | None = None,
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
        self.evidence_recorder = evidence_recorder or ExecutionEvidenceRecorder(
            self.project_root / "security" / "audit"
        )
        self.verifier = verifier or OperationalVerificationRecovery()
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
            audit_recorded = self._record_evidence(
                request=request,
                tool=brain_result.action or "main_brain_action",
                allowed=brain_result.permission_allowed,
                confirmation_required=brain_result.confirmation_required,
                confirmation_provided=(
                    user_confirmation and brain_result.confirmation_required
                ),
                attempts=1,
                result=None,
                verification_status="NOT_EXECUTED",
                recovery_status="BLOCKED",
                final_status="BLOCKED",
                error="Action blocked before tool execution.",
                risk="high" if brain_result.confirmation_required else "medium",
                reason=brain_result.message or "Main Brain blocked the action.",
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
                    "audit_recorded": audit_recorded,
                },
            )

        # Protected actions are executed by MainBrain's Tool Brain only
        # after its authority/permission gates. Do not mislabel them as
        # cognitive answers: require the Tool Brain's authenticated audit.
        if brain_result.action in {"write_file", "delete_file", "run_command"}:
            tool_meta = brain_result.metadata.get("tool_brain_integration", {})
            if not isinstance(tool_meta, dict):
                tool_meta = {}
            verified = brain_result.verification_status == "VERIFIED"
            audit_recorded = tool_meta.get("audit_recorded") is True
            if tool_meta.get("success") is True and verified and audit_recorded:
                tool_name = str(tool_meta.get("tool") or brain_result.action)
                self._observe(
                    request=request,
                    brain=brain_result,
                    status="COMPLETED",
                    tool_id=tool_name,
                    result_status="SUCCESS",
                    verification_status="VERIFIED",
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
                        "execution_kind": "protected_tool",
                        "tool_name": tool_name,
                        "verified": True,
                        "audit_recorded": True,
                    },
                )

            self._observe(
                request=request,
                brain=brain_result,
                status="FAILED",
                tool_id=str(tool_meta.get("tool") or brain_result.action),
                result_status="FAILED",
                verification_status=brain_result.verification_status,
                error_class="ProtectedToolAuditOrVerificationFailure",
            )
            return ExecutionLoopResult(
                success=False,
                status="FAILED",
                request=request,
                brain=brain_result,
                tool=None,
                recovery_state=self.recovery.state.value,
                observation_count=len(self.observability.snapshot()),
                response=(
                    "Protected action did not provide verified authenticated audit evidence. "
                    "Inspect the target state before retrying."
                ),
                metadata={
                    "loop_version": self.VERSION,
                    "execution_kind": "protected_tool",
                    "verified": False,
                    "audit_recorded": audit_recorded,
                },
            )

        # Only explicit read-only file-operation intent enters this loop's
        # independent tool path. Cognitive requests stay inside MainBrain.
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
            audit_recorded = self._record_evidence(
                request=request,
                tool="tool_discovery",
                allowed=False,
                confirmation_required=False,
                confirmation_provided=False,
                attempts=max(1, attempts),
                result=None,
                verification_status="NOT_EXECUTED",
                recovery_status="BLOCKED",
                final_status="BLOCKED",
                error="No safe read-only tool matched the request.",
                risk="low",
                reason="Tool discovery found no permitted candidate.",
            )
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
                    "audit_recorded": audit_recorded,
                },
            )

        verification = self.verifier.verify_tool_result(tool_result)
        accepted = verification.success and verification.verified
        audit_recorded = self._record_evidence(
            request=request,
            tool=tool_result.tool,
            allowed=tool_result.allowed,
            confirmation_required=tool_result.requires_confirmation,
            confirmation_provided=(
                user_confirmation and tool_result.requires_confirmation
            ),
            attempts=max(1, attempts),
            result=tool_result.result if accepted else None,
            verification_status=verification.verification_status,
            recovery_status=verification.recovery_status,
            final_status="SUCCESS" if accepted else "FAILED",
            error=tool_result.error if not accepted else None,
            risk=tool_result.risk,
            reason=verification.reason,
        )

        if accepted and audit_recorded:
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
                verification_status=verification.verification_status,
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
                    "verification_status": verification.verification_status,
                    "audit_recorded": True,
                },
            )

        failure_reason = (
            verification.reason
            if not accepted
            else "Execution evidence could not be persisted; failing closed."
        )
        self._observe(
            request=request,
            brain=brain_result,
            status="FAILED",
            tool_id=tool_result.tool,
            result_status="FAILED",
            verification_status=verification.verification_status,
            error_class=(
                "ToolVerificationFailure" if not accepted else "AuditWriteFailure"
            ),
        )
        return ExecutionLoopResult(
            success=False,
            status="FAILED",
            request=request,
            brain=brain_result,
            tool=tool_result,
            recovery_state=self.recovery.state.value,
            observation_count=len(self.observability.snapshot()),
            response=failure_reason,
            metadata={
                "loop_version": self.VERSION,
                "execution_kind": "read_only_tool",
                "attempts": attempts,
                "verified": False,
                "verification_status": verification.verification_status,
                "audit_recorded": audit_recorded,
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

    def _record_evidence(
        self,
        *,
        request: str,
        tool: str,
        allowed: bool,
        confirmation_required: bool,
        confirmation_provided: bool,
        attempts: int,
        result: Any,
        verification_status: str,
        recovery_status: str,
        final_status: str,
        error: str | None,
        risk: str,
        reason: str,
    ) -> bool:
        """Persist authenticated evidence without storing tool output bodies."""
        try:
            serialized_result = json.dumps(
                result,
                sort_keys=True,
                default=str,
            ) if result is not None else "null"
            result_summary = None
            if result is not None:
                encoded = serialized_result.encode("utf-8")
                result_summary = {
                    "type": type(result).__name__,
                    "sha256": hashlib.sha256(encoded).hexdigest(),
                    "size_bytes": len(encoded),
                }
            self.evidence_recorder.record_authenticated(
                execution_id=str(uuid4()),
                tool=tool or "unknown",
                action="main_brain_tool_execution",
                permission_allowed=bool(allowed),
                confirmation_required=bool(confirmation_required),
                confirmation_provided=bool(confirmation_provided),
                attempts=max(1, int(attempts)),
                result=result_summary,
                verification_status=verification_status or "NOT_VERIFIED",
                recovery_status=recovery_status or "FAILED",
                final_status=final_status or "FAILED",
                error=error,
                risk=risk or "unknown",
                reason=(
                    f"request_sha256={hashlib.sha256(request.encode('utf-8')).hexdigest()}; "
                    f"{reason or 'No additional detail.'}"
                ),
            )
            return True
        except Exception:
            # The caller must not report a successful tool action when
            # durable audit evidence could not be written.
            return False

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
