from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

class RuntimeStatus(str, Enum):
    STOPPED='stopped'; RUNNING='running'; PAUSED='paused'; INTERRUPTED='interrupted'; FAILED='failed'

def _now(): return datetime.now(timezone.utc).isoformat()

@dataclass(frozen=True)
class RuntimeCheckpoint:
    runtime_id: str
    sequence: int
    status: str
    state: dict[str, Any]
    created_at: str = field(default_factory=_now)

class ContinuousRuntime:
    """Controlled continuous runtime; persistence/restore is explicit and permission-neutral."""
    def __init__(self, runtime_id: str):
        if not runtime_id.strip(): raise ValueError('runtime_id required')
        self.runtime_id=runtime_id; self.status=RuntimeStatus.STOPPED; self.sequence=0; self._state={}; self._checkpoint=None
    def start(self):
        if self.status in (RuntimeStatus.FAILED,): raise RuntimeError('failed runtime must be reset')
        self.status=RuntimeStatus.RUNNING
    def pause(self):
        if self.status != RuntimeStatus.RUNNING: raise RuntimeError('runtime must be running')
        self.status=RuntimeStatus.PAUSED
    def interrupt(self):
        if self.status not in (RuntimeStatus.RUNNING, RuntimeStatus.PAUSED): raise RuntimeError('runtime is not active')
        self.status=RuntimeStatus.INTERRUPTED
    def stop(self): self.status=RuntimeStatus.STOPPED
    def fail(self, reason: str):
        if not reason.strip(): raise ValueError('reason required')
        self._state['failure_reason']=reason; self.status=RuntimeStatus.FAILED
    def update_state(self, **values):
        if self.status != RuntimeStatus.RUNNING: raise RuntimeError('runtime must be running')
        self.sequence += 1; self._state.update(values)
    def checkpoint(self) -> RuntimeCheckpoint:
        self._checkpoint=RuntimeCheckpoint(self.runtime_id,self.sequence,self.status.value,dict(self._state))
        return self._checkpoint
    def restore(self, checkpoint: RuntimeCheckpoint):
        if checkpoint.runtime_id != self.runtime_id: raise ValueError('checkpoint runtime mismatch')
        self.sequence=checkpoint.sequence; self._state=dict(checkpoint.state); self.status=RuntimeStatus.PAUSED; self._checkpoint=checkpoint
    def state(self): return dict(self._state)
    @staticmethod
    def grants_permission(): return False
    @staticmethod
    def executes_protected_actions(): return False

class RuntimeCheckpointStore:
    def __init__(self): self._items={}
    def save(self, checkpoint): self._items[checkpoint.runtime_id]=checkpoint
    def load(self, runtime_id):
        if runtime_id not in self._items: raise KeyError(runtime_id)
        return self._items[runtime_id]
    def has(self, runtime_id): return runtime_id in self._items
