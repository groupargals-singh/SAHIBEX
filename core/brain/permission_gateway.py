from __future__ import annotations

from core.policies.approval import (
    ActionType,
    PermissionDecision,
    PermissionEngine,
)


class PermissionGateway:
    """
    Canonical runtime permission gateway for SAHIBEX actions.

    This gateway delegates permission decisions to the existing
    PermissionEngine. It never executes actions and never grants
    authority by itself.
    """

    def __init__(
        self,
        permission_engine: PermissionEngine | None = None,
    ) -> None:
        self.permission_engine = (
            permission_engine
            if permission_engine is not None
            else PermissionEngine()
        )

    def check(
        self,
        action: ActionType,
        *,
        confirmation: bool = False,
    ) -> PermissionDecision:
        if not isinstance(action, ActionType):
            raise TypeError("action must be an ActionType.")

        if not isinstance(confirmation, bool):
            raise TypeError("confirmation must be a boolean.")

        return self.permission_engine.check(
            action,
            confirmation=confirmation,
        )

    def require(
        self,
        action: ActionType,
        *,
        confirmation: bool = False,
    ) -> PermissionDecision:
        result = self.check(
            action,
            confirmation=confirmation,
        )

        if not result.allowed:
            raise PermissionError(
                f"Permission blocked for "
                f"{action.value}: {result.reason}"
            )

        return result
