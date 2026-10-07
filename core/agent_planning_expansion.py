from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from core.agent_decomposition_expansion import DecompositionTask


@dataclass(frozen=True)
class PlanningTask:
    task_id: str
    title: str
    objective: str
    dependencies: tuple[str, ...]
    constraints: tuple[str, ...]
    success_criteria: tuple[str, ...]
    requires_approval: bool
    verification_required: bool
    sequence: int


@dataclass(frozen=True)
class PlanningResult:
    success: bool
    tasks: tuple[PlanningTask, ...]
    plan_id: str = field(default_factory=lambda: str(uuid4()))
    error: str | None = None
    grants_permission: bool = False
    executes_protected_actions: bool = False


class AgentPlanningExpansion:
    def build_plan(self, tasks: tuple[DecompositionTask, ...]) -> PlanningResult:
        if not isinstance(tasks, tuple) or not tasks:
            raise ValueError("tasks must be a non-empty tuple")
        ids = {task.task_id for task in tasks}
        for task in tasks:
            if not isinstance(task, DecompositionTask):
                raise TypeError("all tasks must be DecompositionTask")
            if any(dep not in ids for dep in task.dependencies):
                return PlanningResult(False, (), error="unknown dependency")

        remaining = list(tasks)
        ordered: list[DecompositionTask] = []
        completed: set[str] = set()
        while remaining:
            ready = [task for task in remaining if all(dep in completed for dep in task.dependencies)]
            if not ready:
                return PlanningResult(False, (), error="dependency cycle detected")
            for task in ready:
                ordered.append(task)
                completed.add(task.task_id)
                remaining.remove(task)

        planned = tuple(
            PlanningTask(
                task_id=task.task_id,
                title=task.title,
                objective=task.objective,
                dependencies=task.dependencies,
                constraints=task.constraints,
                success_criteria=task.success_criteria,
                requires_approval=task.protected_action,
                verification_required=task.verification_required,
                sequence=index,
            )
            for index, task in enumerate(ordered, start=1)
        )
        return PlanningResult(True, planned)

    @staticmethod
    def validate(plan: PlanningResult) -> tuple[str, ...]:
        if not plan.success:
            return (plan.error or "planning failed",)
        errors: list[str] = []
        seen: set[str] = set()
        for task in plan.tasks:
            if task.task_id in seen:
                errors.append("duplicate task id")
            seen.add(task.task_id)
            if not task.success_criteria:
                errors.append("missing success criteria")
            if not task.verification_required:
                errors.append("verification missing")
            if any(dep not in seen for dep in task.dependencies):
                errors.append("dependency order invalid")
        return tuple(errors)
