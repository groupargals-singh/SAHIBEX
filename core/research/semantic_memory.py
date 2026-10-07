from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


SEMANTIC_MEMORY_VERSION = "P2-SM-1"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class SemanticMemory:
    """
    Stable factual/conceptual knowledge represented as semantic memory.

    Semantic memory stores generalized meaning rather than a single episode.
    It is immutable and grants no authority to execute actions.
    """

    memory_id: str
    concept: str
    meaning: str
    source: str
    confidence: float = 0.5
    importance: float = 0.5
    provenance: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not isinstance(self.memory_id, str) or not self.memory_id.strip():
            raise ValueError("memory_id must be non-empty")

        if not isinstance(self.concept, str) or not self.concept.strip():
            raise ValueError("concept must be non-empty")

        if not isinstance(self.meaning, str) or not self.meaning.strip():
            raise ValueError("meaning must be non-empty")

        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source must be non-empty")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if not 0.0 <= self.importance <= 1.0:
            raise ValueError("importance must be between 0 and 1")

        if not isinstance(self.provenance, dict):
            raise TypeError("provenance must be a dictionary")

        if not isinstance(self.tags, list):
            raise TypeError("tags must be a list")


class SemanticMemoryStore:
    """
    Bounded in-process semantic memory store.

    This layer:
    - stores generalized concepts and meanings
    - supports deterministic retrieval
    - preserves provenance
    - provides no execution authority
    - provides no permission
    - cannot modify the Constitution
    """

    def __init__(self, capacity: int = 512) -> None:
        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("capacity must be a positive integer")

        self._capacity = capacity
        self._memories: Dict[str, SemanticMemory] = {}

    @property
    def capacity(self) -> int:
        return self._capacity

    def store(self, memory: SemanticMemory) -> SemanticMemory:
        if not isinstance(memory, SemanticMemory):
            raise TypeError("memory must be a SemanticMemory")

        if memory.memory_id in self._memories:
            raise ValueError(
                f"semantic memory already exists: {memory.memory_id}"
            )

        self._memories[memory.memory_id] = memory

        if len(self._memories) > self._capacity:
            oldest = min(
                self._memories.values(),
                key=lambda item: (
                    item.updated_at,
                    item.created_at,
                    item.memory_id,
                ),
            )
            del self._memories[oldest.memory_id]

        return memory

    def get(self, memory_id: str) -> Optional[SemanticMemory]:
        return self._memories.get(memory_id)

    def contains(self, memory_id: str) -> bool:
        return memory_id in self._memories

    def by_concept(self, concept: str) -> Tuple[SemanticMemory, ...]:
        if not isinstance(concept, str):
            raise TypeError("concept must be a string")

        target = concept.strip().lower()

        matches = [
            memory
            for memory in self._memories.values()
            if memory.concept.strip().lower() == target
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

    def by_tag(self, tag: str) -> Tuple[SemanticMemory, ...]:
        if not isinstance(tag, str):
            raise TypeError("tag must be a string")

        target = tag.strip().lower()

        matches = [
            memory
            for memory in self._memories.values()
            if any(existing.strip().lower() == target for existing in memory.tags)
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

    def search(self, text: str) -> Tuple[SemanticMemory, ...]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        query = text.strip().lower()

        if not query:
            return tuple()

        matches = [
            memory
            for memory in self._memories.values()
            if (
                query in memory.concept.lower()
                or query in memory.meaning.lower()
                or any(query in tag.lower() for tag in memory.tags)
            )
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

    def all(self) -> Tuple[SemanticMemory, ...]:
        return tuple(
            sorted(
                self._memories.values(),
                key=lambda item: (
                    item.importance,
                    item.confidence,
                    item.updated_at,
                ),
                reverse=True,
            )
        )

    def count(self) -> int:
        return len(self._memories)

    def remove(self, memory_id: str) -> Optional[SemanticMemory]:
        return self._memories.pop(memory_id, None)

    def clear(self) -> None:
        self._memories.clear()

    def summary(self) -> Dict[str, Any]:
        return {
            "version": SEMANTIC_MEMORY_VERSION,
            "capacity": self._capacity,
            "memory_count": len(self._memories),
            "immutable_memory_objects": True,
            "preserves_meaning": True,
            "preserves_provenance": True,
            "supports_concept_retrieval": True,
            "supports_tag_retrieval": True,
            "supports_text_search": True,
            "grants_permission": False,
            "executes_actions": False,
            "modifies_constitution": False,
        }
