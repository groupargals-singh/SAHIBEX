from __future__ import annotations
from dataclasses import dataclass, field
from uuid import uuid4
from core.agent_goal import AgentGoal

@dataclass(frozen=True)
class DecompositionTask:
    title: str
    objective: str
    intent: str
    success_criteria: tuple[str, ...]
    constraints: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    protected_action: bool = False
    verification_required: bool = True
    task_id: str = field(default_factory=lambda: str(uuid4()))

@dataclass(frozen=True)
class DecompositionExpansionResult:
    success: bool
    objective: str
    tasks: tuple[DecompositionTask, ...]
    decomposition_id: str = field(default_factory=lambda: str(uuid4()))
    error: str | None = None
    @property
    def grants_permission(self) -> bool: return False
    @property
    def executes_protected_actions(self) -> bool: return False

class GoalDecompositionExpansion:
    """Safe additive 6P-2 decomposition validation layer."""
    def decompose(self, goal: AgentGoal) -> DecompositionExpansionResult:
        if not isinstance(goal, AgentGoal):
            raise TypeError("goal must be AgentGoal.")
        objective=goal.objective.strip()
        constraints=tuple(goal.constraints)
        intent=goal.intent.strip().lower()
        verify=tuple(goal.success_criteria) or ("Result satisfies the objective.",)
        first=DecompositionTask("Understand objective", objective, intent, verify, constraints)
        protected = intent in {"write","delete","execute","network","credential","system_change","financial","self_update","external_control"}
        work=DecompositionTask("Perform required work", objective, intent, verify, constraints, (first.task_id,), protected, True)
        final=DecompositionTask("Verify result", objective, "verify", verify, constraints, (work.task_id,), False, True)
        return DecompositionExpansionResult(True, objective, (first,work,final))

    @staticmethod
    def validate(tasks: tuple[DecompositionTask, ...]) -> tuple[str, ...]:
        errors=[]; ids={x.task_id for x in tasks}
        if len(ids)!=len(tasks): errors.append("duplicate task identity")
        for task in tasks:
            if not task.success_criteria: errors.append(f"missing success criteria: {task.task_id}")
            if not task.verification_required: errors.append(f"verification required: {task.task_id}")
            for dep in task.dependencies:
                if dep not in ids: errors.append(f"unknown dependency: {dep}")
                if dep == task.task_id: errors.append(f"self dependency: {dep}")
        return tuple(errors)
