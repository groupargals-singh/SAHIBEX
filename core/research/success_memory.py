from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


SUCCESS_MEMORY_VERSION = "P2-SC-1"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class SuccessMemory:
    """
    Structured memory of a successful task or outcome.

    Preserves:
    - task
    - context/conditions
    - effective action
    - successful outcome
    - reusable lesson

    This layer stores success knowledge only.
    It does not execute actions or grant authority.
    """

    success_id: str
    task: str
    context: str
    action_taken: str
    outcome: str
    lesson: str
    source: str
    confidence: float = 0.5
    importance: float = 0.5
    effectiveness: float = 0.5
    provenance: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    occurred_at: datetime = field(default_factory=utc_now)
    recorded_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        for field_name in (
            "success_id",
            "task",
            "context",
            "action_taken",
            "outcome",
            "lesson",
            "source",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be non-empty")

        for field_name in (
            "confidence",
            "importance",
            "effectiveness",
        ):
            value = getattr(self, field_name)

            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0 and 1")

        if not isinstance(self.provenance, dict):
            raise TypeError("provenance must be a dictionary")

        if not isinstance(self.tags, list):
            raise TypeError("tags must be a list")


class SuccessMemoryStore:
    """
    Bounded in-process success memory.

    Supports retrieval and ranking of successful experiences.
    It does not execute actions and does not grant permissions.
    """

    def __init__(self, capacity: int = 256) -> None:
        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("capacity must be a positive integer")

        self._capacity = capacity
        self._successes: Dict[str, SuccessMemory] = {}

    @staticmethod
    def _score(success: SuccessMemory) -> float:
        return (
            success.effectiveness * 0.40
            + success.importance * 0.30
            + success.confidence * 0.30
        )

    def store(self, success: SuccessMemory) -> SuccessMemory:
        if not isinstance(success, SuccessMemory):
            raise TypeError("success must be a SuccessMemory")

        if success.success_id in self._successes:
            raise ValueError(
                f"success memory already exists: {success.success_id}"
            )

        self._successes[success.success_id] = success

        if len(self._successes) > self._capacity:
            oldest = min(
                self._successes.values(),
                key=lambda item: (
                    item.occurred_at,
                    item.recorded_at,
                    item.success_id,
                ),
            )

            del self._successes[oldest.success_id]

        return success

    def get(self, success_id: str) -> Optional[SuccessMemory]:
        return self._successes.get(success_id)

    def contains(self, success_id: str) -> bool:
        return success_id in self._successes

    def by_effectiveness(
        self,
        minimum: float = 0.0,
    ) -> Tuple[SuccessMemory, ...]:
        if not 0.0 <= minimum <= 1.0:
            raise ValueError("minimum must be between 0 and 1")

        matches = [
            success
            for success in self._successes.values()
            if success.effectiveness >= minimum
        ]

        return tuple(
            sorted(
                matches,
                key=lambda item: (
                    item.effectiveness,
                    item.importance,
                    item.confidence,
                    item.occurred_at,
                ),
                reverse=True,
            )
        )

    def by_tag(self, tag: str) -> Tuple[SuccessMemory, ...]:
        if not isinstance(tag, str):
            raise TypeError("tag must be a string")

        target = tag.strip().lower()

        matches = [
            success
            for success in self._successes.values()
            if any(
                existing.strip().lower() == target
                for existing in success.tags
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

    def search(self, text: str) -> Tuple[SuccessMemory, ...]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        query = text.strip().lower()

        if not query:
            return tuple()

        matches = [
            success
            for success in self._successes.values()
            if (
                query in success.task.lower()
                or query in success.context.lower()
                or query in success.action_taken.lower()
                or query in success.outcome.lower()
                or query in success.lesson.lower()
                or any(query in tag.lower() for tag in success.tags)
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
            self._successes.values(),
            key=lambda item: (
                self._score(item),
                item.occurred_at,
            ),
            reverse=True,
        )

        return tuple(item.lesson for item in ordered)

    def effective_actions(self) -> Tuple[str, ...]:
        ordered = sorted(
            self._successes.values(),
            key=lambda item: (
                self._score(item),
                item.occurred_at,
            ),
            reverse=True,
        )

        return tuple(item.action_taken for item in ordered)

    def recent(self, limit: int = 10) -> Tuple[SuccessMemory, ...]:
        if not isinstance(limit, int) or limit < 0:
            raise ValueError("limit must be a non-negative integer")

        ordered = sorted(
            self._successes.values(),
            key=lambda item: (
                item.occurred_at,
                item.recorded_at,
            ),
            reverse=True,
        )

        return tuple(ordered[:limit])

    def all(self) -> Tuple[SuccessMemory, ...]:
        return tuple(
            sorted(
                self._successes.values(),
                key=lambda item: (
                    self._score(item),
                    item.occurred_at,
                ),
                reverse=True,
            )
        )

    def count(self) -> int:
        return len(self._successes)

    def remove(self, success_id: str) -> Optional[SuccessMemory]:
        return self._successes.pop(success_id, None)

    def clear(self) -> None:
        self._successes.clear()

    def summary(self) -> Dict[str, Any]:
        return {
            "version": SUCCESS_MEMORY_VERSION,
            "capacity": self._capacity,
            "success_count": len(self._successes),
            "immutable_success_objects": True,
            "preserves_context": True,
            "preserves_action_record": True,
            "preserves_outcome": True,
            "preserves_lesson": True,
            "preserves_provenance": True,
            "tracks_effectiveness": True,
            "supports_effectiveness_retrieval": True,
            "supports_success_search": True,
            "supports_lesson_retrieval": True,
            "supports_effective_action_retrieval": True,
            "execution_authority": False,
            "grants_permission": False,
            "executes_actions": False,
            "modifies_constitution": False,
        }
