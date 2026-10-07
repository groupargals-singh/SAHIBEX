from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4
from core.agent.agent_objective_contract import AgentObjective

@dataclass(frozen=True)
class TaskIntakeResult:
    accepted: bool
    intake_id: str
    objective: AgentObjective | None
    errors: tuple[str, ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    @property
    def grants_permission(self) -> bool: return False
    @property
    def executes_protected_actions(self) -> bool: return False

class AgentTaskIntake:
    """6P-1 intake boundary: validate request and create an AgentObjective only."""
    def intake(self, objective: str, *, intent: str, priority: int = 0,
               constraints: tuple[str, ...] = (), success_criteria: tuple[str, ...] = (),
               authority_context: str = "user", metadata: dict | None = None) -> TaskIntakeResult:
        errors: list[str] = []
        if not isinstance(objective, str) or not objective.strip(): errors.append("objective must not be empty.")
        if not isinstance(intent, str) or not intent.strip(): errors.append("intent must not be empty.")
        if not isinstance(priority, int): errors.append("priority must be an integer.")
        if not isinstance(authority_context, str) or not authority_context.strip(): errors.append("authority_context must not be empty.")
        if not isinstance(constraints, tuple): errors.append("constraints must be tuple.")
        if not isinstance(success_criteria, tuple): errors.append("success_criteria must be tuple.")
        if not success_criteria: errors.append("at least one success criterion is required.")
        if errors: return TaskIntakeResult(False, str(uuid4()), None, tuple(errors))
        try:
            obj=AgentObjective(objective=objective.strip(), intent=intent.strip(), priority=priority,
                constraints=tuple(x.strip() for x in constraints), success_criteria=tuple(x.strip() for x in success_criteria),
                authority_context={"source": authority_context.strip()}, metadata=dict(metadata or {}))
        except (TypeError, ValueError) as exc:
            return TaskIntakeResult(False, str(uuid4()), None, (str(exc),))
        return TaskIntakeResult(True, str(uuid4()), obj)
