from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class BrainOrchestrationResult:
    """
    Result of a master-brain orchestration plan.

    This object represents an orchestration plan only.
    It does not execute specialist brains or grant permissions.
    """

    success: bool
    brain_ids: list[str]
    objective: str
    plan_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")

        if not isinstance(self.brain_ids, list):
            raise TypeError("brain_ids must be a list.")

        if not self.brain_ids:
            raise ValueError(
                "brain_ids must contain at least one brain ID."
            )

        for brain_id in self.brain_ids:
            if not isinstance(brain_id, str):
                raise TypeError(
                    "every brain ID must be a string."
                )

            if not brain_id.strip():
                raise ValueError(
                    "brain IDs must not be empty."
                )

        if not isinstance(self.objective, str):
            raise TypeError("objective must be a string.")

        if not self.objective.strip():
            raise ValueError(
                "objective must be a non-empty string."
            )

        if not isinstance(self.plan_id, str) or not self.plan_id.strip():
            raise ValueError(
                "plan_id must be a non-empty string."
            )


class BrainOrchestration:
    """
    Contract-level specialist-brain orchestration.

    This layer creates a normalized plan describing which
    specialist brains should participate in a task.

    It does not execute brains, access external systems,
    grant permissions, or modify the constitution.
    """

    def create_plan(
        self,
        *,
        brain_ids: list[str],
        objective: str,
    ) -> BrainOrchestrationResult:
        if not isinstance(brain_ids, list):
            raise TypeError("brain_ids must be a list.")

        if not brain_ids:
            raise ValueError(
                "brain_ids must contain at least one brain ID."
            )

        normalized_brain_ids: list[str] = []

        for brain_id in brain_ids:
            if not isinstance(brain_id, str):
                raise TypeError(
                    "every brain ID must be a string."
                )

            normalized = brain_id.strip()

            if not normalized:
                raise ValueError(
                    "brain IDs must not be empty."
                )

            if normalized not in normalized_brain_ids:
                normalized_brain_ids.append(normalized)

        if not isinstance(objective, str):
            raise TypeError("objective must be a string.")

        if not objective.strip():
            raise ValueError(
                "objective must be a non-empty string."
            )

        return BrainOrchestrationResult(
            success=True,
            brain_ids=normalized_brain_ids,
            objective=objective,
        )
