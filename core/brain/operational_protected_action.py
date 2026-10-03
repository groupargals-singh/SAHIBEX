from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from core.policies.approval import (
    ActionType,
    PermissionEngine,
)
from core.policies.constitution import (
    ActionClass,
)
from tools.human_approval import (
    HumanApprovalGateway,
)


class ProtectedActionStatus(str, Enum):
    BLOCKED = "blocked"
    APPROVED = "approved"


@dataclass(frozen=True)
class ProtectedActionResult:
    """
    Stable result of the protected-action approval gate.

    This object records whether a protected action has received
    the required user authorization and permission approval.

    Approval does NOT execute the action.
    """

    status: ProtectedActionStatus
    action_class: ActionClass
    action_type: ActionType
    allowed: bool
    requires_confirmation: bool
    risk: str
    reason: str
    user_confirmation: bool
    execution_allowed: bool
    request_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.action_class,
            ActionClass,
        ):
            raise TypeError(
                "action_class must be ActionClass."
            )

        if not isinstance(
            self.action_type,
            ActionType,
        ):
            raise TypeError(
                "action_type must be ActionType."
            )

        if not self.request_id.strip():
            raise ValueError(
                "request_id cannot be empty."
            )

        if self.allowed and not self.execution_allowed:
            raise ValueError(
                "Allowed protected action must permit execution."
            )

        if (
            self.status == ProtectedActionStatus.APPROVED
            and not self.allowed
        ):
            raise ValueError(
                "Approved status requires allowed=True."
            )

        if (
            self.status == ProtectedActionStatus.BLOCKED
            and self.execution_allowed
        ):
            raise ValueError(
                "Blocked action cannot permit execution."
            )


class OperationalProtectedActionGateway:
    """
    Approval gate for protected SAHIBEX actions.

    This layer:
    - validates protected action identity
    - asks the root Constitution for authority
    - re-checks the existing PermissionEngine
    - requires explicit user confirmation
    - returns a stable approval result

    This layer does NOT:
    - execute commands
    - write files
    - delete files
    - access credentials
    - perform network operations
    - perform financial actions
    - modify system configuration
    - modify the Constitution
    - grant itself permission
    """

    ACTION_MAP: dict[ActionClass, ActionType] = {
        ActionClass.WRITE: ActionType.WRITE_FILE,
        ActionClass.DELETE: ActionType.DELETE_FILE,
        ActionClass.EXECUTE: ActionType.RUN_COMMAND,
        ActionClass.NETWORK: ActionType.NETWORK_ACCESS,
        ActionClass.CREDENTIAL: ActionType.CREDENTIAL_USE,
        ActionClass.SYSTEM_CHANGE: ActionType.SYSTEM_CHANGE,
        ActionClass.FINANCIAL: ActionType.FINANCIAL_ACTION,
    }

    def __init__(
        self,
        human_approval: HumanApprovalGateway | None = None,
        permission_engine: PermissionEngine | None = None,
    ) -> None:
        self.human_approval = (
            human_approval or HumanApprovalGateway()
        )
        self.permission_engine = (
            permission_engine or PermissionEngine()
        )

    def approve(
        self,
        action_class: ActionClass,
        *,
        user_confirmation: bool = False,
    ) -> ProtectedActionResult:
        if not isinstance(
            action_class,
            ActionClass,
        ):
            raise TypeError(
                "action_class must be an ActionClass."
            )

        if action_class not in self.ACTION_MAP:
            return ProtectedActionResult(
                status=ProtectedActionStatus.BLOCKED,
                action_class=action_class,
                action_type=ActionType.RESPOND,
                allowed=False,
                requires_confirmation=False,
                risk="unknown",
                reason=(
                    "Action is not a protected execution "
                    "action handled by this gateway."
                ),
                user_confirmation=user_confirmation,
                execution_allowed=False,
            )

        action_type = self.ACTION_MAP[action_class]

        authority = self.human_approval.check(
            action_class,
            user_confirmation=user_confirmation,
        )

        if not authority.allowed:
            return ProtectedActionResult(
                status=ProtectedActionStatus.BLOCKED,
                action_class=action_class,
                action_type=action_type,
                allowed=False,
                requires_confirmation=(
                    authority.requires_confirmation
                ),
                risk=(
                    PermissionEngine.RISK_MAP[
                        action_type
                    ].value
                ),
                reason=authority.reason,
                user_confirmation=user_confirmation,
                execution_allowed=False,
            )

        permission = self.permission_engine.check(
            action_type,
            confirmation=user_confirmation,
        )

        if not permission.allowed:
            return ProtectedActionResult(
                status=ProtectedActionStatus.BLOCKED,
                action_class=action_class,
                action_type=action_type,
                allowed=False,
                requires_confirmation=(
                    permission.requires_confirmation
                ),
                risk=permission.risk.value,
                reason=permission.reason,
                user_confirmation=user_confirmation,
                execution_allowed=False,
            )

        return ProtectedActionResult(
            status=ProtectedActionStatus.APPROVED,
            action_class=action_class,
            action_type=action_type,
            allowed=True,
            requires_confirmation=False,
            risk=permission.risk.value,
            reason=(
                "Protected action approved after "
                "explicit user authorization and "
                "permission re-check."
            ),
            user_confirmation=True,
            execution_allowed=True,
        )
