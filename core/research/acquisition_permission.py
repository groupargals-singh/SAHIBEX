from __future__ import annotations

from dataclasses import dataclass

from core.policies.approval import (
    ActionType,
    PermissionEngine,
)


@dataclass(frozen=True)
class AcquisitionPermissionResult:
    allowed: bool
    action: str
    reason: str
    requires_confirmation: bool
    risk: str


class AcquisitionPermissionGate:
    """
    Safety boundary between research acquisition
    and network access.

    This class does NOT perform network access.

    It only asks the existing SAHIBEX PermissionEngine
    whether NETWORK_ACCESS is currently permitted.
    """

    def __init__(
        self,
        permission_engine: PermissionEngine,
    ):
        if not isinstance(
            permission_engine,
            PermissionEngine,
        ):
            raise TypeError(
                "permission_engine must be PermissionEngine"
            )

        self.permission_engine = permission_engine

    def check_network_access(
        self,
        *,
        confirmation: bool = False,
    ) -> AcquisitionPermissionResult:
        action = ActionType.NETWORK_ACCESS

        decision = self.permission_engine.check(
            action,
            confirmation=confirmation,
        )

        return AcquisitionPermissionResult(
            allowed=decision.allowed,
            action=action.value,
            reason=decision.reason,
            requires_confirmation=(
                decision.requires_confirmation
            ),
            risk=decision.risk.value,
        )

    def require_network_access(
        self,
        *,
        confirmation: bool = False,
    ) -> AcquisitionPermissionResult:
        result = self.check_network_access(
            confirmation=confirmation,
        )

        if not result.allowed:
            raise PermissionError(
                "network acquisition blocked: "
                f"{result.reason}"
            )

        return result
