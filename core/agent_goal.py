from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class AgentGoal:
    objective: str
    intent: str
    priority: str = "normal"
    constraints: tuple[str, ...] = ()
    success_criteria: tuple[str, ...] = ()
    authority_context: str = "user"
    goal_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.objective, str):
            raise TypeError("objective must be str.")
        if not self.objective.strip():
            raise ValueError("objective must not be empty.")

        if not isinstance(self.intent, str):
            raise TypeError("intent must be str.")
        if not self.intent.strip():
            raise ValueError("intent must not be empty.")

        if not isinstance(self.priority, str):
            raise TypeError("priority must be str.")
        if not self.priority.strip():
            raise ValueError("priority must not be empty.")

        if not isinstance(self.constraints, tuple):
            raise TypeError("constraints must be tuple.")
        for item in self.constraints:
            if not isinstance(item, str):
                raise TypeError(
                    "every constraint must be str."
                )
            if not item.strip():
                raise ValueError(
                    "constraints cannot contain empty strings."
                )

        if not isinstance(self.success_criteria, tuple):
            raise TypeError(
                "success_criteria must be tuple."
            )
        for item in self.success_criteria:
            if not isinstance(item, str):
                raise TypeError(
                    "every success criterion must be str."
                )
            if not item.strip():
                raise ValueError(
                    "success_criteria cannot contain "
                    "empty strings."
                )

        if not isinstance(self.authority_context, str):
            raise TypeError(
                "authority_context must be str."
            )
        if not self.authority_context.strip():
            raise ValueError(
                "authority_context must not be empty."
            )

        if not isinstance(self.goal_id, str):
            raise TypeError("goal_id must be str.")
        if not self.goal_id.strip():
            raise ValueError("goal_id must not be empty.")

        if not isinstance(self.created_at, datetime):
            raise TypeError(
                "created_at must be datetime."
            )

        if not isinstance(self.metadata, dict):
            raise TypeError("metadata must be dict.")
