from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class MasterBrainIntegrationResult:
    """
    Result produced by the master-brain integration contract.

    This object represents normalized input for the master brain.
    It does not execute tasks, grant permissions, or access external
    systems.
    """

    success: bool
    intent: str
    summary: str
    result_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")

        if not isinstance(self.intent, str):
            raise TypeError("intent must be a string.")

        if not self.intent.strip():
            raise ValueError(
                "intent must be a non-empty string."
            )

        if not isinstance(self.summary, str):
            raise TypeError("summary must be a string.")

        if not self.summary.strip():
            raise ValueError(
                "summary must be a non-empty string."
            )

        if (
            not isinstance(self.result_id, str)
            or not self.result_id.strip()
        ):
            raise ValueError(
                "result_id must be a non-empty string."
            )


class MasterBrainIntegration:
    """
    Contract-level integration entry point for SAHIBEX's master brain.

    This layer currently normalizes and validates an intent plus summary.
    It does not execute tools, access devices, grant permissions,
    or modify the constitution.
    """

    def process(
        self,
        *,
        intent: str,
        summary: str,
    ) -> MasterBrainIntegrationResult:
        if not isinstance(intent, str):
            raise TypeError("intent must be a string.")

        if not intent.strip():
            raise ValueError(
                "intent must be a non-empty string."
            )

        if not isinstance(summary, str):
            raise TypeError("summary must be a string.")

        if not summary.strip():
            raise ValueError(
                "summary must be a non-empty string."
            )

        return MasterBrainIntegrationResult(
            success=True,
            intent=intent.strip().lower(),
            summary=summary,
        )
