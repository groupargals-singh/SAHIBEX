from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class WorkerType(str, Enum):
    ARMY = "army"
    LABOR = "labor"


class WorkerTaskDecision(str, Enum):
    ALLOW = "allow"
    REQUIRE_AUTHORITY = "require_authority"
    DENY = "deny"


@dataclass(frozen=True)
class WorkerTask:
    task_id: str
    worker_id: str
    worker_type: WorkerType
    child_brain_id: str
    description: str


@dataclass(frozen=True)
class WorkerTaskResult:
    allowed: bool
    decision: WorkerTaskDecision
    reason: str
    task: WorkerTask | None = None


class ChildWorkerCoordinator:
    VERSION = "1.0"

    def __init__(self) -> None:
        self._tasks: dict[str, WorkerTask] = {}

    def assign_task(
        self,
        task_id: str,
        worker_id: str,
        worker_type: WorkerType,
        child_brain_id: str,
        description: str,
        authority_approved: bool = False,
    ) -> WorkerTaskResult:

        if not task_id or not worker_id or not child_brain_id:
            return WorkerTaskResult(
                False,
                WorkerTaskDecision.DENY,
                "task identity, worker identity and child identity are required",
            )

        if not description:
            return WorkerTaskResult(
                False,
                WorkerTaskDecision.DENY,
                "task description is required",
            )

        if task_id in self._tasks:
            return WorkerTaskResult(
                False,
                WorkerTaskDecision.DENY,
                "task already exists",
            )

        if not authority_approved:
            return WorkerTaskResult(
                False,
                WorkerTaskDecision.REQUIRE_AUTHORITY,
                "child authority approval required for worker task assignment",
            )

        task = WorkerTask(
            task_id=task_id,
            worker_id=worker_id,
            worker_type=worker_type,
            child_brain_id=child_brain_id,
            description=description,
        )

        self._tasks[task_id] = task

        return WorkerTaskResult(
            True,
            WorkerTaskDecision.ALLOW,
            "worker task assigned",
            task,
        )

    def get_task(self, task_id: str) -> WorkerTask | None:
        return self._tasks.get(task_id)

    def list_child_tasks(
        self,
        child_brain_id: str,
    ) -> list[WorkerTask]:
        return [
            task
            for task in self._tasks.values()
            if task.child_brain_id == child_brain_id
        ]

    def can_worker_assign_own_task(self) -> bool:
        return False

    def can_worker_grant_authority(self) -> bool:
        return False

    def can_worker_override_child(self) -> bool:
        return False

    def can_worker_override_mother(self) -> bool:
        return False

    def can_worker_self_promote(self) -> bool:
        return False

    def can_worker_execute_without_authority(self) -> bool:
        return False

    def can_worker_modify_constitution(self) -> bool:
        return False

    def can_worker_modify_soul(self) -> bool:
        return False
