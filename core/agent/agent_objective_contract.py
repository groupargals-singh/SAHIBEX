"""6P-1 durable Agent Goal & Objective Contract."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4

@dataclass(frozen=True)
class AgentObjective:
    objective: str
    intent: str
    priority: int = 0
    constraints: tuple[str, ...] = ()
    success_criteria: tuple[str, ...] = ()
    authority_context: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    goal_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str | None = None

    def __post_init__(self) -> None:
        if not self.objective.strip(): raise ValueError("objective must not be empty")
        if not self.intent.strip(): raise ValueError("intent must not be empty")
        if not isinstance(self.priority, int): raise TypeError("priority must be an integer")
        object.__setattr__(self, "constraints", tuple(self.constraints))
        object.__setattr__(self, "success_criteria", tuple(self.success_criteria))
        object.__setattr__(self, "authority_context", MappingProxyType(dict(self.authority_context)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def grants_permission(self) -> bool: return False
    @property
    def executes_protected_actions(self) -> bool: return False

    def with_update_timestamp(self, timestamp: str | None = None) -> "AgentObjective":
        return AgentObjective(self.objective, self.intent, self.priority, self.constraints,
            self.success_criteria, dict(self.authority_context), dict(self.metadata),
            self.goal_id, self.created_at, timestamp or datetime.now(timezone.utc).isoformat())
