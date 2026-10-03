from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class AgentStatus(str, Enum):
    CREATED = "created"
    READY = "ready"
    PLANNING = "planning"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"
    VERIFYING = "verifying"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


VALID_TRANSITIONS: dict[AgentStatus, frozenset[AgentStatus]] = {
    AgentStatus.CREATED: frozenset({
        AgentStatus.READY,
        AgentStatus.CANCELLED,
    }),
    AgentStatus.READY: frozenset({
        AgentStatus.PLANNING,
        AgentStatus.CANCELLED,
        AgentStatus.PAUSED,
    }),
    AgentStatus.PLANNING: frozenset({
        AgentStatus.RUNNING,
        AgentStatus.BLOCKED,
        AgentStatus.FAILED,
        AgentStatus.CANCELLED,
    }),
    AgentStatus.RUNNING: frozenset({
        AgentStatus.WAITING_APPROVAL,
        AgentStatus.BLOCKED,
        AgentStatus.VERIFYING,
        AgentStatus.RECOVERING,
        AgentStatus.PAUSED,
        AgentStatus.FAILED,
        AgentStatus.CANCELLED,
    }),
    AgentStatus.WAITING_APPROVAL: frozenset({
        AgentStatus.RUNNING,
        AgentStatus.BLOCKED,
        AgentStatus.CANCELLED,
    }),
    AgentStatus.BLOCKED: frozenset({
        AgentStatus.READY,
        AgentStatus.PLANNING,
        AgentStatus.RECOVERING,
        AgentStatus.FAILED,
        AgentStatus.CANCELLED,
    }),
    AgentStatus.VERIFYING: frozenset({
        AgentStatus.COMPLETED,
        AgentStatus.RECOVERING,
        AgentStatus.FAILED,
        AgentStatus.BLOCKED,
    }),
    AgentStatus.RECOVERING: frozenset({
        AgentStatus.READY,
        AgentStatus.PLANNING,
        AgentStatus.RUNNING,
        AgentStatus.FAILED,
        AgentStatus.CANCELLED,
    }),
    AgentStatus.PAUSED: frozenset({
        AgentStatus.READY,
        AgentStatus.CANCELLED,
    }),
    AgentStatus.COMPLETED: frozenset(),
    AgentStatus.FAILED: frozenset({
        AgentStatus.RECOVERING,
        AgentStatus.CANCELLED,
    }),
    AgentStatus.CANCELLED: frozenset(),
}


@dataclass
class AgentState:
    agent_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    status: AgentStatus = AgentStatus.CREATED
    reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.agent_id, str):
            raise TypeError("agent_id must be str.")
        if not self.agent_id.strip():
            raise ValueError("agent_id must not be empty.")

        if not isinstance(self.status, AgentStatus):
            raise TypeError(
                "status must be an AgentStatus."
            )

        if not isinstance(self.reason, str):
            raise TypeError("reason must be str.")

    def can_transition_to(
        self,
        target: AgentStatus,
    ) -> bool:
        if not isinstance(target, AgentStatus):
            raise TypeError(
                "target must be an AgentStatus."
            )

        return target in VALID_TRANSITIONS[self.status]

    def transition(
        self,
        target: AgentStatus,
        *,
        reason: str = "",
    ) -> None:
        if not isinstance(target, AgentStatus):
            raise TypeError(
                "target must be an AgentStatus."
            )

        if not self.can_transition_to(target):
            raise ValueError(
                f"Invalid agent transition: "
                f"{self.status.value} -> {target.value}"
            )

        if not isinstance(reason, str):
            raise TypeError("reason must be str.")

        self.status = target
        self.reason = reason

    @property
    def terminal(self) -> bool:
        return self.status in {
            AgentStatus.COMPLETED,
            AgentStatus.CANCELLED,
        }

    @property
    def active(self) -> bool:
        return self.status in {
            AgentStatus.PLANNING,
            AgentStatus.RUNNING,
            AgentStatus.WAITING_APPROVAL,
            AgentStatus.BLOCKED,
            AgentStatus.VERIFYING,
            AgentStatus.RECOVERING,
        }
