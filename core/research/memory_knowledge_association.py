from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from core.research.memory_association import (
    MemoryAssociation,
    MemoryAssociationEngine,
    VALID_ASSOCIATION_TYPES,
)

MEMORY_KNOWLEDGE_ASSOCIATION_VERSION = "P2-MK-1"

MEMORY_KNOWLEDGE_TARGET_TYPES = {
    "memory",
    "entity",
    "concept",
    "event",
    "knowledge",
    "source",
    "experience",
}


@dataclass(frozen=True)
class MemoryKnowledgeAssociationResult:
    association: MemoryAssociation
    created: bool


class MemoryKnowledgeAssociation:
    """
    Read-only orchestration layer between Memory and the
    associative graph.

    This layer creates references/links only.
    It does not duplicate memory or knowledge content.
    It has no execution or permission authority.
    """

    def __init__(
        self,
        engine: MemoryAssociationEngine | None = None,
    ) -> None:
        self._engine = engine or MemoryAssociationEngine()

    @staticmethod
    def _validate_id(value: str, name: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")

    @staticmethod
    def _validate_target_type(target_type: str) -> None:
        if target_type not in MEMORY_KNOWLEDGE_TARGET_TYPES:
            raise ValueError(
                f"unsupported target type: {target_type}"
            )

    def link(
        self,
        memory_id: str,
        target_id: str,
        target_type: str,
        association_type: str | None = None,
        *,
        strength: float = 0.5,
        confidence: float = 0.5,
        metadata: Dict[str, Any] | None = None,
    ) -> MemoryKnowledgeAssociationResult:
        self._validate_id(memory_id, "memory_id")
        self._validate_id(target_id, "target_id")
        self._validate_target_type(target_type)

        if association_type is None:
            if target_type == "memory":
                association_type = "memory_to_memory"
            elif target_type == "entity":
                association_type = "memory_to_entity"
            elif target_type == "concept":
                association_type = "memory_to_concept"
            elif target_type == "event":
                association_type = "memory_to_event"
            elif target_type == "knowledge":
                association_type = "memory_to_knowledge"
            elif target_type == "source":
                association_type = "memory_to_source"
            elif target_type == "experience":
                association_type = "memory_to_experience"

        if association_type not in VALID_ASSOCIATION_TYPES:
            raise ValueError(
                f"unsupported association type: {association_type}"
            )

        before = self._engine.association_count()

        association = self._engine.associate(
            source_memory_id=memory_id,
            target_id=target_id,
            target_type=target_type,
            association_type=association_type,
            strength=strength,
            confidence=confidence,
            metadata=metadata,
        )

        after = self._engine.association_count()

        return MemoryKnowledgeAssociationResult(
            association=association,
            created=after > before,
        )

    def links_for_memory(
        self,
        memory_id: str,
    ) -> tuple[MemoryAssociation, ...]:
        self._validate_id(memory_id, "memory_id")
        return self._engine.associations_for_memory(memory_id)

    def memories_for_target(
        self,
        target_id: str,
        target_type: str,
    ) -> tuple[str, ...]:
        self._validate_id(target_id, "target_id")
        self._validate_target_type(target_type)
        return self._engine.memories_for_target(
            target_id,
            target_type,
        )

    def association_count(self) -> int:
        return self._engine.association_count()

    def summary(self) -> dict[str, Any]:
        return {
            "version": MEMORY_KNOWLEDGE_ASSOCIATION_VERSION,
            "association_count": self.association_count(),
            "link_based": True,
            "duplicates_memory_content": False,
            "read_only": True,
            "grants_permission": False,
            "executes_actions": False,
            "modifies_constitution": False,
        }
