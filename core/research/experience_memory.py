from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


EXPERIENCE_MEMORY_VERSION = "P2-EX-1"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ExperienceMemory:
    """
    Learned experience from a completed or attempted interaction/task.

    Experience memory connects context, action, outcome and lesson.
    It stores experience only; it does not execute actions.
    """

    experience_id: str
    task: str
    context: str
    action_taken: str
    outcome: str
    lesson: str
    source: str
    success: bool
    confidence: float = 0.5
    importance: float = 0.5
    provenance: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    occurred_at: datetime = field(default_factory=utc_now)
    recorded_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        for field_name in (
            "experience_id",
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

        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if not 0.0 <= self.importance <= 1.0:
            raise ValueError("importance must be between 0 and 1")

        if not isinstance(self.provenance, dict):
            raise TypeError("provenance must be a dictionary")

        if not isinstance(self.tags, list):
            raise TypeError("tags must be a list")


class ExperienceMemoryStore:
    """
    Bounded in-process experience memory.

    Supports experience retrieval, outcome filtering and lesson search.
    It provides no execution authority and no permission.
    """

    def __init__(self, capacity: int = 256) -> None:
        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("capacity must be a positive integer")

        self._capacity = capacity
        self._experiences: Dict[str, ExperienceMemory] = {}

    @staticmethod
    def _score(experience: ExperienceMemory) -> float:
        outcome_value = 1.0 if experience.success else 0.0

        return (
            experience.importance * 0.35
            + experience.confidence * 0.35
            + outcome_value * 0.30
        )

    def store(self, experience: ExperienceMemory) -> ExperienceMemory:
        if not isinstance(experience, ExperienceMemory):
            raise TypeError("experience must be an ExperienceMemory")

        if experience.experience_id in self._experiences:
            raise ValueError(
                f"experience already exists: {experience.experience_id}"
            )

        self._experiences[experience.experience_id] = experience

        if len(self._experiences) > self._capacity:
            oldest = min(
                self._experiences.values(),
                key=lambda item: (
                    item.occurred_at,
                    item.recorded_at,
                    item.experience_id,
                ),
            )
            del self._experiences[oldest.experience_id]

        return experience

    def get(self, experience_id: str) -> Optional[ExperienceMemory]:
        return self._experiences.get(experience_id)

    def contains(self, experience_id: str) -> bool:
        return experience_id in self._experiences

    def successful(self) -> Tuple[ExperienceMemory, ...]:
        matches = [
            experience
            for experience in self._experiences.values()
            if experience.success
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

    def failed(self) -> Tuple[ExperienceMemory, ...]:
        matches = [
            experience
            for experience in self._experiences.values()
            if not experience.success
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

    def by_tag(self, tag: str) -> Tuple[ExperienceMemory, ...]:
        if not isinstance(tag, str):
            raise TypeError("tag must be a string")

        target = tag.strip().lower()

        matches = [
            experience
            for experience in self._experiences.values()
            if any(existing.strip().lower() == target for existing in experience.tags)
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

    def search(self, text: str) -> Tuple[ExperienceMemory, ...]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        query = text.strip().lower()

        if not query:
            return tuple()

        matches = [
            experience
            for experience in self._experiences.values()
            if (
                query in experience.task.lower()
                or query in experience.context.lower()
                or query in experience.action_taken.lower()
                or query in experience.outcome.lower()
                or query in experience.lesson.lower()
                or any(query in tag.lower() for tag in experience.tags)
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

    def recent(self, limit: int = 10) -> Tuple[ExperienceMemory, ...]:
        if not isinstance(limit, int) or limit < 0:
            raise ValueError("limit must be a non-negative integer")

        ordered = sorted(
            self._experiences.values(),
            key=lambda item: (
                item.occurred_at,
                item.recorded_at,
            ),
            reverse=True,
        )

        return tuple(ordered[:limit])

    def lessons(self) -> Tuple[str, ...]:
        ordered = sorted(
            self._experiences.values(),
            key=lambda item: (
                self._score(item),
                item.occurred_at,
            ),
            reverse=True,
        )

        return tuple(item.lesson for item in ordered)

    def all(self) -> Tuple[ExperienceMemory, ...]:
        return tuple(
            sorted(
                self._experiences.values(),
                key=lambda item: (
                    self._score(item),
                    item.occurred_at,
                ),
                reverse=True,
            )
        )

    def count(self) -> int:
        return len(self._experiences)

    def remove(self, experience_id: str) -> Optional[ExperienceMemory]:
        return self._experiences.pop(experience_id, None)

    def clear(self) -> None:
        self._experiences.clear()

    def summary(self) -> Dict[str, Any]:
        return {
            "version": EXPERIENCE_MEMORY_VERSION,
            "capacity": self._capacity,
            "experience_count": len(self._experiences),
            "immutable_experience_objects": True,
            "preserves_context": True,
            "preserves_action_record": True,
            "preserves_outcome": True,
            "preserves_lesson": True,
            "preserves_provenance": True,
            "supports_success_failure_retrieval": True,
            "supports_lesson_retrieval": True,
            "supports_experience_search": True,
            "grants_permission": False,
            "executes_actions": False,
            "modifies_constitution": False,
        }
