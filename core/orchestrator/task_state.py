from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from typing import Any
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Task:
    """
    Atomic unit of work inside SAHIBEX.

    Important:
    A Task describes work.
    It does NOT execute the work.
    """

    title: str
    description: str = ""

    task_id: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )

    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL

    parent_task_id: str | None = None

    dependencies: list[str] = field(
        default_factory=list
    )

    requires_approval: bool = False

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
        if self.status != TaskStatus.PENDING:
            raise ValueError(
                "Only pending tasks can become ready."
            )

        self.status = TaskStatus.READY

    def mark_running(self) -> None:
        if self.status != TaskStatus.READY:
            raise ValueError(
                "Only ready tasks can start running."
            )

        self.status = TaskStatus.RUNNING

        self.started_at = datetime.now(
            timezone.utc
        ).isoformat()

    def mark_waiting_approval(self) -> None:
        self.status = TaskStatus.WAITING_APPROVAL

    def mark_blocked(self, reason: str) -> None:
        self.status = TaskStatus.BLOCKED
        self.error = reason

    def complete(self, result: Any = None) -> None:
        if self.status != TaskStatus.RUNNING:
            raise ValueError(
                "Only running tasks can be completed."
            )

        self.status = TaskStatus.COMPLETED
        self.result = result

        self.completed_at = datetime.now(
            timezone.utc
        ).isoformat()

    def fail(self, error: str) -> None:
        if not error.strip():
            raise ValueError(
                "Failure reason cannot be empty."
            )

        self.status = TaskStatus.FAILED
        self.error = error

        self.completed_at = datetime.now(
            timezone.utc
        ).isoformat()

    def retry(self) -> None:
        if self.status != TaskStatus.FAILED:
            raise ValueError(
                "Only failed tasks can be retried."
            )

        if self.retry_count >= self.max_retries:
            raise ValueError(
                "Maximum task retries exceeded."
            )

        self.retry_count += 1
        self.status = TaskStatus.READY
        self.error = None

    def cancel(self, reason: str = "") -> None:
        self.status = TaskStatus.CANCELLED

        if reason:
            self.error = reason

        self.completed_at = datetime.now(
            timezone.utc
        ).isoformat()


@dataclass
class Goal:
    """
    High-level objective.

    A Goal can contain multiple Tasks.
    """

    title: str
    description: str = ""

    goal_id: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )

    tasks: list[Task] = field(
        default_factory=list
    )

    created_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def get_task(
        self,
        task_id: str,
    ) -> Task | None:

        for task in self.tasks:
            if task.task_id == task_id:
                return task

        return None

    def completed_tasks(self) -> int:
        return sum(
            task.status == TaskStatus.COMPLETED
            for task in self.tasks
        )

    def failed_tasks(self) -> int:
        return sum(
            task.status == TaskStatus.FAILED
            for task in self.tasks
        )

    def is_complete(self) -> bool:
        if not self.tasks:
            return False

        return all(
            task.status == TaskStatus.COMPLETED
            for task in self.tasks
        )

    def summary(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "title": self.title,
            "task_count": len(self.tasks),
            "completed": self.completed_tasks(),
            "failed": self.failed_tasks(),
            "complete": self.is_complete(),
        }


class TaskManager:
    """
    Central in-memory task/goal state manager.

    This manager tracks state only.
    It does not execute tools or commands.
    """

    def __init__(self, storage: Any | None = None) -> None:
        self.goals: dict[str, Goal] = {}
        self.tasks: dict[str, Task] = {}
        self.storage = storage
        if self.storage is not None:
            # Rehydrate the complete graph before accepting new work.
            for goal in self.storage.list_goals():
                recovered = False
                for task in goal.tasks:
                    if task.status == TaskStatus.RUNNING:
                        task.status = TaskStatus.READY
                        task.metadata = dict(task.metadata)
                        task.metadata["recovered_after_restart"] = True
                        recovered = True
                self._attach_goal(goal)
                if recovered:
                    self.storage.save_planning_graph(goal)
            # Older stores may have task rows not embedded in their goal row.
            for task in self.storage.list_tasks():
                if task.task_id not in self.tasks:
                    owner = next((g for g in self.storage.list_goals()
                                  if any(t.task_id == task.task_id for t in g.tasks)), None)
                    if owner is not None:
                        self.tasks[task.task_id] = task

    def _attach_goal(self, goal: Goal) -> None:
        self.goals[goal.goal_id] = goal
        for task in goal.tasks:
            self.tasks[task.task_id] = task

    def persist_goal(self, goal_id: str) -> None:
        """Atomically persist a goal's full task graph through ResearchStorage."""
        if self.storage is None:
            return
        goal = self.get_goal(goal_id)
        if goal is None:
            raise KeyError(f"Unknown goal: {goal_id}")
        self.storage.save_planning_graph(goal)

    def create_goal(
        self,
        title: str,
        description: str = "",
    ) -> Goal:

        if not title.strip():
            raise ValueError(
                "Goal title cannot be empty."
            )

        goal = Goal(
            title=title.strip(),
            description=description.strip(),
        )

        self.goals[goal.goal_id] = goal
        self.persist_goal(goal.goal_id)

        return goal

    def create_task(
        self,
        goal_id: str,
        title: str,
        description: str = "",
        *,
        priority: TaskPriority = TaskPriority.NORMAL,
        requires_approval: bool = False,
        parent_task_id: str | None = None,
        dependencies: list[str] | None = None,
    ) -> Task:

        if goal_id not in self.goals:
            raise KeyError(
                f"Unknown goal: {goal_id}"
            )

        if not title.strip():
            raise ValueError(
                "Task title cannot be empty."
            )

        task = Task(
            title=title.strip(),
            description=description.strip(),
            priority=priority,
            requires_approval=requires_approval,
            parent_task_id=parent_task_id,
            dependencies=list(
                dependencies or []
            ),
        )

        self.tasks[task.task_id] = task

        self.goals[goal_id].add_task(task)
        self.persist_goal(goal_id)

        return task

    def get_task(
        self,
        task_id: str,
    ) -> Task | None:

        return self.tasks.get(task_id)

    def get_goal(
        self,
        goal_id: str,
    ) -> Goal | None:

        return self.goals.get(goal_id)

    def ready_tasks(
        self,
        goal_id: str,
    ) -> list[Task]:

        goal = self.get_goal(goal_id)

        if goal is None:
            raise KeyError(
                f"Unknown goal: {goal_id}"
            )

        ready: list[Task] = []

        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.LOW: 3,
        }

        for task in goal.tasks:

            if task.status not in {TaskStatus.PENDING, TaskStatus.READY}:
                continue

            dependencies_complete = all(
                self.tasks.get(
                    dependency_id
                ) is not None
                and self.tasks[
                    dependency_id
                ].status == TaskStatus.COMPLETED
                for dependency_id
                in task.dependencies
            )

            if dependencies_complete:
                ready.append(task)

        ready.sort(
            key=lambda task: priority_order[
                task.priority
            ]
        )

        return ready

    def cancel_goal(
        self,
        goal_id: str,
        reason: str = "",
    ) -> None:

        goal = self.get_goal(goal_id)

        if goal is None:
            raise KeyError(
                f"Unknown goal: {goal_id}"
            )

        for task in goal.tasks:

            if task.status not in {
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            }:
                task.cancel(reason)
        self.persist_goal(goal_id)

    def goal_summary(
        self,
        goal_id: str,
    ) -> dict[str, Any]:

        goal = self.get_goal(goal_id)

        if goal is None:
            raise KeyError(
                f"Unknown goal: {goal_id}"
            )

        return goal.summary()
