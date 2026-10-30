from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable
import hashlib
import json
import time
from threading import RLock


class WorkerLifecycle(str, Enum):
    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass(frozen=True)
class WorkerCheckpoint:
    worker_id: str
    job_id: str | None
    sequence: int
    state: dict[str, Any]
    state_hash: str
    created_at: float


@dataclass(frozen=True)
class WorkerRecord:
    worker_id: str
    job_id: str | None
    lifecycle: WorkerLifecycle
    runs: int
    failures: int
    last_error: str | None
    last_output: Any
    updated_at: float


@dataclass(frozen=True)
class WorkerRunResult:
    worker_id: str
    success: bool
    output: Any = None
    error: str | None = None
    sequence: int = 0


class BackgroundWorkerManager:
    """Bounded worker lifecycle manager; workers never gain authority."""

    SENSITIVE = {"permission", "authority", "credentials", "credential", "token", "secret", "password"}

    def __init__(self, max_workers: int = 8) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be positive")
        self._max_workers = max_workers
        self._workers: dict[str, Callable[[Any], Any]] = {}
        self._records: dict[str, WorkerRecord] = {}
        self._history: dict[str, list[WorkerRunResult]] = {}
        self._checkpoints: dict[str, WorkerCheckpoint] = {}
        # Protect lifecycle transitions and sequence/history updates. Worker
        # callables run outside this lock so unrelated workers remain usable.
        self._lock = RLock()

    def register(self, worker_id: str, worker: Callable[[Any], Any], job_id: str | None = None) -> WorkerRecord:
        if not isinstance(worker_id, str) or not worker_id.strip() or not callable(worker):
            raise ValueError("valid worker required")
        worker_id = worker_id.strip()
        with self._lock:
            if worker_id in self._workers:
                raise ValueError("worker already registered")
            if len(self._workers) >= self._max_workers:
                raise RuntimeError("worker capacity limit reached")
            now = time.time()
            self._workers[worker_id] = worker
            self._records[worker_id] = WorkerRecord(worker_id, job_id, WorkerLifecycle.READY, 0, 0, None, None, now)
            self._history[worker_id] = []
            return self._records[worker_id]

    def _set(self, worker_id: str, **changes: Any) -> WorkerRecord:
        old = self._records[worker_id]
        data = {
            "worker_id": old.worker_id, "job_id": old.job_id, "lifecycle": old.lifecycle,
            "runs": old.runs, "failures": old.failures, "last_error": old.last_error,
            "last_output": old.last_output, "updated_at": time.time(),
        }
        data.update(changes)
        self._records[worker_id] = WorkerRecord(**data)
        return self._records[worker_id]

    def run(self, worker_id: str, payload: Any = None) -> WorkerRunResult:
        with self._lock:
            if worker_id not in self._workers:
                raise KeyError(worker_id)
            rec = self._records[worker_id]
            if rec.lifecycle in {WorkerLifecycle.STOPPED, WorkerLifecycle.COMPLETED}:
                return WorkerRunResult(worker_id, False, error=f"worker is {rec.lifecycle.value}")
            if rec.lifecycle == WorkerLifecycle.PAUSED:
                return WorkerRunResult(worker_id, False, error="worker is paused")
            if rec.lifecycle == WorkerLifecycle.RUNNING:
                return WorkerRunResult(worker_id, False, error="worker is already running")
            run_sequence = rec.runs + 1
            self._set(worker_id, lifecycle=WorkerLifecycle.RUNNING, runs=run_sequence)
            worker = self._workers[worker_id]
        try:
            # Never hold the manager lock while calling worker-controlled code.
            output = worker(payload)
            result = WorkerRunResult(worker_id, True, output=output, sequence=run_sequence)
            with self._lock:
                self._history[worker_id].append(result)
                current = self._records[worker_id]
                lifecycle = current.lifecycle if current.lifecycle in {WorkerLifecycle.PAUSED, WorkerLifecycle.STOPPED} else WorkerLifecycle.READY
                self._set(worker_id, lifecycle=lifecycle, last_output=output, last_error=None)
            return result
        except Exception as exc:
            result = WorkerRunResult(worker_id, False, error=str(exc), sequence=run_sequence)
            with self._lock:
                self._history[worker_id].append(result)
                current = self._records[worker_id]
                self._set(worker_id, lifecycle=WorkerLifecycle.FAILED, failures=current.failures + 1, last_error=str(exc))
            return result

    def pause(self, worker_id: str) -> WorkerRecord:
        with self._lock:
            return self._set(worker_id, lifecycle=WorkerLifecycle.PAUSED)

    def resume(self, worker_id: str) -> WorkerRecord:
        with self._lock:
            rec = self._records[worker_id]
            if rec.lifecycle != WorkerLifecycle.PAUSED:
                raise RuntimeError("worker is not paused")
            return self._set(worker_id, lifecycle=WorkerLifecycle.READY)

    def stop(self, worker_id: str) -> WorkerRecord:
        with self._lock:
            return self._set(worker_id, lifecycle=WorkerLifecycle.STOPPED)

    def complete(self, worker_id: str) -> WorkerRecord:
        with self._lock:
            return self._set(worker_id, lifecycle=WorkerLifecycle.COMPLETED)

    def retry(self, worker_id: str) -> WorkerRecord:
        with self._lock:
            rec = self._records[worker_id]
            if rec.lifecycle != WorkerLifecycle.FAILED:
                raise RuntimeError("worker is not failed")
            return self._set(worker_id, lifecycle=WorkerLifecycle.READY, last_error=None)

    @classmethod
    def _sanitize(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(k): cls._sanitize(v) for k, v in value.items() if str(k).lower() not in cls.SENSITIVE}
        if isinstance(value, (list, tuple)):
            return [cls._sanitize(v) for v in value]
        return value

    @classmethod
    def _hash(cls, state: dict[str, Any]) -> str:
        raw = json.dumps(cls._sanitize(state), sort_keys=True, separators=(",", ":"), default=str).encode()
        return hashlib.sha256(raw).hexdigest()

    def checkpoint(self, worker_id: str, state: dict[str, Any], job_id: str | None = None) -> WorkerCheckpoint:
        safe = self._sanitize(dict(state))
        with self._lock:
            seq = len(self._history[worker_id]) + 1
            cp = WorkerCheckpoint(worker_id, job_id or self._records[worker_id].job_id, seq, safe, self._hash(safe), time.time())
            self._checkpoints[worker_id] = cp
            return cp

    def restore_checkpoint(self, worker_id: str) -> dict[str, Any]:
        with self._lock:
            cp = self._checkpoints[worker_id]
            if self._hash(cp.state) != cp.state_hash:
                raise ValueError("checkpoint integrity failure")
            return dict(cp.state)

    def record(self, worker_id: str) -> WorkerRecord:
        with self._lock:
            return self._records[worker_id]

    def history(self, worker_id: str) -> tuple[WorkerRunResult, ...]:
        with self._lock:
            return tuple(self._history[worker_id])

    @staticmethod
    def grants_permission() -> bool:
        return False

    @staticmethod
    def executes_protected_actions() -> bool:
        return False

    @staticmethod
    def can_bypass_authority() -> bool:
        return False
