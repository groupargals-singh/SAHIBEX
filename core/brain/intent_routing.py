from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class BrainIntentRoutingResult:
    """
    Result of routing an intent to a specialist brain.

    This object represents a routing decision only.
    It does not execute the selected brain or grant permissions.
    """

    success: bool
    intent: str
    brain_id: str
    route_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")

        if not isinstance(self.intent, str):
            raise TypeError("intent must be a string.")

        if not self.intent.strip():
            raise ValueError(
                "intent must be a non-empty string."
            )

        if not isinstance(self.brain_id, str):
            raise TypeError("brain_id must be a string.")

        if not self.brain_id.strip():
            raise ValueError(
                "brain_id must be a non-empty string."
            )

        if not isinstance(self.route_id, str) or not self.route_id.strip():
            raise ValueError(
                "route_id must be a non-empty string."
            )


class BrainIntentRouter:
    """
    Contract-level intent-to-specialist-brain router.

    This layer normalizes an intent and selected brain identity.
    It does not execute brains, grant permissions, access credentials,
    or modify the constitution.
    """

    def route(
        self,
        *,
        intent: str,
        brain_id: str,
    ) -> BrainIntentRoutingResult:
        if not isinstance(intent, str):
            raise TypeError("intent must be a string.")

        if not intent.strip():
            raise ValueError(
                "intent must be a non-empty string."
            )

        if not isinstance(brain_id, str):
            raise TypeError("brain_id must be a string.")

        if not brain_id.strip():
            raise ValueError(
                "brain_id must be a non-empty string."
            )

        return BrainIntentRoutingResult(
            success=True,
            intent=intent.strip().lower(),
            brain_id=brain_id.strip(),
        )
