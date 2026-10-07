from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


PROCEDURAL_MEMORY_VERSION = "P2-PM-1"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ProceduralMemory:
    """
    Learned procedural knowledge: how a task or skill is performed.

    This layer stores procedures only.
    It does not execute procedures and does not grant authority.
    """

    procedure_id: str
    name: str
    purpose: str
    steps: Tuple[str, ...]
    source: str
    confidence: float = 0.5
    importance: float = 0.5
    success_count: int = 0
    failure_count: int = 0
    provenance: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not isinstance(self.procedure_id, str) or not self.procedure_id.strip():
            raise ValueError("procedure_id must be non-empty")

        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be non-empty")

        if not isinstance(self.purpose, str) or not self.purpose.strip():
            raise ValueError("purpose must be non-empty")

        if not isinstance(self.steps, tuple):
            raise TypeError("steps must be a tuple")

        if not self.steps:
            raise ValueError("steps must contain at least one step")

        if any(
            not isinstance(step, str) or not step.strip()
            for step in self.steps
        ):
            raise ValueError("every step must be a non-empty string")

        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source must be non-empty")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if not 0.0 <= self.importance <= 1.0:
            raise ValueError("importance must be between 0 and 1")

        if not isinstance(self.success_count, int) or self.success_count < 0:
            raise ValueError("success_count must be a non-negative integer")

        if not isinstance(self.failure_count, int) or self.failure_count < 0:
            raise ValueError("failure_count must be a non-negative integer")

        if not isinstance(self.provenance, dict):
            raise TypeError("provenance must be a dictionary")

        if not isinstance(self.tags, list):
            raise TypeError("tags must be a list")


class ProceduralMemoryStore:
    """
    Bounded in-process procedural memory.

    Stores learned procedures and supports retrieval/ranking.
    It does not execute steps or grant permissions.
    """

    def __init__(self, capacity: int = 256) -> None:
        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("capacity must be a positive integer")

        self._capacity = capacity
        self._procedures: Dict[str, ProceduralMemory] = {}

    @staticmethod
    def _score(procedure: ProceduralMemory) -> float:
        total = procedure.success_count + procedure.failure_count

        success_rate = (
            procedure.success_count / total
            if total > 0
            else procedure.confidence
        )

        return (
            procedure.importance * 0.35
            + procedure.confidence * 0.30
            + success_rate * 0.35
        )

    def store(self, procedure: ProceduralMemory) -> ProceduralMemory:
        if not isinstance(procedure, ProceduralMemory):
            raise TypeError("procedure must be a ProceduralMemory")

        if procedure.procedure_id in self._procedures:
            raise ValueError(
                f"procedural memory already exists: {procedure.procedure_id}"
            )

        self._procedures[procedure.procedure_id] = procedure

        if len(self._procedures) > self._capacity:
            oldest = min(
                self._procedures.values(),
                key=lambda item: (
                    item.updated_at,
                    item.created_at,
                    item.procedure_id,
                ),
            )
            del self._procedures[oldest.procedure_id]

        return procedure

    def get(self, procedure_id: str) -> Optional[ProceduralMemory]:
        return self._procedures.get(procedure_id)

    def contains(self, procedure_id: str) -> bool:
        return procedure_id in self._procedures

    def by_name(self, name: str) -> Tuple[ProceduralMemory, ...]:
        if not isinstance(name, str):
            raise TypeError("name must be a string")

        target = name.strip().lower()

        matches = [
            procedure
            for procedure in self._procedures.values()
            if procedure.name.strip().lower() == target
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

    def by_tag(self, tag: str) -> Tuple[ProceduralMemory, ...]:
        if not isinstance(tag, str):
            raise TypeError("tag must be a string")

        target = tag.strip().lower()

        matches = [
            procedure
            for procedure in self._procedures.values()
            if any(existing.strip().lower() == target for existing in procedure.tags)
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

    def search(self, text: str) -> Tuple[ProceduralMemory, ...]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        query = text.strip().lower()

        if not query:
            return tuple()

        matches = [
            procedure
            for procedure in self._procedures.values()
            if (
                query in procedure.name.lower()
                or query in procedure.purpose.lower()
                or any(query in step.lower() for step in procedure.steps)
                or any(query in tag.lower() for tag in procedure.tags)
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

    def successful(self) -> Tuple[ProceduralMemory, ...]:
        matches = [
            procedure
            for procedure in self._procedures.values()
            if procedure.success_count > procedure.failure_count
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

    def all(self) -> Tuple[ProceduralMemory, ...]:
        return tuple(
            sorted(
                self._procedures.values(),
                key=lambda item: (
                    self._score(item),
                    item.updated_at,
                ),
                reverse=True,
            )
        )

    def count(self) -> int:
        return len(self._procedures)

    def remove(self, procedure_id: str) -> Optional[ProceduralMemory]:
        return self._procedures.pop(procedure_id, None)

    def clear(self) -> None:
        self._procedures.clear()

    def summary(self) -> Dict[str, Any]:
        return {
            "version": PROCEDURAL_MEMORY_VERSION,
            "capacity": self._capacity,
            "procedure_count": len(self._procedures),
            "immutable_procedure_objects": True,
            "preserves_steps": True,
            "preserves_provenance": True,
            "tracks_success_failure": True,
            "supports_procedure_retrieval": True,
            "supports_tag_retrieval": True,
            "supports_procedure_search": True,
            "execution_authority": False,
            "grants_permission": False,
            "executes_actions": False,
            "modifies_constitution": False,
        }
