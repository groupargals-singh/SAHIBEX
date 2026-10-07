from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


FAILURE_MEMORY_VERSION = "P2-FM-1"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class FailureMemory:
    """
    Structured memory of a failed attempt.

    Failure memory preserves:
    - what was being attempted
    - context
    - attempted action
    - failure/error
    - cause
    - recovery
    - lesson

    This layer records failure knowledge only.
    It does not execute recovery or grant authority.
    """

    failure_id: str
    task: str
    context: str
    attempted_action: str
    failure: str
    cause: str
    recovery: str
    lesson: str
    source: str
    severity: float = 0.5
    confidence: float = 0.5
    importance: float = 0.5
    provenance: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    occurred_at: datetime = field(default_factory=utc_now)
    recorded_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        for field_name in (
            "failure_id",
            "task",
            "context",
            "attempted_action",
            "failure",
            "cause",
            "recovery",
            "lesson",
            "source",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be non-empty")

        if not 0.0 <= self.severity <= 1.0:
            raise ValueError("severity must be between 0 and 1")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if not 0.0 <= self.importance <= 1.0:
            raise ValueError("importance must be between 0 and 1")

        if not isinstance(self.provenance, dict):
            raise TypeError("provenance must be a dictionary")

        if not isinstance(self.tags, list):
            raise TypeError("tags must be a list")


class FailureMemoryStore:
    """
    Bounded in-process failure memory.

    Stores failure experiences and supports retrieval by:
    - severity
    - tag
    - task/context/error/cause/lesson text

    Recovery is represented as knowledge only.
    This store never executes recovery actions.
    """

    def __init__(self, capacity: int = 256) -> None:
        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("capacity must be a positive integer")

        self._capacity = capacity
        self._failures: Dict[str, FailureMemory] = {}

    @staticmethod
    def _score(failure: FailureMemory) -> float:
        return (
            failure.severity * 0.40
            + failure.importance * 0.35
            + failure.confidence * 0.25
        )

    def store(self, failure: FailureMemory) -> FailureMemory:
        if not isinstance(failure, FailureMemory):
            raise TypeError("failure must be a FailureMemory")

        if failure.failure_id in self._failures:
            raise ValueError(
                f"failure memory already exists: {failure.failure_id}"
            )

        self._failures[failure.failure_id] = failure

        if len(self._failures) > self._capacity:
            oldest = min(
                self._failures.values(),
                key=lambda item: (
                    item.occurred_at,
                    item.recorded_at,
                    item.failure_id,
                ),
            )

            del self._failures[oldest.failure_id]

        return failure

    def get(self, failure_id: str) -> Optional[FailureMemory]:
        return self._failures.get(failure_id)

    def contains(self, failure_id: str) -> bool:
        return failure_id in self._failures

    def by_severity(
        self,
        minimum: float = 0.0,
    ) -> Tuple[FailureMemory, ...]:
        if not 0.0 <= minimum <= 1.0:
            raise ValueError("minimum must be between 0 and 1")

        matches = [
            failure
            for failure in self._failures.values()
            if failure.severity >= minimum
        ]

        return tuple(
            sorted(
                matches,
                key=lambda item: (
                    item.severity,
                    item.importance,
                    item.confidence,
                    item.occurred_at,
                ),
                reverse=True,
            )
        )

    def by_tag(self, tag: str) -> Tuple[FailureMemory, ...]:
        if not isinstance(tag, str):
            raise TypeError("tag must be a string")

        target = tag.strip().lower()

        matches = [
            failure
            for failure in self._failures.values()
            if any(
                existing.strip().lower() == target
                for existing in failure.tags
            )
        ]

        return tuple(
            sorted(
                matches,
                key=lambda item: (
                    self._score(item),
                    item.occurred_at,
                ),
                reverse=True,
            )
        )

    def search(self, text: str) -> Tuple[FailureMemory, ...]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        query = text.strip().lower()

        if not query:
            return tuple()

        matches = [
            failure
            for failure in self._failures.values()
            if (
                query in failure.task.lower()
                or query in failure.context.lower()
                or query in failure.attempted_action.lower()
                or query in failure.failure.lower()
                or query in failure.cause.lower()
                or query in failure.recovery.lower()
                or query in failure.lesson.lower()
                or any(query in tag.lower() for tag in failure.tags)
            )
        ]

        return tuple(
            sorted(
                matches,
                key=lambda item: (
                    self._score(item),
                    item.occurred_at,
                ),
                reverse=True,
            )
        )

    def lessons(self) -> Tuple[str, ...]:
        ordered = sorted(
            self._failures.values(),
            key=lambda item: (
                self._score(item),
                item.occurred_at,
            ),
            reverse=True,
        )

        return tuple(item.lesson for item in ordered)

    def recovery_knowledge(self) -> Tuple[str, ...]:
        ordered = sorted(
            self._failures.values(),
            key=lambda item: (
                self._score(item),
                item.occurred_at,
            ),
            reverse=True,
        )

        return tuple(item.recovery for item in ordered)

    def recent(self, limit: int = 10) -> Tuple[FailureMemory, ...]:
        if not isinstance(limit, int) or limit < 0:
            raise ValueError("limit must be a non-negative integer")

        ordered = sorted(
            self._failures.values(),
            key=lambda item: (
                item.occurred_at,
                item.recorded_at,
            ),
            reverse=True,
        )

        return tuple(ordered[:limit])

    def all(self) -> Tuple[FailureMemory, ...]:
        return tuple(
            sorted(
                self._failures.values(),
                key=lambda item: (
                    self._score(item),
                    item.occurred_at,
                ),
                reverse=True,
            )
        )

    def count(self) -> int:
        return len(self._failures)

    def remove(self, failure_id: str) -> Optional[FailureMemory]:
        return self._failures.pop(failure_id, None)

    def clear(self) -> None:
        self._failures.clear()

    def summary(self) -> Dict[str, Any]:
        return {
            "version": FAILURE_MEMORY_VERSION,
            "capacity": self._capacity,
            "failure_count": len(self._failures),
            "immutable_failure_objects": True,
            "preserves_context": True,
            "preserves_attempted_action": True,
            "preserves_failure": True,
            "preserves_cause": True,
            "preserves_recovery": True,
            "preserves_lesson": True,
            "preserves_provenance": True,
            "supports_severity_retrieval": True,
            "supports_failure_search": True,
            "supports_lesson_retrieval": True,
            "recovery_is_knowledge_only": True,
            "grants_permission": False,
            "executes_actions": False,
            "modifies_constitution": False,
        }
