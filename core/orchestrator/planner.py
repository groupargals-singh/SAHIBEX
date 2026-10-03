from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid

from core.orchestrator.task_state import (
    Goal,
    Task,
    TaskManager,
    TaskPriority,
)


class PlanStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class PlanStep:
    title: str
    description: str
    priority: TaskPriority = TaskPriority.NORMAL
    requires_approval: bool = False


@dataclass
class Plan:
    """
    Structured planning object.

    A Plan represents an intended sequence or group
    of work. It does not execute tasks or tools.
    """

    title: str
    description: str = ""

    plan_id: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )

    goal_id: str | None = None

    task_ids: list[str] = field(
        default_factory=list
    )

    status: PlanStatus = PlanStatus.PENDING

    result: Any = None
    error: str | None = None

    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    started_at: str | None = None
    completed_at: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    retry_count: int = 0
    max_retries: int = 3

    memory_ids: list[str] = field(
        default_factory=list
    )

    knowledge_ids: list[str] = field(
        default_factory=list
    )

    def add_memory_reference(
        self,
        memory_id: str,
    ) -> None:

        if not memory_id.strip():
            raise ValueError(
                "Memory reference cannot be empty."
            )

        if memory_id not in self.memory_ids:
            self.memory_ids.append(memory_id)

    def add_knowledge_reference(
        self,
        knowledge_id: str,
    ) -> None:

        if not knowledge_id.strip():
            raise ValueError(
                "Knowledge reference cannot be empty."
            )

        if knowledge_id not in self.knowledge_ids:
            self.knowledge_ids.append(knowledge_id)

    def mark_ready(self) -> None:
        if self.status != PlanStatus.PENDING:
            raise ValueError(
                "Only pending plans can become ready."
            )

        self.status = PlanStatus.READY

    def mark_running(self) -> None:
        if self.status not in (
            PlanStatus.READY,
            PlanStatus.BLOCKED,
            PlanStatus.WAITING_APPROVAL,
        ):
            raise ValueError(
                "Only ready, blocked, or "
                "approval-waiting plans "
                "can become running."
            )

        self.status = PlanStatus.RUNNING

        if self.started_at is None:
            self.started_at = datetime.now(
                timezone.utc
            ).isoformat()

    def mark_waiting_approval(self) -> None:
        if self.status not in (
            PlanStatus.PENDING,
            PlanStatus.READY,
            PlanStatus.RUNNING,
        ):
            raise ValueError(
                "Plan cannot wait for approval "
                "from its current state."
            )

        self.status = PlanStatus.WAITING_APPROVAL

    def mark_blocked(self, reason: str) -> None:
        if not reason.strip():
            raise ValueError(
                "Block reason cannot be empty."
            )

        self.status = PlanStatus.BLOCKED
        self.error = reason

    def complete(self, result: Any = None) -> None:
        if self.status != PlanStatus.RUNNING:
            raise ValueError(
                "Only running plans can be completed."
            )

        self.status = PlanStatus.COMPLETED
        self.result = result

        self.completed_at = datetime.now(
            timezone.utc
        ).isoformat()

    def fail(self, error: str) -> None:
        if not error.strip():
            raise ValueError(
                "Failure reason cannot be empty."
            )

        self.status = PlanStatus.FAILED
        self.error = error

        self.completed_at = datetime.now(
            timezone.utc
        ).isoformat()

    def retry(self) -> None:
        if self.status not in (
            PlanStatus.FAILED,
            PlanStatus.BLOCKED,
        ):
            raise ValueError(
                "Only failed or blocked plans "
                "can be retried."
            )

        if self.retry_count >= self.max_retries:
            raise ValueError(
                "Maximum plan retries exceeded."
            )

        self.retry_count += 1
        self.status = PlanStatus.READY
        self.error = None

    def cancel(self, reason: str = "") -> None:
        self.status = PlanStatus.CANCELLED

        if reason:
            self.error = reason

        self.completed_at = datetime.now(
            timezone.utc
        ).isoformat()


class PlanRegistry:
    """
    In-memory registry for SAHIBEX plans.

    The registry stores and retrieves Plan objects.
    It does not execute plans, tasks, commands, or tools.
    """

    def __init__(self) -> None:
        self.plans: dict[str, Plan] = {}

    def register(
        self,
        plan: Plan,
    ) -> Plan:

        if not plan.plan_id.strip():
            raise ValueError(
                "Plan ID cannot be empty."
            )

        if plan.plan_id in self.plans:
            raise ValueError(
                f"Plan already registered: "
                f"{plan.plan_id}"
            )

        self.plans[plan.plan_id] = plan

        return plan

    def get(
        self,
        plan_id: str,
    ) -> Plan | None:

        return self.plans.get(plan_id)

    def list_plans(self) -> list[Plan]:

        return list(self.plans.values())

    def count(self) -> int:

        return len(self.plans)


@dataclass(frozen=True)
class PlanResult:
    success: bool
    goal: Goal
    tasks: list[Task]
    message: str
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


class MasterPlanner:
    """
    SAHIBEX Master Planning Engine.

    Responsibilities:
    - Convert a high-level goal into structured tasks.
    - Create task dependencies.
    - Mark protected tasks.
    - Maintain execution-neutral planning.

    Important:
    This class NEVER executes commands or tools.
    It only creates a plan.
    """

    def __init__(
        self,
        task_manager: TaskManager | None = None,
    ) -> None:

        self.task_manager = (
            task_manager
            if task_manager is not None
            else TaskManager()
        )

    def create_plan(
        self,
        title: str,
        description: str,
        steps: list[PlanStep],
    ) -> PlanResult:

        if not title.strip():
            raise ValueError(
                "Plan title cannot be empty."
            )

        if not steps:
            raise ValueError(
                "A plan must contain at least one step."
            )

        goal = self.task_manager.create_goal(
            title=title,
            description=description,
        )

        created_tasks: list[Task] = []

        previous_task_id: str | None = None

        for step in steps:

            dependencies: list[str] = []

            if previous_task_id is not None:
                dependencies.append(
                    previous_task_id
                )

            task = self.task_manager.create_task(
                goal_id=goal.goal_id,
                title=step.title,
                description=step.description,
                priority=step.priority,
                requires_approval=(
                    step.requires_approval
                ),
                dependencies=dependencies,
            )

            created_tasks.append(task)

            previous_task_id = task.task_id

        return PlanResult(
            success=True,
            goal=goal,
            tasks=created_tasks,
            message=(
                "Master plan created successfully."
            ),
            metadata={
                "planner": "master_planner_v1",
                "task_count": len(created_tasks),
                "goal_id": goal.goal_id,
            },
        )

    def create_parallel_plan(
        self,
        title: str,
        description: str,
        steps: list[PlanStep],
    ) -> PlanResult:

        if not title.strip():
            raise ValueError(
                "Plan title cannot be empty."
            )

        if not steps:
            raise ValueError(
                "A plan must contain at least one step."
            )

        goal = self.task_manager.create_goal(
            title=title,
            description=description,
        )

        created_tasks: list[Task] = []

        for step in steps:

            task = self.task_manager.create_task(
                goal_id=goal.goal_id,
                title=step.title,
                description=step.description,
                priority=step.priority,
                requires_approval=(
                    step.requires_approval
                ),
            )

            created_tasks.append(task)

        return PlanResult(
            success=True,
            goal=goal,
            tasks=created_tasks,
            message=(
                "Parallel master plan created "
                "successfully."
            ),
            metadata={
                "planner": "master_planner_v1",
                "mode": "parallel",
                "task_count": len(created_tasks),
                "goal_id": goal.goal_id,
            },
        )

    def next_tasks(
        self,
        goal_id: str,
    ) -> list[Task]:

        return self.task_manager.ready_tasks(
            goal_id
        )

    def summary(
        self,
        goal_id: str,
    ) -> dict[str, Any]:

        return self.task_manager.goal_summary(
            goal_id
        )
