from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MultimodalSafetyResult:
    """
    Result of a multimodal safety evaluation.

    This object represents a safety decision only.
    It does not grant permissions or execute actions.
    """

    allowed: bool
    requires_confirmation: bool
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.allowed, bool):
            raise TypeError("allowed must be a boolean.")

        if not isinstance(self.requires_confirmation, bool):
            raise TypeError(
                "requires_confirmation must be a boolean."
            )

        if not isinstance(self.reason, str):
            raise TypeError("reason must be a string.")

        if not self.reason.strip():
            raise ValueError("reason must be a non-empty string.")


class MultimodalSafetyPolicy:
    """
    Contract-level safety evaluation for multimodal actions.

    This layer does not grant permissions, execute actions,
    access credentials, or override the main constitution.
    """

    _AUTONOMOUS_ACTIONS = {
        "think",
        "research",
        "read",
    }

    _PROTECTED_ACTIONS = {
        "write",
        "delete",
        "execute",
        "network",
        "credential",
        "system_change",
        "financial",
        "self_update",
        "external_control",
    }

    def evaluate(
        self,
        *,
        modality: str,
        action: str,
    ) -> MultimodalSafetyResult:
        if not isinstance(modality, str):
            raise TypeError("modality must be a string.")

        if not modality.strip():
            raise ValueError(
                "modality must be a non-empty string."
            )

        if not isinstance(action, str):
            raise TypeError("action must be a string.")

        if not action.strip():
            raise ValueError(
                "action must be a non-empty string."
            )

        normalized_action = action.strip().lower()

        if normalized_action in self._AUTONOMOUS_ACTIONS:
            return MultimodalSafetyResult(
                allowed=True,
                requires_confirmation=False,
                reason=(
                    "Action is within the autonomous multimodal "
                    "safety boundary."
                ),
            )

        if normalized_action in self._PROTECTED_ACTIONS:
            return MultimodalSafetyResult(
                allowed=False,
                requires_confirmation=True,
                reason=(
                    "Protected action requires explicit user "
                    "confirmation through the authorized "
                    "permission system."
                ),
            )

        return MultimodalSafetyResult(
            allowed=False,
            requires_confirmation=False,
            reason="Unknown action is denied by default.",
        )
