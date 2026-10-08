from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LongRunningJobStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    FAILED = "failed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class LongRunningJobCheckpoint:
    job_id: str
    sequence: int
    status: str
    state: dict[str, Any]
    created_at: str = field(default_factory=_now)


@dataclass(frozen=True)
class LongRunningJobRecord:
    job_id: str
    objective: str
    status: str
    runtime_id: str | None
    sequence: int
    created_at: str
    updated_at: str
    failure_reason: str | None = None


class LongRunningJobManager:
    """Additive lifecycle boundary for durable-style long-running jobs.

    This manager coordinates state only; it never grants permission or executes
    protected actions. Persistence is intentionally injectable/portable via
    snapshots and checkpoints so later storage can be added without changing
    the authority boundary.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, LongRunningJobRecord] = {}
        self._checkpoints: dict[str, LongRunningJobCheckpoint] = {}
        self._history: dict[str, list[dict[str, Any]]] = {}

    def create(self, job_id: str, objective: str, runtime_id: str | None = None) -> LongRunningJobRecord:
        if not job_id.strip() or not objective.strip():
            raise ValueError("job_id and objective are required")
        if job_id in self._jobs:
            raise ValueError(f"job already exists: {job_id}")
        now = _now()
        record = LongRunningJobRecord(job_id, objective.strip(), LongRunningJobStatus.CREATED.value, runtime_id, 0, now, now)
        self._jobs[job_id] = record
        self._history[job_id] = [{"status": record.status, "timestamp": now}]
        return record

    def _transition(self, job_id: str, status: LongRunningJobStatus, reason: str | None = None) -> LongRunningJobRecord:
        record = self.get(job_id)
        terminal = {LongRunningJobStatus.STOPPED.value, LongRunningJobStatus.COMPLETED.value, LongRunningJobStatus.CANCELLED.value}
        if record.status in terminal:
            raise RuntimeError("terminal job cannot transition")
        if status == LongRunningJobStatus.RUNNING and record.status not in {LongRunningJobStatus.CREATED.value, LongRunningJobStatus.PAUSED.value, LongRunningJobStatus.FAILED.value}:
            raise RuntimeError("job cannot start/resume from current state")
        if status == LongRunningJobStatus.PAUSED and record.status != LongRunningJobStatus.RUNNING.value:
            raise RuntimeError("job must be running to pause")
        if status in {LongRunningJobStatus.STOPPED, LongRunningJobStatus.CANCELLED} and record.status not in {LongRunningJobStatus.CREATED.value, LongRunningJobStatus.RUNNING.value, LongRunningJobStatus.PAUSED.value}:
            raise RuntimeError("job cannot stop/cancel from current state")
        if status == LongRunningJobStatus.FAILED and not (reason and reason.strip()):
            raise ValueError("failure reason required")
        now = _now()
        updated = LongRunningJobRecord(record.job_id, record.objective, status.value, record.runtime_id, record.sequence + 1, record.created_at, now, reason)
        self._jobs[job_id] = updated
        self._history[job_id].append({"status": updated.status, "timestamp": now, "reason": reason})
        return updated

    def get(self, job_id: str) -> LongRunningJobRecord:
        if job_id not in self._jobs:
            raise KeyError(job_id)
        return self._jobs[job_id]

    def start(self, job_id: str) -> LongRunningJobRecord: return self._transition(job_id, LongRunningJobStatus.RUNNING)
    def pause(self, job_id: str) -> LongRunningJobRecord: return self._transition(job_id, LongRunningJobStatus.PAUSED)
    def resume(self, job_id: str) -> LongRunningJobRecord: return self._transition(job_id, LongRunningJobStatus.RUNNING)
    def stop(self, job_id: str) -> LongRunningJobRecord: return self._transition(job_id, LongRunningJobStatus.STOPPED)
    def cancel(self, job_id: str) -> LongRunningJobRecord: return self._transition(job_id, LongRunningJobStatus.CANCELLED)
    def fail(self, job_id: str, reason: str) -> LongRunningJobRecord: return self._transition(job_id, LongRunningJobStatus.FAILED, reason)
    def complete(self, job_id: str) -> LongRunningJobRecord: return self._transition(job_id, LongRunningJobStatus.COMPLETED)

    def checkpoint(self, job_id: str, state: dict[str, Any]) -> LongRunningJobCheckpoint:
        record = self.get(job_id)
        if record.status not in {LongRunningJobStatus.RUNNING.value, LongRunningJobStatus.PAUSED.value}:
            raise RuntimeError("job must be active or paused for checkpoint")
        safe = dict(state)
        forbidden = {"permission", "authority", "credentials", "credential", "token", "secret", "password"}
        safe = {k: v for k, v in safe.items() if k.lower() not in forbidden}
        cp = LongRunningJobCheckpoint(job_id, record.sequence, record.status, safe)
        self._checkpoints[job_id] = cp
        self._history[job_id].append({"event": "checkpoint", "sequence": cp.sequence, "timestamp": cp.created_at})
        return cp

    def checkpoint_for(self, job_id: str) -> LongRunningJobCheckpoint:
        if job_id not in self._checkpoints:
            raise KeyError(job_id)
        return self._checkpoints[job_id]

    def history(self, job_id: str) -> list[dict[str, Any]]:
        self.get(job_id)
        return [dict(item) for item in self._history[job_id]]

    def snapshot(self, job_id: str) -> dict[str, Any]:
        record = self.get(job_id)
        checkpoint = self._checkpoints.get(job_id)
        return {"job": record, "checkpoint": checkpoint, "history": self.history(job_id)}

    @staticmethod
    def grants_permission() -> bool: return False

    @staticmethod
    def executes_protected_actions() -> bool: return False
