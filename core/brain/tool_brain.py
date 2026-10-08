from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.policies.approval import PermissionEngine
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
    ) -> None:
        if not isinstance(permission_engine, PermissionEngine):
            raise TypeError("permission_engine must be PermissionEngine")

        root = (
            Path(project_root).resolve()
            if project_root is not None
            else Path.cwd().resolve()
        )
        self.registry = registry or build_runtime_registry(root)

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
        result: ToolIntelligenceResult = self.intelligence.execute(
            discovery_query,
            user_confirmation=user_confirmation,
            max_attempts=max_attempts,
            **kwargs,
        )
        return ToolBrainResult(
            operation="execute",
            success=result.success,
            tool=result.tool,
            allowed=result.allowed,
            requires_confirmation=result.requires_confirmation,
            attempts=result.attempts,
            recovery_status=result.recovery_status,
            retryable=result.retryable,
            result=result.result,
            error=result.error,
            risk=result.risk,
            reason=result.reason,
        )

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
