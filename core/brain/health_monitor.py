from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from core.brain.brain_clock import BrainClock, BrainClockState
from core.brain.wake_sleep_state import WakeSleepController, WakeSleepState


class BrainHealth(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class HealthSnapshot:
    timestamp: str
    health: BrainHealth
    online: bool
    awake: bool
    sleeping: bool
    clock_running: bool
    reason: str


class HealthMonitor:
    """Read-only health observer. Sleep is online low-activity mode."""

    def __init__(self, *, wake_sleep=None, clock=None):
        if wake_sleep is not None and not isinstance(wake_sleep, WakeSleepController):
            raise TypeError("wake_sleep must be a WakeSleepController or None.")
        if clock is not None and not isinstance(clock, BrainClock):
            raise TypeError("clock must be a BrainClock or None.")
        self._wake_sleep = wake_sleep
        self._clock = clock

    def check(self) -> HealthSnapshot:
        timestamp = datetime.now(timezone.utc).isoformat()
        if self._wake_sleep is None:
            return HealthSnapshot(timestamp, BrainHealth.UNKNOWN, True, False, False, False, "lifecycle_source_unavailable")

        state = self._wake_sleep.state
        sleeping = state is WakeSleepState.SLEEPING
        awake = state is WakeSleepState.AWAKE
        clock_running = self._clock is not None and self._clock.state is BrainClockState.RUNNING
        clock_failed = self._clock is not None and self._clock.state is BrainClockState.FAILED

        if clock_failed:
            health, reason = BrainHealth.CRITICAL, "brain_clock_failed"
        elif state is WakeSleepState.AWAKING:
            health, reason = BrainHealth.DEGRADED, "wake_transition_in_progress"
        elif sleeping:
            health, reason = BrainHealth.HEALTHY, "online_sleep_mode_low_activity"
        elif awake and self._clock is not None and not clock_running:
            health, reason = BrainHealth.DEGRADED, "awake_but_clock_not_running"
        elif awake:
            health, reason = BrainHealth.HEALTHY, "online_active"
        else:
            health, reason = BrainHealth.UNKNOWN, "unknown_lifecycle_state"

        return HealthSnapshot(timestamp, health, True, awake, sleeping, clock_running, reason)

    @staticmethod
    def is_read_only() -> bool:
        return True

    @staticmethod
    def grants_permission() -> bool:
        return False

    @staticmethod
    def executes_actions() -> bool:
        return False

    @staticmethod
    def modifies_system() -> bool:
        return False

    @staticmethod
    def sleep_is_offline() -> bool:
        return False

    @staticmethod
    def keeps_mother_brain_online() -> bool:
        return True
