from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any
from uuid import uuid4


MEMORY_ASSOCIATION_VERSION = "P2-ASSOC-1"

VALID_ASSOCIATION_TYPES = {
    "memory_to_memory",
    "memory_to_entity",
    "memory_to_concept",
    "memory_to_event",
    "memory_to_knowledge",
    "memory_to_source",
    "memory_to_experience",
}


@dataclass(frozen=True)
class MemoryAssociation:
    """
    Directed associative connection between a memory and another
    memory/knowledge-world object.

    This is an association model only.
    It does not execute actions, grant permissions, or modify
    constitutional authority.
    """

    association_id: str
    source_memory_id: str
    target_id: str
    target_type: str
    association_type: str
    strength: float = 0.5
    confidence: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.association_id.strip():
            raise ValueError("association_id cannot be empty")

        if not self.source_memory_id.strip():
            raise ValueError("source_memory_id cannot be empty")

        if not self.target_id.strip():
            raise ValueError("target_id cannot be empty")

        if self.association_type not in VALID_ASSOCIATION_TYPES:
            raise ValueError(
                f"invalid association_type: {self.association_type}"
            )

        if not self.target_type.strip():
            raise ValueError("target_type cannot be empty")

        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("strength must be between 0 and 1")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")


class MemoryAssociationEngine:
    """
    In-memory associative layer.

    Design goal:
    reuse shared identities and relationships instead of
    duplicating complete memory content.

    This layer does not persist data yet.
    """

    def __init__(self) -> None:
        self._associations: dict[
            tuple[str, str, str, str],
            MemoryAssociation,
        ] = {}

    def associate(
        self,
        source_memory_id: str,
        target_id: str,
        target_type: str,
        association_type: str,
        *,
        strength: float = 0.5,
        confidence: float = 0.5,
        metadata: Dict[str, Any] | None = None,
    ) -> MemoryAssociation:
        association = MemoryAssociation(
            association_id=str(uuid4()),
            source_memory_id=source_memory_id,
            target_id=target_id,
            target_type=target_type,
            association_type=association_type,
            strength=strength,
            confidence=confidence,
            metadata={} if metadata is None else dict(metadata),
        )

        key = (
            source_memory_id,
            target_type,
            target_id,
            association_type,
        )

        existing = self._associations.get(key)

        if existing is not None:
            return existing

        self._associations[key] = association
        return association

    def associations_for_memory(
        self,
        memory_id: str,
    ) -> tuple[MemoryAssociation, ...]:
        if not memory_id.strip():
            raise ValueError("memory_id cannot be empty")

        return tuple(
            association
            for association in self._associations.values()
            if association.source_memory_id == memory_id
        )

    def memories_for_target(
        self,
        target_id: str,
        target_type: str,
    ) -> tuple[str, ...]:
        if not target_id.strip():
            raise ValueError("target_id cannot be empty")

        return tuple(
            association.source_memory_id
            for association in self._associations.values()
            if (
                association.target_id == target_id
                and association.target_type == target_type
            )
        )

    def association_count(self) -> int:
        return len(self._associations)

    def clear(self) -> None:
        self._associations.clear()

    def summary(self) -> dict[str, object]:
        return {
            "association_count": self.association_count(),
            "version": MEMORY_ASSOCIATION_VERSION,
            "read_only": True,
            "grants_permission": False,
            "executes_actions": False,
            "modifies_constitution": False,
        }
