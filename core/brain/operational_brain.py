from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class OperationalBrainResult:
    success: bool
    objective: str
    intent: str
    status: str
    result_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be bool")

        if not isinstance(self.objective, str):
            raise TypeError("objective must be str")

        if not self.objective.strip():
            raise ValueError("objective must not be empty")

        if not isinstance(self.intent, str):
            raise TypeError("intent must be str")

        if not self.intent.strip():
            raise ValueError("intent must not be empty")

        if not isinstance(self.status, str):
            raise TypeError("status must be str")

        if not self.status.strip():
            raise ValueError("status must not be empty")

        if not isinstance(self.result_id, str):
            raise TypeError("result_id must be str")

        if not self.result_id.strip():
            raise ValueError("result_id must not be empty")


class OperationalBrain:
    """
    Contract-level operational brain.

    This layer does not:
    - execute tools
    - call external models
    - access the network
    - grant permissions
    - override the constitution
    - execute protected actions
    """

    def process(
        self,
        *,
        objective: str,
        intent: str,
    ) -> OperationalBrainResult:
        if not isinstance(objective, str):
            raise TypeError("objective must be str")

        if not objective.strip():
            raise ValueError("objective must not be empty")

        if not isinstance(intent, str):
            raise TypeError("intent must be str")

        if not intent.strip():
            raise ValueError("intent must not be empty")

        normalized_objective = objective.strip()
        normalized_intent = intent.strip().lower()

        return OperationalBrainResult(
            success=True,
            objective=normalized_objective,
            intent=normalized_intent,
            status="READY",
        )
