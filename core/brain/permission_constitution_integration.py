from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class MasterPermissionConstitutionResult:
    """
    Result of integrating an existing permission/constitution
    decision into the master brain.

    This object records the decision only. It does not grant
    permission, override the constitution, or execute actions.
    """

    success: bool
    action: str
    allowed: bool
    requires_confirmation: bool
    reason: str
    integration_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")

        if not isinstance(self.action, str):
            raise TypeError("action must be a string.")

        if not self.action.strip():
            raise ValueError(
                "action must be a non-empty string."
            )

        if not isinstance(self.allowed, bool):
            raise TypeError("allowed must be a boolean.")

        if not isinstance(
            self.requires_confirmation,
            bool,
        ):
            raise TypeError(
                "requires_confirmation must be a boolean."
            )

        if not isinstance(self.reason, str):
            raise TypeError("reason must be a string.")

        if not self.reason.strip():
            raise ValueError(
                "reason must be a non-empty string."
            )

        if (
            not isinstance(self.integration_id, str)
            or not self.integration_id.strip()
        ):
            raise ValueError(
                "integration_id must be a non-empty string."
            )


class MasterPermissionConstitutionIntegration:
    """
    Contract-level integration of an existing permission and
    constitution decision with the master brain.

    The root constitution and permission system remain the
    authoritative decision makers.

    This layer does not:
    - grant permissions
    - override the constitution
    - execute actions
    """

    def evaluate(
        self,
        *,
        action: str,
        allowed: bool,
        requires_confirmation: bool,
        reason: str,
    ) -> MasterPermissionConstitutionResult:
        if not isinstance(action, str):
            raise TypeError("action must be a string.")

        normalized_action = action.strip().lower()

        if not normalized_action:
            raise ValueError(
                "action must be a non-empty string."
            )

        if not isinstance(allowed, bool):
            raise TypeError(
                "allowed must be a boolean."
            )

        if not isinstance(
            requires_confirmation,
            bool,
        ):
            raise TypeError(
                "requires_confirmation must be a boolean."
            )

        if not isinstance(reason, str):
            raise TypeError(
                "reason must be a string."
            )

        normalized_reason = reason.strip()

        if not normalized_reason:
            raise ValueError(
                "reason must be a non-empty string."
            )

        return MasterPermissionConstitutionResult(
            success=True,
            action=normalized_action,
            allowed=allowed,
            requires_confirmation=requires_confirmation,
            reason=normalized_reason,
        )
