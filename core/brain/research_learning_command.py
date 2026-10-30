from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable
from threading import RLock
from uuid import uuid4


class DepartmentOperation(str, Enum):
    RESEARCH = "research"
    LEARN = "learn"


class TaskStage(str, Enum):
    RECEIVED = "received"
    PLANNED = "planned"
    ARMY_ASSIGNED = "army_assigned"
    LABOUR_ASSIGNED = "labour_assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    UNVERIFIED = "unverified"


@dataclass(frozen=True)
class CommandEvent:
    stage: TaskStage
    detail: str


@dataclass(frozen=True)
class DepartmentCommandTrace:
    task_id: str
    operation: DepartmentOperation
    army_id: str
    labour_brain_id: str
    status: TaskStage
    started_at: str
    finished_at: str
    events: tuple[CommandEvent, ...]


@dataclass(frozen=True)
class DepartmentCommandResult:
    result: Any
    trace: DepartmentCommandTrace


class ResearchLearningCommander:
    """Auditable command boundary for the Research & Learning Department.

    Existing integrations remain authoritative for acquisition, verification,
    and persistence. This layer routes tasks and records their lifecycle; it
    does not pretend that each pipeline stage is an independent AI model.
    """

    VERSION = "1.0"
    ROUTES = {
        DepartmentOperation.RESEARCH: ("research_army", "research_pipeline_labour"),
        DepartmentOperation.LEARN: ("learning_army", "learning_pipeline_labour"),
    }

    def __init__(self) -> None:
        self._last_trace: DepartmentCommandTrace | None = None
        self._trace_lock = RLock()

    @property
    def last_trace(self) -> DepartmentCommandTrace | None:
        with self._trace_lock:
            return self._last_trace

    def dispatch(self, operation: DepartmentOperation, subject: str, worker: Callable[[], Any]) -> DepartmentCommandResult:
        if not isinstance(operation, DepartmentOperation):
            raise TypeError("operation must be DepartmentOperation")
        if not isinstance(subject, str) or not subject.strip():
            raise ValueError("task subject must not be empty")
        if not callable(worker):
            raise TypeError("worker must be callable")

        task_id = str(uuid4())
        started_at = datetime.now(timezone.utc).isoformat()
        army_id, labour_brain_id = self.ROUTES[operation]
        events = [
            CommandEvent(TaskStage.RECEIVED, "task received by department commander"),
            CommandEvent(TaskStage.PLANNED, "existing integration pipeline selected"),
            CommandEvent(TaskStage.ARMY_ASSIGNED, army_id),
            CommandEvent(TaskStage.LABOUR_ASSIGNED, labour_brain_id),
            CommandEvent(TaskStage.RUNNING, "delegating to existing pipeline"),
        ]
        status = TaskStage.FAILED
        result: Any = None
        try:
            result = worker()
            verification_status = str(getattr(result, "verification_status", ""))
            verified_flag = getattr(result, "verified", None)
            persisted_flag = getattr(result, "persisted", None)
            verified = verification_status == "VERIFIED" and verified_flag is not False
            verified = verified and persisted_flag is not False
            if operation is DepartmentOperation.LEARN:
                count = getattr(result, "verified_knowledge_count", None)
                if count is not None:
                    verified = verified and int(count or 0) > 0
            success = bool(getattr(result, "success", False))
            if success and verified:
                status = TaskStage.COMPLETED
                events.append(CommandEvent(status, "pipeline returned a verified result"))
            elif success or verification_status == "PENDING":
                status = TaskStage.UNVERIFIED
                events.append(CommandEvent(status, "result did not satisfy verification gate"))
            else:
                status = TaskStage.FAILED
                events.append(CommandEvent(status, "pipeline did not complete successfully"))
        except Exception:
            events.append(CommandEvent(TaskStage.FAILED, "pipeline raised an exception"))
            raise
        finally:
            trace = DepartmentCommandTrace(
                task_id=task_id,
                operation=operation,
                army_id=army_id,
                labour_brain_id=labour_brain_id,
                status=status,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc).isoformat(),
                events=tuple(events),
            )
            with self._trace_lock:
                self._last_trace = trace
        return DepartmentCommandResult(result=result, trace=trace)

    def dispatch_workers(
        self,
        operation: DepartmentOperation,
        subject: str,
        *,
        army_worker: Callable[[str], Any],
        labour_worker: Callable[[str], Any],
        verify_results: Callable[[Any, Any], bool],
    ) -> DepartmentCommandResult:
        """Run two distinct workers and fail closed unless their joint result verifies."""
        if not isinstance(operation, DepartmentOperation):
            raise TypeError("operation must be DepartmentOperation")
        if not isinstance(subject, str) or not subject.strip():
            raise ValueError("task subject must not be empty")
        if not callable(army_worker) or not callable(labour_worker):
            raise TypeError("both worker callbacks are required")
        if army_worker is labour_worker:
            raise ValueError("army_and_labour_workers_must_be_distinct")
        if not callable(verify_results):
            raise TypeError("verify_results must be callable")
        task_id = str(uuid4())
        started_at = datetime.now(timezone.utc).isoformat()
        army_id, labour_id = self.ROUTES[operation]
        events = [
            CommandEvent(TaskStage.RECEIVED, "task received"),
            CommandEvent(TaskStage.PLANNED, "task split between Army and Labour"),
            CommandEvent(TaskStage.ARMY_ASSIGNED, army_id),
            CommandEvent(TaskStage.LABOUR_ASSIGNED, labour_id),
            CommandEvent(TaskStage.RUNNING, "invoking both distinct worker callbacks"),
        ]
        status = TaskStage.FAILED
        result = None
        try:
            army_result = army_worker(subject.strip())
            labour_result = labour_worker(subject.strip())
            verified = (
                army_result is not None
                and labour_result is not None
                and bool(verify_results(army_result, labour_result))
            )
            result = {
                "army_result": army_result,
                "labour_result": labour_result,
                "verification_status": "VERIFIED" if verified else "UNVERIFIED",
            }
            status = TaskStage.COMPLETED if verified else TaskStage.UNVERIFIED
            events.append(CommandEvent(status, "both worker results verified" if verified else "missing or conflicting worker results"))
        except Exception:
            events.append(CommandEvent(TaskStage.FAILED, "worker orchestration raised an exception"))
            raise
        finally:
            trace = DepartmentCommandTrace(
                task_id=task_id, operation=operation, army_id=army_id,
                labour_brain_id=labour_id, status=status, started_at=started_at,
                finished_at=datetime.now(timezone.utc).isoformat(), events=tuple(events),
            )
            with self._trace_lock:
                self._last_trace = trace
        return DepartmentCommandResult(result=result, trace=trace)

    def capability_contract(self) -> dict[str, bool]:
        return {
            "department_command": True,
            "army_routing": True,
            "labour_pipeline_delegation": True,
            "dual_worker_execution": True,
            "joint_result_verification": True,
            "task_trace": True,
            "independent_worker_models": False,
            "permission_authority": False,
            "tool_execution_authority": False,
            "constitution_mutation": False,
            "child_brain_creation": False,
        }
