from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Any

class WorkerStatus(str, Enum): IDLE='idle'; RUNNING='running'; PAUSED='paused'; STOPPED='stopped'; FAILED='failed'
@dataclass(frozen=True)
class WorkerResult:
    worker_id: str; success: bool; output: Any=None; error: str|None=None

class BackgroundWorkerOrchestrator:
    """Synchronous deterministic worker coordinator; no authority escalation."""
    def __init__(self): self._workers={}; self._status={}
    def register(self, worker_id: str, worker: Callable[[Any], Any]):
        if not worker_id.strip() or not callable(worker): raise ValueError('valid worker required')
        if worker_id in self._workers: raise ValueError('worker already registered')
        self._workers[worker_id]=worker; self._status[worker_id]=WorkerStatus.IDLE
    def run(self, worker_id: str, payload: Any=None) -> WorkerResult:
        if worker_id not in self._workers: raise KeyError(worker_id)
        self._status[worker_id]=WorkerStatus.RUNNING
        try:
            out=self._workers[worker_id](payload); self._status[worker_id]=WorkerStatus.IDLE
            return WorkerResult(worker_id,True,out)
        except Exception as exc:
            self._status[worker_id]=WorkerStatus.FAILED
            return WorkerResult(worker_id,False,error=str(exc))
    def pause(self, worker_id):
        if worker_id not in self._workers: raise KeyError(worker_id)
        self._status[worker_id]=WorkerStatus.PAUSED
    def stop(self, worker_id):
        if worker_id not in self._workers: raise KeyError(worker_id)
        self._status[worker_id]=WorkerStatus.STOPPED
    def status(self, worker_id): return self._status[worker_id]
    @staticmethod
    def can_grant_permission(): return False
    @staticmethod
    def can_bypass_authority(): return False
