from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any

from core.brain.backup_recovery_expansion import BackupRecoveryManager
from core.brain.brain_clock import BrainClock
from core.brain.health_monitor import HealthMonitor, BrainHealth
from core.brain.root_identity import SahibexRootIdentity
from core.brain.wake_sleep_state import WakeSleepController, WakeSleepState


class LifecycleState(str, Enum):
    NEW = "new"
    STARTING = "starting"
    RUNNING = "running"
    SLEEPING = "sleeping"
    RECOVERING = "recovering"
    STOPPED = "stopped"
    CRASHED = "crashed"


@dataclass(frozen=True)
class BrainVersion:
    version: str
    schema_version: int
    identity_version: str


@dataclass(frozen=True)
class LifecycleCheckpoint:
    checkpoint_id: str
    sequence: int
    state: dict[str, Any]
    checksum: str
    brain_version: BrainVersion
    identity_fingerprint: str
    created_at: str


@dataclass(frozen=True)
class LifecycleStatus:
    state: LifecycleState
    health: BrainHealth
    awake: bool
    checkpoint_sequence: int
    brain_version: BrainVersion


class BrainLifecycle:
    """Phase 12 lifecycle control plane.

    Lifecycle state is controlled and observable. It never grants permission,
    changes the Constitution, or executes protected actions.
    """

    VERSION = BrainVersion("12.0.0", 1, "1.0")

    def __init__(
        self,
        *,
        root_identity: SahibexRootIdentity | None = None,
        clock: BrainClock | None = None,
    ) -> None:
        self.root_identity = root_identity or SahibexRootIdentity()
        if not self.root_identity.validate():
            raise RuntimeError("root identity integrity validation failed")

        self.clock = clock or BrainClock()
        self.wake_sleep = WakeSleepController(clock=self.clock)
        self.health = HealthMonitor(wake_sleep=self.wake_sleep, clock=self.clock)
        self.state = LifecycleState.NEW
        self._sequence = 0
        self._checkpoint: LifecycleCheckpoint | None = None
        self._backup_manifest = None
        self._last_error = ""

    @property
    def checkpoint(self) -> LifecycleCheckpoint | None:
        return self._checkpoint

    @property
    def last_error(self) -> str:
        return self._last_error

    def startup(self) -> LifecycleStatus:
        self._validate_identity()
        if self.state not in {
            LifecycleState.NEW,
            LifecycleState.STOPPED,
            LifecycleState.CRASHED,
            LifecycleState.RECOVERING,
        }:
            raise RuntimeError("brain cannot start from current lifecycle state")
        self.state = LifecycleState.STARTING
        try:
            self.clock.reset()
            self.wake_sleep.reset("startup")
            self.wake_sleep.wake("startup")
            self.state = LifecycleState.RUNNING
            self._last_error = ""
            return self.status()
        except Exception as exc:
            self.state = LifecycleState.CRASHED
            self._last_error = str(exc) or exc.__class__.__name__
            raise

    def sleep(self) -> LifecycleStatus:
        if self.state != LifecycleState.RUNNING:
            raise RuntimeError("brain must be running before sleep")
        self.wake_sleep.sleep("lifecycle_sleep")
        self.state = LifecycleState.SLEEPING
        return self.status()

    def wake(self) -> LifecycleStatus:
        if self.state != LifecycleState.SLEEPING:
            raise RuntimeError("brain must be sleeping before wake")
        self.wake_sleep.wake("lifecycle_wake")
        self.state = LifecycleState.RUNNING
        return self.status()

    def checkpoint_state(self, state: dict[str, Any], *, checkpoint_id: str = "auto") -> LifecycleCheckpoint:
        if self.state not in {LifecycleState.RUNNING, LifecycleState.SLEEPING}:
            raise RuntimeError("checkpoint requires a running or sleeping brain")
        if not isinstance(state, dict):
            raise TypeError("state must be a dictionary")
        self._validate_identity()
        safe_state = self._json_safe(state)
        self._sequence += 1
        checksum = self._checksum(safe_state)
        self._checkpoint = LifecycleCheckpoint(
            checkpoint_id=str(checkpoint_id),
            sequence=self._sequence,
            state=safe_state,
            checksum=checksum,
            brain_version=self.VERSION,
            identity_fingerprint=self.root_identity.fingerprint,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        return self._checkpoint

    def restore_checkpoint(
        self,
        checkpoint: LifecycleCheckpoint | None = None,
        *,
        authorized: bool = False,
    ) -> dict[str, Any]:
        if authorized is not True:
            raise PermissionError("checkpoint restore requires explicit authorization")
        cp = checkpoint or self._checkpoint
        if cp is None:
            raise ValueError("no checkpoint available")
        self._validate_identity()
        if cp.identity_fingerprint != self.root_identity.fingerprint:
            raise ValueError("checkpoint identity integrity mismatch")
        if cp.brain_version.schema_version != self.VERSION.schema_version:
            raise ValueError("checkpoint schema version is incompatible")
        if self._checksum(cp.state) != cp.checksum:
            raise ValueError("checkpoint state integrity failure")
        self._sequence = max(self._sequence, cp.sequence)
        return dict(cp.state)

    def backup_state(self, state: dict[str, Any], *, backup_id: str = "lifecycle") -> dict[str, Any]:
        if not isinstance(state, dict):
            raise TypeError("state must be a dictionary")
        self._validate_identity()
        safe_state = BackupRecoveryManager.sanitize_state(self._json_safe(state))
        manifest = BackupRecoveryManager.manifest(
            backup_id,
            safe_state,
            self.VERSION.version,
            schema_version=self.VERSION.schema_version,
        )
        self._backup_manifest = manifest
        return {"state": safe_state, "manifest": manifest}

    def restore_backup(self, backup: dict[str, Any], *, authorized: bool = False) -> dict[str, Any]:
        if authorized is not True:
            raise PermissionError("backup restore requires explicit authorization")
        if not isinstance(backup, dict) or not isinstance(backup.get("state"), dict):
            raise TypeError("backup must contain a state dictionary")
        manifest = backup.get("manifest")
        if manifest is None or not BackupRecoveryManager.verify_integrity(backup["state"], manifest):
            raise ValueError("backup integrity verification failed")
        if manifest.schema_version != self.VERSION.schema_version:
            raise ValueError("backup schema version is incompatible")
        self._validate_identity()
        return dict(backup["state"])

    def recover_from_crash(self, *, checkpoint: LifecycleCheckpoint | None = None, authorized: bool = False) -> dict[str, Any]:
        if self.state != LifecycleState.CRASHED:
            raise RuntimeError("crash recovery requires CRASHED state")
        self.state = LifecycleState.RECOVERING
        try:
            restored = self.restore_checkpoint(checkpoint, authorized=authorized)
            self.startup()
            return restored
        except Exception as exc:
            self.state = LifecycleState.CRASHED
            self._last_error = str(exc) or exc.__class__.__name__
            raise

    def mark_crashed(self, reason: str) -> None:
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason must be a non-empty string")
        self.state = LifecycleState.CRASHED
        self._last_error = reason.strip()

    def shutdown(self) -> LifecycleStatus:
        self.wake_sleep.reset("shutdown")
        self.state = LifecycleState.STOPPED
        return self.status()

    def status(self) -> LifecycleStatus:
        snapshot = self.health.check()
        return LifecycleStatus(
            state=self.state,
            health=snapshot.health,
            awake=snapshot.awake,
            checkpoint_sequence=self._sequence,
            brain_version=self.VERSION,
        )

    def verify_integrity(self) -> bool:
        return self.root_identity.validate()

    @staticmethod
    def grants_permission() -> bool:
        return False

    @staticmethod
    def modifies_constitution() -> bool:
        return False

    @staticmethod
    def overrides_human_authority() -> bool:
        return False

    @staticmethod
    def executes_protected_actions() -> bool:
        return False

    def _validate_identity(self) -> None:
        if not self.root_identity.validate():
            raise RuntimeError("SAHIBEX identity integrity validation failed")

    @staticmethod
    def _checksum(payload: dict[str, Any]) -> str:
        data = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _json_safe(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(k): BrainLifecycle._json_safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [BrainLifecycle._json_safe(v) for v in value]
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        raise TypeError(f"state contains unsupported value: {type(value).__name__}")
