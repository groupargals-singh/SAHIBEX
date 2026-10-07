from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


USER_CONTEXT_MEMORY_VERSION = "P2-UCM-1"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class UserContextMemory:
    """
    Structured memory for reusable user-context information.

    Examples:
    - preferences
    - workflow habits
    - recurring constraints
    - project context
    - interaction context

    This memory is informational only.
    It does not grant authority or permissions.
    """

    context_id: str
    context_type: str
    subject: str
    value: str
    context: str
    source: str
    confidence: float = 0.5
    importance: float = 0.5
    provenance: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        for field_name in (
            "context_id",
            "context_type",
            "subject",
            "value",
            "context",
            "source",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be non-empty")

        for field_name in ("confidence", "importance"):
            value = getattr(self, field_name)

            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0 and 1")

        if not isinstance(self.provenance, dict):
            raise TypeError("provenance must be a dictionary")

        if not isinstance(self.tags, list):
            raise TypeError("tags must be a list")


class UserContextMemoryStore:
    """
    Bounded in-process user-context memory.

    Stores contextual information only.
    No execution, permission, or constitutional authority.
    """

    def __init__(self, capacity: int = 256) -> None:
        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("capacity must be a positive integer")

        self._capacity = capacity
        self._contexts: Dict[str, UserContextMemory] = {}

    @staticmethod
    def _score(item: UserContextMemory) -> float:
        return (
            item.importance * 0.55
            + item.confidence * 0.45
        )

    def store(self, item: UserContextMemory) -> UserContextMemory:
        if not isinstance(item, UserContextMemory):
            raise TypeError("item must be a UserContextMemory")

        if item.context_id in self._contexts:
            raise ValueError(
                f"user context already exists: {item.context_id}"
            )

        self._contexts[item.context_id] = item

        if len(self._contexts) > self._capacity:
            oldest = min(
                self._contexts.values(),
                key=lambda entry: (
                    entry.updated_at,
                    entry.created_at,
                    entry.context_id,
                ),
            )

            del self._contexts[oldest.context_id]

        return item

    def get(self, context_id: str) -> Optional[UserContextMemory]:
        return self._contexts.get(context_id)

    def contains(self, context_id: str) -> bool:
        return context_id in self._contexts

    def by_type(self, context_type: str) -> Tuple[UserContextMemory, ...]:
        if not isinstance(context_type, str):
            raise TypeError("context_type must be a string")

        target = context_type.strip().lower()

        matches = [
            item
            for item in self._contexts.values()
            if item.context_type.strip().lower() == target
        ]

        return tuple(
            sorted(
                matches,
                key=lambda item: (
                    self._score(item),
                    item.updated_at,
                ),
                reverse=True,
            )
        )

    def by_subject(self, subject: str) -> Tuple[UserContextMemory, ...]:
        if not isinstance(subject, str):
            raise TypeError("subject must be a string")

        target = subject.strip().lower()

        matches = [
            item
            for item in self._contexts.values()
            if item.subject.strip().lower() == target
        ]

        return tuple(
            sorted(
                matches,
                key=lambda item: (
                    self._score(item),
                    item.updated_at,
                ),
                reverse=True,
            )
        )

    def by_tag(self, tag: str) -> Tuple[UserContextMemory, ...]:
        if not isinstance(tag, str):
            raise TypeError("tag must be a string")

        target = tag.strip().lower()

        matches = [
            item
            for item in self._contexts.values()
            if any(
                existing.strip().lower() == target
                for existing in item.tags
            )
        ]

        return tuple(
            sorted(
                matches,
                key=lambda item: (
                    self._score(item),
                    item.updated_at,
                ),
                reverse=True,
            )
        )

    def search(self, text: str) -> Tuple[UserContextMemory, ...]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        query = text.strip().lower()

        if not query:
            return tuple()

        matches = [
            item
            for item in self._contexts.values()
            if (
                query in item.context_type.lower()
                or query in item.subject.lower()
                or query in item.value.lower()
                or query in item.context.lower()
                or query in item.source.lower()
                or any(query in tag.lower() for tag in item.tags)
            )
        ]

        return tuple(
            sorted(
                matches,
                key=lambda item: (
                    self._score(item),
                    item.updated_at,
                ),
                reverse=True,
            )
        )

    def important(self, minimum: float = 0.0) -> Tuple[UserContextMemory, ...]:
        if not 0.0 <= minimum <= 1.0:
            raise ValueError("minimum must be between 0 and 1")

        matches = [
            item
            for item in self._contexts.values()
            if item.importance >= minimum
        ]

        return tuple(
            sorted(
                matches,
                key=lambda item: (
                    item.importance,
                    item.confidence,
                    item.updated_at,
                ),
                reverse=True,
            )
        )

    def recent(self, limit: int = 10) -> Tuple[UserContextMemory, ...]:
        if not isinstance(limit, int) or limit < 0:
            raise ValueError("limit must be a non-negative integer")

        ordered = sorted(
            self._contexts.values(),
            key=lambda item: (
                item.updated_at,
                item.created_at,
            ),
            reverse=True,
        )

        return tuple(ordered[:limit])

    def all(self) -> Tuple[UserContextMemory, ...]:
        return tuple(
            sorted(
                self._contexts.values(),
                key=lambda item: (
                    self._score(item),
                    item.updated_at,
                ),
                reverse=True,
            )
        )

    def count(self) -> int:
        return len(self._contexts)

    def remove(self, context_id: str) -> Optional[UserContextMemory]:
        return self._contexts.pop(context_id, None)

    def clear(self) -> None:
        self._contexts.clear()

    def summary(self) -> Dict[str, Any]:
        return {
            "version": USER_CONTEXT_MEMORY_VERSION,
            "capacity": self._capacity,
            "context_count": len(self._contexts),
            "immutable_context_objects": True,
            "supports_type_retrieval": True,
            "supports_subject_retrieval": True,
            "supports_tag_retrieval": True,
            "supports_context_search": True,
            "supports_importance_retrieval": True,
            "supports_recent_retrieval": True,
            "execution_authority": False,
            "grants_permission": False,
            "executes_actions": False,
            "modifies_constitution": False,
        }
