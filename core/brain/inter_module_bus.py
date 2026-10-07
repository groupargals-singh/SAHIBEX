"""Controlled inter-module messaging and parallel work coordination."""
from dataclasses import dataclass
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable


@dataclass(frozen=True)
class ModuleMessage:
    channel: str
    source: str
    payload: Any
    sequence: int
    timestamp: str


class InterModuleBus:
    """In-process module bus with bounded parallel dispatch."""

    def __init__(self, max_workers: int = 4) -> None:
        if not isinstance(max_workers, int) or max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        self._max_workers = max_workers
        self._sequence = 0
        self._history: list[ModuleMessage] = []
        self._handlers: dict[str, list[Callable[[ModuleMessage], Any]]] = {}

    @staticmethod
    def _text(value: str, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")
        return value.strip()

    def subscribe(self, channel: str, handler: Callable[[ModuleMessage], Any]) -> None:
        channel = self._text(channel, "channel")
        if not callable(handler):
            raise TypeError("handler must be callable")
        self._handlers.setdefault(channel, []).append(handler)

    def send(self, channel: str, source: str, payload: Any) -> ModuleMessage:
        channel = self._text(channel, "channel")
        source = self._text(source, "source")
        self._sequence += 1
        message = ModuleMessage(
            channel, source, payload, self._sequence,
            datetime.now(timezone.utc).isoformat()
        )
        self._history.append(message)
        return message

    def dispatch(self, message: ModuleMessage) -> list[Any]:
        handlers = tuple(self._handlers.get(message.channel, ()))
        if not handlers:
            return []
        with ThreadPoolExecutor(max_workers=min(self._max_workers, len(handlers))) as pool:
            return list(pool.map(lambda fn: fn(message), handlers))

    def publish(self, channel: str, source: str, payload: Any) -> list[Any]:
        return self.dispatch(self.send(channel, source, payload))

    @property
    def history(self) -> tuple[ModuleMessage, ...]:
        return tuple(self._history)

    @property
    def max_workers(self) -> int:
        return self._max_workers

    def grants_permission(self) -> bool:
        return False

    def executes_protected_actions(self) -> bool:
        return False

    def modifies_system(self) -> bool:
        return False
