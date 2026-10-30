from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import Path
import hashlib
import json
from typing import Any
from uuid import uuid4

from core.policies.approval import PermissionEngine
from core.brain.emergency_stop import EmergencyStop
from security.audit.execution_evidence import ExecutionEvidenceRecorder
from security.audit.execution_trace import ExecutionTraceVerifier
from tools.discovery import ToolCandidate
from tools.intelligence import ToolIntelligence, ToolIntelligenceResult
from tools.registry import ToolRegistry, build_runtime_registry


@dataclass(frozen=True)
class ToolBrainResult:
    """Stable result exposed by the SAHIBEX Tool Brain boundary."""

    operation: str
    success: bool
    tool: str
    allowed: bool
    requires_confirmation: bool
    attempts: int
    recovery_status: str
    retryable: bool
    result: Any
    error: str | None
    risk: str
    reason: str
    audit_recorded: bool = False


class ToolBrain:
    """
    SAHIBEX Tool Brain boundary.

    The Tool Brain coordinates the existing, security-critical tool stack:
        discovery -> permission -> safe execution
        -> result verification -> failure recovery

    It does not grant authority, modify the Constitution, or bypass
    Human Authority. Protected tools remain permission/confirmation gated.
    """

    VERSION = "1.0"

    def __init__(
        self,
        permission_engine: PermissionEngine,
        *,
        project_root: Path | None = None,
        registry: ToolRegistry | None = None,
        emergency_stop: EmergencyStop | None = None,
        evidence_recorder: ExecutionEvidenceRecorder | None = None,
    ) -> None:
        if not isinstance(permission_engine, PermissionEngine):
            raise TypeError("permission_engine must be PermissionEngine")

        root = (
            Path(project_root).resolve()
            if project_root is not None
            else Path.cwd().resolve()
        )
        self.emergency_stop = emergency_stop or EmergencyStop()
        self.evidence_recorder = evidence_recorder or ExecutionEvidenceRecorder(
            root / "security" / "audit"
        )
        self.registry = registry or build_runtime_registry(
            root,
            evidence_recorder=self.evidence_recorder,
        )

        # Import lazily to keep this facade a composition boundary only.
        from tools.discovery import ToolDiscovery
        from tools.executor import SafeToolExecutor
        from tools.failure_recovery import ToolFailureRecovery
        from tools.invocation import ToolInvoker
        from tools.permission_gateway import ToolPermissionGateway
        from tools.result_handler import ToolResultHandler

        discovery = ToolDiscovery(self.registry)
        permissions = ToolPermissionGateway(
            permission_engine,
            self.registry,
        )
        executor = SafeToolExecutor(self.registry)
        invoker = ToolInvoker(discovery, permissions, executor)

        self.discovery = discovery
        self.permissions = permissions
        self.executor = executor
        self.invoker = invoker
        self.intelligence = ToolIntelligence(
            tool_invoker=invoker,
            result_handler=ToolResultHandler(),
            recovery=ToolFailureRecovery(),
        )

    def _record_protected_evidence(
        self,
        *,
        tool: str,
        request: str,
        permission_allowed: bool,
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
        """Persist and authenticate protected-action evidence.

        Protected execution uses a two-phase trail: a durable intent record
        must pass provenance verification before the handler is allowed to
        run, then a separate result record closes the trace.
        """
        try:
            result_summary = None
            if result is not None:
                encoded = json.dumps(
                    result,
                    sort_keys=True,
                    default=str,
                ).encode("utf-8")
                result_summary = {
                    "type": type(result).__name__,
                    "sha256": hashlib.sha256(encoded).hexdigest(),
                    "size_bytes": len(encoded),
                }
            evidence = self.evidence_recorder.record_authenticated(
                execution_id=str(uuid4()),
                tool=tool or "unknown",
                action="tool_brain_protected_execution",
                permission_allowed=bool(permission_allowed),
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
            trace = ExecutionTraceVerifier().verify_provenance(
                asdict(evidence),
                self.evidence_recorder.log_directory,
            )
            return trace.verified
        except Exception:
            return False

    def discover(
        self,
        query: str,
        *,
        max_results: int = 10,
    ) -> list[ToolCandidate]:
        return self.discovery.discover(query, max_results=max_results)

    def execute(
        self,
        discovery_query: str,
        *,
        user_confirmation: bool = False,
        max_attempts: int = 3,
        **kwargs: Any,
    ) -> ToolBrainResult:
        if self.emergency_stop.requires_execution_block():
            return ToolBrainResult(
                operation="execute",
                success=False,
                tool="",
                allowed=False,
                requires_confirmation=False,
                attempts=0,
                recovery_status="BLOCKED",
                retryable=False,
                result=None,
                error="Emergency stop is engaged; protected execution is blocked.",
                risk="high",
                reason="Emergency stop is engaged.",
            )

        candidate = self.discovery.select(discovery_query)
        protected = candidate is not None and not candidate.read_only
        confirmation_required = False
        permission = None

        if protected:
            definition = self.registry.get(candidate.name)
            confirmation_required = bool(definition.requires_confirmation)
            try:
                permission = self.permissions.check(
                    candidate.name,
                    confirmation=user_confirmation,
                )
            except Exception as exc:
                return ToolBrainResult(
                    operation="execute",
                    success=False,
                    tool=candidate.name,
                    allowed=False,
                    requires_confirmation=confirmation_required,
                    attempts=0,
                    recovery_status="BLOCKED",
                    retryable=False,
                    result=None,
                    error=f"Protected action permission check failed: {type(exc).__name__}",
                    risk="high",
                    reason="Protected action blocked before execution.",
                )

            confirmation_required = bool(
                confirmation_required or permission.requires_confirmation
            )
            confirmation_provided = bool(
                user_confirmation and confirmation_required
            )

            if not permission.allowed:
                self._record_protected_evidence(
                    tool=candidate.name,
                    request=discovery_query,
                    permission_allowed=False,
                    confirmation_required=confirmation_required,
                    confirmation_provided=False,
                    attempts=1,
                    result=None,
                    verification_status="NOT_EXECUTED",
                    recovery_status="BLOCKED",
                    final_status="BLOCKED",
                    error=permission.reason,
                    risk=permission.risk,
                    reason="Protected action denied before handler execution.",
                )
                return ToolBrainResult(
                    operation="execute",
                    success=False,
                    tool=candidate.name,
                    allowed=False,
                    requires_confirmation=True,
                    attempts=1,
                    recovery_status="BLOCKED",
                    retryable=False,
                    result=None,
                    error=permission.reason,
                    risk=permission.risk,
                    reason=permission.reason,
                )

            # Fail closed before any protected side effect if the intent
            # cannot be durably recorded and authenticated.
            intent_recorded = self._record_protected_evidence(
                tool=candidate.name,
                request=discovery_query,
                permission_allowed=True,
                confirmation_required=confirmation_required,
                confirmation_provided=confirmation_provided,
                attempts=1,
                result=None,
                verification_status="NOT_VERIFIED",
                recovery_status="PENDING",
                final_status="PENDING",
                error=None,
                risk=permission.risk,
                reason="Protected execution intent recorded before handler execution.",
            )
            if not intent_recorded:
                return ToolBrainResult(
                    operation="execute",
                    success=False,
                    tool=candidate.name,
                    allowed=True,
                    requires_confirmation=confirmation_required,
                    attempts=0,
                    recovery_status="BLOCKED",
                    retryable=False,
                    result=None,
                    error="Protected execution blocked: authenticated intent audit could not be persisted.",
                    risk=permission.risk,
                    reason="Fail-closed audit precondition failed; no protected handler was run.",
                )

        result: ToolIntelligenceResult = self.intelligence.execute(
            discovery_query,
            user_confirmation=user_confirmation,
            max_attempts=max_attempts,
            **kwargs,
        )
        tool_result = ToolBrainResult(
            operation="execute",
            success=result.success,
            tool=result.tool,
            allowed=result.allowed,
            requires_confirmation=(
                confirmation_required if protected else result.requires_confirmation
            ),
            attempts=result.attempts,
            recovery_status=result.recovery_status,
            retryable=result.retryable,
            result=result.result,
            error=result.error,
            risk=result.risk,
            reason=result.reason,
        )

        if protected:
            final_status = (
                "SUCCESS" if result.success
                else "BLOCKED" if not result.allowed
                else "FAILED"
            )
            verification_status = (
                "VERIFIED" if result.success
                else "NOT_EXECUTED" if not result.allowed
                else "NOT_VERIFIED"
            )
            final_recorded = self._record_protected_evidence(
                tool=candidate.name,
                request=discovery_query,
                permission_allowed=bool(result.allowed),
                confirmation_required=confirmation_required,
                confirmation_provided=bool(
                    user_confirmation and confirmation_required
                ),
                attempts=max(1, result.attempts),
                result=result.result if result.success else None,
                verification_status=verification_status,
                recovery_status=(
                    "SUCCESS" if result.success else result.recovery_status
                ),
                final_status=final_status,
                error=result.error,
                risk=result.risk,
                reason=result.reason,
            )
            if not final_recorded:
                return ToolBrainResult(
                    operation="execute",
                    success=False,
                    tool=candidate.name,
                    allowed=bool(result.allowed),
                    requires_confirmation=confirmation_required,
                    attempts=result.attempts,
                    recovery_status="AUDIT_FINALIZATION_FAILED",
                    retryable=False,
                    result=None,
                    error=(
                        "Protected action may have executed, but final authenticated "
                        "audit verification failed. Inspect the pending intent record "
                        "before retrying."
                    ),
                    risk=result.risk,
                    reason="Final audit verification failed after protected execution.",
                )
            tool_result = replace(tool_result, audit_recorded=True)

        return tool_result

    def capability_contract(self) -> dict[str, bool]:
        return {
            "tool_discovery": True,
            "tool_selection": True,
            "permission_check": True,
            "safe_execution": True,
            "result_verification": True,
            "failure_recovery": True,
            "protected_action_support": True,
            "permission_authority": False,
            "constitution_mutation": False,
            "human_authority_override": False,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "version": self.VERSION,
            "registered_tools": [
                tool.name for tool in self.registry.list_tools()
            ],
            "capabilities": self.capability_contract(),
        }
