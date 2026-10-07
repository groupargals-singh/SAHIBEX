from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from core.research.memory_object import MemoryCandidate


WORKING_MEMORY_VERSION = "P2-WM-1"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class WorkingMemoryEntry:
    memory: MemoryCandidate
    priority: float
    activated_at: datetime
    last_accessed_at: datetime
    access_count: int = 0

    def __post_init__(self) -> None:
        if not 0.0 <= self.priority <= 1.0:
            raise ValueError("priority must be between 0 and 1")

        if self.access_count < 0:
            raise ValueError("access_count cannot be negative")


class WorkingMemory:
    """
    Bounded active-memory layer for SAHIBEX.

    Working memory holds information currently relevant to
    reasoning, planning, attention, and active tasks.

    It is intentionally separate from long-term memory storage.

    Security boundary:
    - no permission authority
    - no action execution
    - no credential authority
    - no Constitution modification
    """

    def __init__(
        self,
        capacity: int = 32,
    ) -> None:
        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("capacity must be a positive integer")

        self.capacity = capacity
        self._entries: Dict[str, WorkingMemoryEntry] = {}

    @staticmethod
    def _validate_memory(
        memory: MemoryCandidate,
    ) -> None:
        if not isinstance(memory, MemoryCandidate):
            raise TypeError(
                "memory must be a MemoryCandidate"
            )

    @staticmethod
    def _score(
        entry: WorkingMemoryEntry,
    ) -> float:
        memory = entry.memory

        return (
            (entry.priority * 0.35)
            + (memory.importance * 0.25)
            + (memory.confidence * 0.20)
            + min(entry.access_count / 10.0, 1.0) * 0.10
            + 0.10
        )

    def activate(
        self,
        memory: MemoryCandidate,
        *,
        priority: float = 0.5,
    ) -> WorkingMemoryEntry:
        self._validate_memory(memory)

        if not 0.0 <= priority <= 1.0:
            raise ValueError(
                "priority must be between 0 and 1"
            )

        now = utc_now()

        existing = self._entries.get(memory.memory_id)

        if existing is not None:
            updated = WorkingMemoryEntry(
                memory=memory,
                priority=max(existing.priority, priority),
                activated_at=existing.activated_at,
                last_accessed_at=now,
                access_count=existing.access_count + 1,
            )

            self._entries[memory.memory_id] = updated
            return updated

        entry = WorkingMemoryEntry(
            memory=memory,
            priority=priority,
            activated_at=now,
            last_accessed_at=now,
            access_count=1,
        )

        self._entries[memory.memory_id] = entry

        self._enforce_capacity()

        return self._entries.get(
            memory.memory_id,
            entry,
        )

    def get(
        self,
        memory_id: str,
    ) -> Optional[WorkingMemoryEntry]:
        if not isinstance(memory_id, str) or not memory_id.strip():
            raise ValueError(
                "memory_id must be a non-empty string"
            )

        entry = self._entries.get(memory_id)

        if entry is None:
            return None

        updated = WorkingMemoryEntry(
            memory=entry.memory,
            priority=entry.priority,
            activated_at=entry.activated_at,
            last_accessed_at=utc_now(),
            access_count=entry.access_count + 1,
        )

        self._entries[memory_id] = updated

        return updated

    def remove(
        self,
        memory_id: str,
    ) -> bool:
        if not isinstance(memory_id, str) or not memory_id.strip():
            raise ValueError(
                "memory_id must be a non-empty string"
            )

        return self._entries.pop(
            memory_id,
            None,
        ) is not None

    def contains(
        self,
        memory_id: str,
    ) -> bool:
        return memory_id in self._entries

    def active_memories(self) -> tuple[MemoryCandidate, ...]:
        entries = sorted(
            self._entries.values(),
            key=self._score,
            reverse=True,
        )

        return tuple(
            entry.memory
            for entry in entries
        )

    def entries(self) -> tuple[WorkingMemoryEntry, ...]:
        return tuple(
            sorted(
                self._entries.values(),
                key=self._score,
                reverse=True,
            )
        )

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()

    def _enforce_capacity(self) -> None:
        while len(self._entries) > self.capacity:
            lowest = min(
                self._entries.values(),
                key=self._score,
            )

            self._entries.pop(
                lowest.memory.memory_id,
                None,
            )

    def promote_candidates(self) -> tuple[MemoryCandidate, ...]:
        """
        Returns currently strong working-memory candidates
        that may be promoted to long-term memory.

        This method proposes candidates only.
        It does not write to long-term storage.
        """

        return tuple(
            entry.memory
            for entry in self.entries()
            if (
                entry.priority >= 0.70
                and entry.memory.importance >= 0.60
                and entry.memory.confidence >= 0.60
            )
        )

    def summary(self) -> dict:
        return {
            "version": WORKING_MEMORY_VERSION,
            "capacity": self.capacity,
            "active_count": self.count(),
            "bounded": True,
            "long_term_storage": False,
            "promotion_is_proposal_only": True,
            "grants_permission": False,
            "executes_actions": False,
            "modifies_constitution": False,
        }
