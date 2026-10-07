"""Controlled recovery state machine for the SAHIBEX root brain."""
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class RecoveryState(str, Enum):
    READY = "ready"
    RECOVERING = "recovering"
    RECOVERED = "recovered"
    FAILED = "failed"


@dataclass(frozen=True)
class RecoveryEvent:
    state: RecoveryState
    reason: str
    timestamp: str


class RecoveryController:
    """Tracks recovery; it never grants permission or executes protected work."""

    def __init__(self) -> None:
        self._state = RecoveryState.READY
        self._history: list[RecoveryEvent] = []

    @staticmethod
    def _time() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _reason(reason: str) -> str:
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason must be a non-empty string")
        return reason.strip()

    @property
    def state(self) -> RecoveryState:
        return self._state

    @property
    def history(self) -> tuple[RecoveryEvent, ...]:
        return tuple(self._history)

    def begin(self, reason: str) -> RecoveryEvent:
        event = RecoveryEvent(RecoveryState.RECOVERING, self._reason(reason), self._time())
        self._state = event.state
        self._history.append(event)
        return event

    def complete(self, reason: str) -> RecoveryEvent:
        event = RecoveryEvent(RecoveryState.RECOVERED, self._reason(reason), self._time())
        self._state = event.state
        self._history.append(event)
        return event

    def fail(self, reason: str) -> RecoveryEvent:
        event = RecoveryEvent(RecoveryState.FAILED, self._reason(reason), self._time())
        self._state = event.state
        self._history.append(event)
        return event

    def reset(self, reason: str) -> RecoveryEvent:
        event = RecoveryEvent(RecoveryState.READY, self._reason(reason), self._time())
        self._state = event.state
        self._history.append(event)
        return event

    def grants_permission(self) -> bool:
        return False

    def executes_actions(self) -> bool:
        return False

    def modifies_system(self) -> bool:
        return False

    def overrides_human_authority(self) -> bool:
        return False

    def is_lifecycle_controller(self) -> bool:
        return True
