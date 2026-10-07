"""Phase Y observability expansion.

Additive, read-only observability primitives. These records describe runtime
activity but never grant authority, permissions, credentials, or execution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ObservationEvent:
    event_type: str
    actor_id: str
    timestamp: datetime = field(default_factory=_utc_now)
    task_id: str | None = None
    model_id: str | None = None
    tool_id: str | None = None
    result_status: str | None = None
    verification_status: str | None = None
    error_class: str | None = None
    resource_usage: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelToolObservation:
    model_id: str | None
    tool_id: str | None
    provider_id: str | None = None
    capability: str | None = None
    success: bool | None = None


@dataclass(frozen=True)
class ErrorObservation:
    error_class: str
    message: str
    recoverable: bool
    timestamp: datetime = field(default_factory=_utc_now)


class ObservabilityEngine:
    """In-memory, read-only observation collector.

    It records facts supplied by callers and exposes snapshots. It does not
    execute actions, change permissions, or transfer authority.
    """

    def __init__(self, max_events: int = 1000) -> None:
        if max_events < 1:
            raise ValueError("max_events must be >= 1")
        self._max_events = max_events
        self._events: list[ObservationEvent] = []

    @property
    def is_authority(self) -> bool:
        return False

    @property
    def grants_permission(self) -> bool:
        return False

    def record(self, event: ObservationEvent) -> ObservationEvent:
        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events :]
        return event

    def snapshot(self) -> tuple[ObservationEvent, ...]:
        return tuple(self._events)

    def latest(self) -> ObservationEvent | None:
        return self._events[-1] if self._events else None

    def errors(self) -> tuple[ObservationEvent, ...]:
        return tuple(e for e in self._events if e.error_class is not None)

    def model_tool_events(self) -> tuple[ObservationEvent, ...]:
        return tuple(
            e for e in self._events
            if e.model_id is not None or e.tool_id is not None
        )

    def resource_usage(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(e.resource_usage for e in self._events if e.resource_usage)
