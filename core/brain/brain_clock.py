from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from time import monotonic, sleep
from typing import Callable


class BrainClockState(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"


@dataclass(frozen=True)
class ClockTick:
    sequence: int
    monotonic_time: float
    timestamp: str


class BrainClock:
    """Controlled, deterministic heartbeat/event loop for SAHIBEX.

    The clock schedules ticks only. It does not grant authority, execute
    protected actions, modify the system, or bypass any policy boundary.
    """

    def __init__(
        self,
        *,
        tick_interval: float = 1.0,
        clock: Callable[[], float] = monotonic,
        sleeper: Callable[[float], None] = sleep,
    ) -> None:
        if isinstance(tick_interval, bool) or tick_interval <= 0:
            raise ValueError("tick_interval must be greater than zero.")
        if not callable(clock):
            raise TypeError("clock must be callable.")
        if not callable(sleeper):
            raise TypeError("sleeper must be callable.")

        self.tick_interval = float(tick_interval)
        self._clock = clock
        self._sleep = sleeper
        self._state = BrainClockState.STOPPED
        self._sequence = 0
        self._last_tick: ClockTick | None = None
        self._failure_reason = ""

    @property
    def state(self) -> BrainClockState:
        return self._state

    @property
    def sequence(self) -> int:
        return self._sequence

    @property
    def last_tick(self) -> ClockTick | None:
        return self._last_tick

    @property
    def failure_reason(self) -> str:
        return self._failure_reason

    def start(self) -> None:
        if self._state == BrainClockState.FAILED:
            raise RuntimeError("failed clock must be reset before starting.")
        if self._state == BrainClockState.RUNNING:
            return
        self._state = BrainClockState.RUNNING

    def pause(self) -> None:
        if self._state != BrainClockState.RUNNING:
            raise RuntimeError("clock must be running to pause.")
        self._state = BrainClockState.PAUSED

    def resume(self) -> None:
        if self._state != BrainClockState.PAUSED:
            raise RuntimeError("clock must be paused to resume.")
        self._state = BrainClockState.RUNNING

    def stop(self) -> None:
        if self._state == BrainClockState.FAILED:
            return
        self._state = BrainClockState.STOPPED

    def reset(self) -> None:
        self._state = BrainClockState.STOPPED
        self._sequence = 0
        self._last_tick = None
        self._failure_reason = ""

    def tick(self, callback: Callable[[ClockTick], None] | None = None) -> ClockTick:
        if self._state != BrainClockState.RUNNING:
            raise RuntimeError("clock must be running to tick.")
        if callback is not None and not callable(callback):
            raise TypeError("callback must be callable.")

        self._sequence += 1
        tick = ClockTick(
            sequence=self._sequence,
            monotonic_time=float(self._clock()),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._last_tick = tick

        if callback is not None:
            try:
                callback(tick)
            except Exception as exc:
                self._state = BrainClockState.FAILED
                self._failure_reason = str(exc) or exc.__class__.__name__
                raise

        return tick

    def run(
        self,
        *,
        max_ticks: int | None = None,
        callback: Callable[[ClockTick], None] | None = None,
    ) -> tuple[ClockTick, ...]:
        if self._state != BrainClockState.RUNNING:
            raise RuntimeError("clock must be running before run().")
        if max_ticks is not None:
            if isinstance(max_ticks, bool) or max_ticks < 1:
                raise ValueError("max_ticks must be a positive integer.")
        if callback is not None and not callable(callback):
            raise TypeError("callback must be callable.")

        ticks: list[ClockTick] = []
        while self._state == BrainClockState.RUNNING:
            ticks.append(self.tick(callback))
            if max_ticks is not None and len(ticks) >= max_ticks:
                break
            self._sleep(self.tick_interval)

        return tuple(ticks)

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
    def is_scheduler_only() -> bool:
        return True
