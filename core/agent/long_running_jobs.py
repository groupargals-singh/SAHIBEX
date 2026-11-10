from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import hashlib
import json
import os
import tempfile
from pathlib import Path


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

    SCHEMA_VERSION = 1
    FORBIDDEN = {"permission", "authority", "credentials", "credential", "token", "secret", "password"}

    def __init__(self, persistence_path: str | Path | None = None) -> None:
        self._jobs: dict[str, LongRunningJobRecord] = {}
        self._checkpoints: dict[str, LongRunningJobCheckpoint] = {}
        self._history: dict[str, list[dict[str, Any]]] = {}
        self.persistence_path = Path(persistence_path).expanduser() if persistence_path else None
        if self.persistence_path is not None and self.persistence_path.exists():
            self._load()

    @classmethod
    def _clean(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(k): cls._clean(v) for k, v in value.items()
                    if not any(word in str(k).lower() for word in cls.FORBIDDEN)}
        if isinstance(value, list):
            return [cls._clean(v) for v in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return repr(value)

    def _snapshot(self) -> dict[str, Any]:
        return self._clean({
            "schema_version": self.SCHEMA_VERSION,
            "jobs": {k: vars(v) for k, v in self._jobs.items()},
            "checkpoints": {k: vars(v) for k, v in self._checkpoints.items()},
            "history": self._history,
        })

    def _persist(self) -> None:
        if self.persistence_path is None:
            return
        target = self.persistence_path
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = self._snapshot()
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        envelope = json.dumps({"payload": payload, "sha256": hashlib.sha256(canonical.encode()).hexdigest()},
                              sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(envelope); stream.flush(); os.fsync(stream.fileno())
            os.chmod(temporary, 0o600); os.replace(temporary, target)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)

    def _load(self) -> None:
        envelope = json.loads(self.persistence_path.read_text(encoding="utf-8"))
        payload = envelope.get("payload") if isinstance(envelope, dict) else None
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        if (not isinstance(payload, dict) or payload.get("schema_version") != self.SCHEMA_VERSION
                or hashlib.sha256(canonical.encode()).hexdigest() != envelope.get("sha256")):
            raise ValueError("job lifecycle store is corrupted or incompatible")
        jobs = {k: LongRunningJobRecord(**v) for k, v in payload.get("jobs", {}).items()}
        checkpoints = {k: LongRunningJobCheckpoint(**v) for k, v in payload.get("checkpoints", {}).items()}
        history = payload.get("history", {})
        if set(history) != set(jobs) or any(k != v.job_id for k, v in jobs.items()):
            raise ValueError("job lifecycle store identity validation failed")
        # A process cannot prove that an in-flight action survived a restart.
        # Convert RUNNING to PAUSED; never resume or execute during construction.
        now = _now()
        for job_id, record in list(jobs.items()):
            if record.status == LongRunningJobStatus.RUNNING.value:
                jobs[job_id] = LongRunningJobRecord(record.job_id, record.objective,
                    LongRunningJobStatus.PAUSED.value, record.runtime_id, record.sequence + 1,
                    record.created_at, now, "Interrupted by runtime restart; explicit resume required.")
                history[job_id] = list(history[job_id]) + [{"status": "paused", "timestamp": now,
                    "reason": "Interrupted by runtime restart; explicit resume required."}]
        self._jobs, self._checkpoints = jobs, checkpoints
        self._history = {k: list(v) for k, v in history.items()}
        self._persist()

    def create(self, job_id: str, objective: str, runtime_id: str | None = None) -> LongRunningJobRecord:
        if not job_id.strip() or not objective.strip():
            raise ValueError("job_id and objective are required")
        if job_id in self._jobs:
            raise ValueError(f"job already exists: {job_id}")
        now = _now()
        record = LongRunningJobRecord(job_id, objective.strip(), LongRunningJobStatus.CREATED.value, runtime_id, 0, now, now)
        self._jobs[job_id] = record
        self._history[job_id] = [{"status": record.status, "timestamp": now}]
        self._persist()
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
        self._persist()
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
        self._persist()
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
