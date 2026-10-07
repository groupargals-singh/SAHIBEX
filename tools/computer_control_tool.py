from __future__ import annotations

from typing import Any
from uuid import uuid4

from security.audit.execution_evidence import ExecutionEvidenceRecorder
from tools.android_computer_control import AndroidComputerControlProvider
from tools.computer_control import ComputerAction, ComputerControlRequest


class ComputerControlTool:
    """Registered protected computer-control tool.

    The caller cannot authorize itself. SafeToolExecutor injects the
    private _permission_granted flag only after the PermissionGateway
    allows the protected action.
    """

    def __init__(
        self,
        provider: AndroidComputerControlProvider | None = None,
        evidence_recorder: ExecutionEvidenceRecorder | None = None,
    ) -> None:
        self.provider = provider or AndroidComputerControlProvider()
        self.evidence_recorder = evidence_recorder

    def execute(
        self,
        *,
        action: ComputerAction | str,
        parameters: dict[str, Any],
        _permission_granted: bool = False,
        _confirmation_provided: bool = False,
    ) -> dict[str, Any]:
        if isinstance(action, str):
            try:
                action = ComputerAction(action)
            except ValueError as exc:
                raise ValueError(f"Unsupported computer action: {action}") from exc

        if not isinstance(action, ComputerAction):
            raise TypeError("action must be ComputerAction or a valid action string")

        request = ComputerControlRequest(
            action=action,
            parameters=parameters,
        )
        result = self.provider.execute(
            request,
            authorized=_permission_granted,
        )

        execution_id = str(uuid4())
        verification_status = "VERIFIED" if result.success else "NOT_VERIFIED"
        final_status = "SUCCESS" if result.success else "FAILED"

        if self.evidence_recorder is not None:
            self.evidence_recorder.record_authenticated(
                execution_id=execution_id,
                tool="computer_control",
                action=result.action.value,
                permission_allowed=_permission_granted,
                confirmation_required=True,
                confirmation_provided=_confirmation_provided,
                attempts=1,
                result=result.result,
                verification_status=verification_status,
                recovery_status="NOT_REQUIRED",
                final_status=final_status,
                error=result.error,
                risk="high",
                reason=(
                    "Android computer control execution completed."
                    if result.success
                    else (result.error or "Android computer control failed.")
                ),
            )

        return {
            "action": result.action.value,
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "execution_id": execution_id,
            "verification_status": verification_status,
            "final_status": final_status,
        }
