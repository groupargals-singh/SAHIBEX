from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

from .memory_object import MemoryCandidate


@dataclass(frozen=True)
class MemoryRegistration:
    """
    Result of registering a memory.

    If is_new is False, the existing memory was already registered
    and is returned without replacing it.
    """

    memory: MemoryCandidate
    is_new: bool


class MemoryRegistry:
    """
    In-memory registry for SAHIBEX memories.

    Responsibilities:
    - Register memories.
    - Prevent duplicate memory identities.
    - Retrieve memories by ID.
    - Require an existing memory.
    - Check memory existence.
    - Enumerate registered memories.
    - Provide counts and summaries.

    Persistence, retrieval ranking, lifecycle management,
    consolidation, and conflict handling are intentionally
    outside this component.
    """

    def __init__(self) -> None:
        self._memories: Dict[str, MemoryCandidate] = {}

    def register(self, memory: MemoryCandidate) -> MemoryRegistration:
        if not isinstance(memory, MemoryCandidate):
            raise TypeError("memory must be a MemoryCandidate")

        existing = self._memories.get(memory.memory_id)

        if existing is not None:
            return MemoryRegistration(
                memory=existing,
                is_new=False,
            )

        self._memories[memory.memory_id] = memory

        return MemoryRegistration(
            memory=memory,
            is_new=True,
        )

    def get(self, memory_id: str) -> MemoryCandidate | None:
        return self._memories.get(memory_id)

    def require(self, memory_id: str) -> MemoryCandidate:
        memory = self.get(memory_id)

        if memory is None:
            raise KeyError(f"Unknown memory: {memory_id}")

        return memory

    def contains(self, memory_id: str) -> bool:
        return memory_id in self._memories

    def all(self) -> Iterable[MemoryCandidate]:
        return tuple(self._memories.values())

    def count(self) -> int:
        return len(self._memories)

    def clear(self) -> None:
        self._memories.clear()

    def summary(self) -> dict:
        return {
            "memory_count": self.count(),
        }
