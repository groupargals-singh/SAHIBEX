"""Deterministic internal state bus for SAHIBEX modules."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable


@dataclass(frozen=True)
class StateEvent:
    topic: str
    value: Any
    source: str
    timestamp: str
    sequence: int


class InternalStateBus:
    """In-process state publication/subscription boundary."""

    def __init__(self) -> None:
        self._sequence = 0
        self._state: dict[str, Any] = {}
        self._history: list[StateEvent] = []
        self._subscribers: dict[str, list[Callable[[StateEvent], None]]] = {}

    @staticmethod
    def _text(value: str, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")
        return value.strip()

    def publish(self, topic: str, value: Any, source: str) -> StateEvent:
        topic = self._text(topic, "topic")
        source = self._text(source, "source")
        self._sequence += 1
        event = StateEvent(
            topic, value, source,
            datetime.now(timezone.utc).isoformat(), self._sequence
        )
        self._state[topic] = value
        self._history.append(event)
        for callback in tuple(self._subscribers.get(topic, ())):
            callback(event)
        return event

    def get(self, topic: str, default: Any = None) -> Any:
        return self._state.get(self._text(topic, "topic"), default)

    def subscribe(
        self, topic: str, callback: Callable[[StateEvent], None]
    ) -> None:
        topic = self._text(topic, "topic")
        if not callable(callback):
            raise TypeError("callback must be callable")
        self._subscribers.setdefault(topic, []).append(callback)

    @property
    def history(self) -> tuple[StateEvent, ...]:
        return tuple(self._history)

    @property
    def sequence(self) -> int:
        return self._sequence

    def grants_permission(self) -> bool:
        return False

    def executes_actions(self) -> bool:
        return False

    def modifies_system(self) -> bool:
        return False
