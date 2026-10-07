from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from core.brain.brain_clock import BrainClock, BrainClockState


class WakeSleepState(str, Enum):
    SLEEPING = "sleeping"
    AWAKING = "awaking"
    AWAKE = "awake"


@dataclass(frozen=True)
class WakeSleepTransition:
    previous: WakeSleepState
    current: WakeSleepState
    reason: str
    timestamp: str


class WakeSleepController:
    """Controlled WAKE/SLEEP lifecycle boundary for the SAHIBEX brain.

    This controller manages lifecycle state only. It never grants permission,
    executes protected actions, or modifies the system.
    """

    def __init__(self, *, clock: BrainClock | None = None) -> None:
        if clock is not None and not isinstance(clock, BrainClock):
            raise TypeError("clock must be a BrainClock or None.")

        self._clock = clock
        self._state = WakeSleepState.SLEEPING
        self._history: list[WakeSleepTransition] = []

    @property
    def state(self) -> WakeSleepState:
        return self._state

    @property
    def history(self) -> tuple[WakeSleepTransition, ...]:
        return tuple(self._history)

    @property
    def can_process(self) -> bool:
        return self._state == WakeSleepState.AWAKE

    @property
    def can_heartbeat(self) -> bool:
        """The root brain remains online even while sleeping."""
        return self._state in (
            WakeSleepState.SLEEPING,
            WakeSleepState.AWAKING,
            WakeSleepState.AWAKE,
        )

    def wake(self, reason: str = "wake_requested") -> WakeSleepTransition:
        self._validate_reason(reason)
        if self._state != WakeSleepState.SLEEPING:
            raise RuntimeError("brain must be sleeping before wake().")

        previous = self._state
        self._state = WakeSleepState.AWAKING

        try:
            if self._clock is not None:
                self._clock.start()
        except Exception:
            self._state = previous
            raise

        self._state = WakeSleepState.AWAKE
        return self._record(previous, self._state, reason)

    def sleep(self, reason: str = "sleep_requested") -> WakeSleepTransition:
        self._validate_reason(reason)
        if self._state != WakeSleepState.AWAKE:
            raise RuntimeError("brain must be awake before sleep().")

        previous = self._state

        if self._clock is not None:
            # Sleep reduces processing but keeps the root heartbeat online.
            if self._clock.state == BrainClockState.PAUSED:
                self._clock.resume()
            elif self._clock.state == BrainClockState.STOPPED:
                self._clock.start()

        self._state = WakeSleepState.SLEEPING
        return self._record(previous, self._state, reason)

    def reset(self, reason: str = "reset") -> WakeSleepTransition:
        self._validate_reason(reason)
        previous = self._state

        if self._clock is not None:
            self._clock.stop()

        self._state = WakeSleepState.SLEEPING
        return self._record(previous, self._state, reason)

    def clock_state(self) -> BrainClockState | None:
        return None if self._clock is None else self._clock.state

    @staticmethod
    def grants_permission() -> bool:
        return False

    @staticmethod
    def executes_actions() -> bool:
        return False

    @staticmethod
    def executes_protected_actions() -> bool:
        return False

    @staticmethod
    def modifies_system() -> bool:
        return False

    @staticmethod
    def is_lifecycle_only() -> bool:
        return True

    def _record(
        self,
        previous: WakeSleepState,
        current: WakeSleepState,
        reason: str,
    ) -> WakeSleepTransition:
        transition = WakeSleepTransition(
            previous=previous,
            current=current,
            reason=reason.strip(),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._history.append(transition)
        return transition

    @staticmethod
    def _validate_reason(reason: str) -> None:
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason must be a non-empty string.")
