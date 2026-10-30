from __future__ import annotations

import json
import multiprocessing as mp
import os
import pickle
import queue
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


_MAX_SERIALIZED_BYTES = 1_000_000


def _worker_entry(out_queue, handler, args, kwargs):
    try:
        value = handler(*args, **kwargs)
        payload = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        if len(payload) > _MAX_SERIALIZED_BYTES:
            out_queue.put(("error", "worker result exceeds 1 MB limit"))
        else:
            out_queue.put(("ok", payload))
    except BaseException as exc:
        out_queue.put(("error", f"{type(exc).__name__}: {str(exc)[:500]}"))


@dataclass(frozen=True)
class WorkerExecution:
    task_id: str
    status: str
    result: Any = None
    error: str | None = None
    attempt: int = 0


class ManagedWorkerRuntime:
    """Durable task ledger with isolated process execution and hard process termination.

    Task inputs/results are not persisted. A handler must be importable/picklable
    by multiprocessing; prefer module-level functions. Runtime state records only
    task identity, status, timestamps, attempt count, and bounded error text.
    """

    TERMINAL = {"completed", "failed", "timed_out", "cancelled"}

    def __init__(self, database_path: str | Path, *, max_workers: int = 2):
        if isinstance(max_workers, bool) or not isinstance(max_workers, int) or not 1 <= max_workers <= 8:
            raise ValueError("max_workers must be between 1 and 8")
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers
        self._ctx = mp.get_context("fork")
        self._active: dict[str, tuple[mp.Process, Any, float, int]] = {}
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("""CREATE TABLE IF NOT EXISTS worker_tasks (
                task_id TEXT PRIMARY KEY, status TEXT NOT NULL,
                created_at REAL NOT NULL, updated_at REAL NOT NULL,
                attempt INTEGER NOT NULL, max_retries INTEGER NOT NULL,
                timeout_seconds REAL NOT NULL, error TEXT
            )""")
            db.execute("UPDATE worker_tasks SET status='failed', error='manager restarted while task was active', updated_at=? WHERE status='running'", (time.time(),))

    def _connect(self):
        db = sqlite3.connect(str(self.database_path), timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def _update(self, task_id: str, status: str, attempt: int, error: str | None = None):
        with self._connect() as db:
            db.execute("UPDATE worker_tasks SET status=?, attempt=?, error=?, updated_at=? WHERE task_id=?",
                       (status, attempt, error[:500] if error else None, time.time(), task_id))

    def submit(self, task_id: str, handler: Callable[..., Any], *, args=(), kwargs=None,
               timeout_seconds: float = 10.0, max_retries: int = 0) -> WorkerExecution:
        if not isinstance(task_id, str) or not task_id.strip() or len(task_id) > 128:
            raise ValueError("task_id must be 1..128 non-whitespace characters")
        if not callable(handler):
            raise TypeError("handler must be callable")
        if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool) or not 0.05 <= timeout_seconds <= 300:
            raise ValueError("timeout_seconds must be between 0.05 and 300")
        if isinstance(max_retries, bool) or not isinstance(max_retries, int) or max_retries != 0:
            raise ValueError("automatic retries are disabled; side-effecting handlers must be explicitly made idempotent before retry support is enabled")
        kwargs = dict(kwargs or {})
        try:
            packed = pickle.dumps((handler, tuple(args), kwargs), protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as exc:
            raise TypeError("handler and arguments must be serializable for process execution") from exc
        if len(packed) > _MAX_SERIALIZED_BYTES:
            raise ValueError("worker input exceeds 1 MB limit")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT status, attempt, error FROM worker_tasks WHERE task_id=?", (task_id,)).fetchone()
            if existing:
                return WorkerExecution(task_id, existing["status"], error=existing["error"], attempt=existing["attempt"])
            active = db.execute("SELECT COUNT(*) FROM worker_tasks WHERE status='running'").fetchone()[0]
            if active >= self.max_workers:
                raise RuntimeError("worker capacity reached; submit rejected")
            now = time.time()
            db.execute("INSERT INTO worker_tasks VALUES (?, 'running', ?, ?, 1, ?, ?, NULL)",
                       (task_id, now, now, max_retries, float(timeout_seconds)))
        q = self._ctx.Queue(maxsize=1)
        proc = self._ctx.Process(target=_worker_entry, args=(q, handler, tuple(args), kwargs), daemon=True)
        try:
            proc.start()
        except Exception as exc:
            self._update(task_id, "failed", 1, f"worker start failed: {exc}")
            q.close()
            return WorkerExecution(task_id, "failed", error=f"worker start failed: {exc}", attempt=1)
        self._active[task_id] = (proc, q, time.monotonic() + float(timeout_seconds), max_retries)
        return WorkerExecution(task_id, "running", attempt=1)

    def wait(self, task_id: str, *, poll_interval: float = 0.02) -> WorkerExecution:
        if not 0.001 <= poll_interval <= 1:
            raise ValueError("poll_interval must be between 0.001 and 1")
        active = self._active.get(task_id)
        if active is None:
            with self._connect() as db:
                row = db.execute("SELECT status, attempt, error FROM worker_tasks WHERE task_id=?", (task_id,)).fetchone()
            if row is None:
                raise KeyError(task_id)
            return WorkerExecution(task_id, row["status"], error=row["error"], attempt=row["attempt"])
        proc, q, deadline, max_retries = active
        attempt = 1
        while proc.is_alive() and time.monotonic() < deadline:
            proc.join(timeout=min(poll_interval, max(0, deadline - time.monotonic())))
        if proc.is_alive():
            proc.terminate()
            proc.join(timeout=0.5)
            if proc.is_alive() and hasattr(proc, "kill"):
                proc.kill()
                proc.join(timeout=0.5)
            self._active.pop(task_id, None)
            q.close()
            self._update(task_id, "timed_out", attempt, "worker exceeded hard timeout and was terminated")
            return WorkerExecution(task_id, "timed_out", error="worker exceeded hard timeout and was terminated", attempt=attempt)
        try:
            kind, payload = q.get(timeout=0.2)
        except queue.Empty:
            kind, payload = "error", f"worker exited without result (exitcode={proc.exitcode})"
        finally:
            q.close()
            self._active.pop(task_id, None)
        if kind == "ok":
            result = pickle.loads(payload)
            self._update(task_id, "completed", attempt)
            return WorkerExecution(task_id, "completed", result=result, attempt=attempt)
        self._update(task_id, "failed", attempt, str(payload))
        return WorkerExecution(task_id, "failed", error=str(payload), attempt=attempt)

    def cancel(self, task_id: str, reason: str = "cancelled by operator") -> WorkerExecution:
        active = self._active.pop(task_id, None)
        if active is None:
            with self._connect() as db:
                row = db.execute("SELECT status, attempt, error FROM worker_tasks WHERE task_id=?", (task_id,)).fetchone()
            if row is None:
                raise KeyError(task_id)
            return WorkerExecution(task_id, row["status"], error=row["error"], attempt=row["attempt"])
        proc, q, _deadline, _retries = active
        if proc.is_alive():
            proc.terminate()
            proc.join(timeout=0.5)
        if proc.is_alive() and hasattr(proc, "kill"):
            proc.kill()
            proc.join(timeout=0.5)
        q.close()
        self._update(task_id, "cancelled", 1, reason[:500])
        return WorkerExecution(task_id, "cancelled", error=reason[:500], attempt=1)

    def get(self, task_id: str) -> WorkerExecution:
        with self._connect() as db:
            row = db.execute("SELECT status, attempt, error FROM worker_tasks WHERE task_id=?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(task_id)
        return WorkerExecution(task_id, row["status"], error=row["error"], attempt=row["attempt"])

    def list_tasks(self) -> list[WorkerExecution]:
        with self._connect() as db:
            rows = db.execute("SELECT task_id, status, attempt, error FROM worker_tasks ORDER BY created_at").fetchall()
        return [WorkerExecution(r["task_id"], r["status"], error=r["error"], attempt=r["attempt"]) for r in rows]
