"""Emergency-stop safety latch for SAHIBEX."""
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class EmergencyStopState(str, Enum):
    CLEAR = "clear"
    STOPPED = "stopped"


@dataclass(frozen=True)
class EmergencyStopEvent:
    state: EmergencyStopState
    reason: str
    timestamp: str


class EmergencyStop:
    """Fail-closed safety latch; it never grants or executes authority."""

    def __init__(self) -> None:
        self._state = EmergencyStopState.CLEAR
        self._history: list[EmergencyStopEvent] = []

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _reason(reason: str) -> str:
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason must be a non-empty string")
        return reason.strip()

    @property
    def state(self) -> EmergencyStopState:
        return self._state

    @property
    def engaged(self) -> bool:
        return self._state is EmergencyStopState.STOPPED

    @property
    def history(self) -> tuple[EmergencyStopEvent, ...]:
        return tuple(self._history)

    def engage(self, reason: str) -> EmergencyStopEvent:
        event = EmergencyStopEvent(
            EmergencyStopState.STOPPED, self._reason(reason), self._timestamp()
        )
        self._state = event.state
        self._history.append(event)
        return event

    def clear(self, reason: str) -> EmergencyStopEvent:
        event = EmergencyStopEvent(
            EmergencyStopState.CLEAR, self._reason(reason), self._timestamp()
        )
        self._state = event.state
        self._history.append(event)
        return event

    def allows_protected_execution(self) -> bool:
        return not self.engaged

    def requires_execution_block(self) -> bool:
        return self.engaged

    def grants_permission(self) -> bool:
        return False

    def executes_actions(self) -> bool:
        return False

    def modifies_system(self) -> bool:
        return False

    def overrides_human_authority(self) -> bool:
        return False

    def is_safety_latch(self) -> bool:
        return True
