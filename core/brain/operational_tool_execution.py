from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from security.audit.execution_evidence import (
    ExecutionEvidenceRecorder,
)
from tools.intelligence import (
    ToolIntelligence,
    ToolIntelligenceResult,
)


@dataclass(frozen=True)
class OperationalToolExecutionResult:
    """
    Stable operational result for real tool execution.

    This object preserves the complete result produced by the
    existing ToolIntelligence pipeline.

    This layer does not:
    - discover tools itself
    - grant permissions
    - execute tools directly
    - bypass SafeToolExecutor
    - modify the constitution
    - perform protected actions
    """

    success: bool
    discovery_query: str
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
    execution_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not self.discovery_query.strip():
            raise ValueError(
                "discovery_query cannot be empty."
            )

        if self.success and self.error is not None:
            raise ValueError(
                "Successful execution cannot contain an error."
            )

        if not self.success and self.result is not None:
            raise ValueError(
                "Failed execution cannot contain a result."
            )

        if self.attempts <= 0:
            raise ValueError(
                "attempts must be greater than zero."
            )

        if not self.execution_id.strip():
            raise ValueError(
                "execution_id cannot be empty."
            )


class OperationalToolExecution:
    """
    Real operational tool-execution boundary.

    Execution is delegated completely to the existing
    ToolIntelligence pipeline.

    The underlying pipeline remains authoritative for:
    - discovery
    - permission
    - safe execution
    - result normalization
    - failure recovery
    - retry decisions

    This layer additionally records execution evidence when
    an ExecutionEvidenceRecorder is explicitly supplied.
    """

    def __init__(
        self,
        tool_intelligence: ToolIntelligence,
        evidence_recorder: ExecutionEvidenceRecorder | None = None,
    ) -> None:
        if not isinstance(
            tool_intelligence,
            ToolIntelligence,
        ):
            raise TypeError(
                "tool_intelligence must be ToolIntelligence"
            )

        if evidence_recorder is not None and not isinstance(
            evidence_recorder,
            ExecutionEvidenceRecorder,
        ):
            raise TypeError(
                "evidence_recorder must be "
                "ExecutionEvidenceRecorder or None"
            )

        self.tool_intelligence = tool_intelligence
        self.evidence_recorder = evidence_recorder

    def execute(
        self,
        discovery_query: str,
        *,
        max_attempts: int = 3,
        **kwargs: Any,
    ) -> OperationalToolExecutionResult:
        """
        Execute a real registered tool through the existing
        controlled ToolIntelligence pipeline.

        Execution evidence is recorded only after the
        ToolIntelligence pipeline returns its result.
        """

        if not isinstance(discovery_query, str):
            raise TypeError(
                "discovery_query must be a string."
            )

        discovery_query = discovery_query.strip()

        if not discovery_query:
            raise ValueError(
                "discovery_query cannot be empty."
            )

        if max_attempts < 1:
            raise ValueError(
                "max_attempts must be at least 1."
            )

        result: ToolIntelligenceResult = (
            self.tool_intelligence.execute(
                discovery_query,
                max_attempts=max_attempts,
                **kwargs,
            )
        )

        execution_id = str(uuid4())

        confirmation_provided = bool(
            kwargs.get("user_confirmation", False)
        )

        if result.success:
            verification_status = "VERIFIED"
            final_status = "SUCCESS"
        elif result.recovery_status == "BLOCKED":
            verification_status = "NOT_VERIFIED"
            final_status = "BLOCKED"
        else:
            verification_status = "NOT_VERIFIED"
            final_status = "FAILED"

        if self.evidence_recorder is not None:
            self.evidence_recorder.record_authenticated(
                execution_id=execution_id,
                tool=result.tool or "unknown",
                action="tool_execution",
                permission_allowed=result.allowed,
                confirmation_required=result.requires_confirmation,
                confirmation_provided=confirmation_provided,
                attempts=result.attempts,
                result=result.result,
                verification_status=verification_status,
                recovery_status=result.recovery_status,
                final_status=final_status,
                error=result.error,
                risk=result.risk,
                reason=result.reason,
            )

        return OperationalToolExecutionResult(
            success=result.success,
            discovery_query=discovery_query,
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
            execution_id=execution_id,
        )
