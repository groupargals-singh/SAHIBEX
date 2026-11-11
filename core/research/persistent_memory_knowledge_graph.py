from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.research.knowledge_graph_storage import KnowledgeGraphStorage
from core.research.memory_association import MemoryAssociation
from core.research.memory_association_storage import MemoryAssociationStorage


PERSISTENT_MEMORY_KNOWLEDGE_GRAPH_VERSION = "P2-PMKG-1"

VALID_TARGET_TYPES = {
    "memory",
    "entity",
    "concept",
    "relationship",
    "knowledge",
    "source",
    "experience",
}


@dataclass(frozen=True)
class PersistentMemoryKnowledgeLinkResult:
    association: MemoryAssociation
    created: bool
    target_exists: bool


class PersistentMemoryKnowledgeGraph:
    """
    Persistent integration between Memory associations and the
    existing SAHIBEX Knowledge Graph.

    This layer stores links, not duplicated memory/knowledge content.

    It has:
    - no permission authority
    - no execution authority
    - no constitution authority
    - no automatic deletion
    - no modification of existing knowledge objects

    Knowledge-graph objects remain owned by their existing storage.
    This layer only creates persistent associative links.
    """

    def __init__(
        self,
        database_path: str,
    ) -> None:
        self.database_path = Path(database_path)
        self._association_storage = MemoryAssociationStorage(
            self.database_path
        )

        self._knowledge_storage = KnowledgeGraphStorage(
            self.database_path
        )

    @staticmethod
    def _validate_id(
        value: str,
        name: str,
    ) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{name} must be a non-empty string"
            )

    @staticmethod
    def _validate_target_type(
        target_type: str,
    ) -> None:
        if target_type not in VALID_TARGET_TYPES:
            raise ValueError(
                f"unsupported target type: {target_type}"
            )

    def _target_exists(
        self,
        target_id: str,
        target_type: str,
    ) -> bool:
        if target_type == "entity":
            return (
                self._knowledge_storage.get_entity(target_id)
                is not None
            )

        if target_type == "concept":
            return (
                self._knowledge_storage.get_concept(target_id)
                is not None
            )

        if target_type == "relationship":
            return (
                self._knowledge_storage.get_relationship(target_id)
                is not None
            )

        if target_type == "memory":
            return self._association_storage.memory_exists(target_id)

        # These objects are owned by other SAHIBEX
        # storage/registry layers. Their existence is not
        # silently inferred here.
        if target_type in {
            "knowledge",
            "source",
            "experience",
        }:
            return True

        return False

    @staticmethod
    def _association_type(
        target_type: str,
    ) -> str:
        mapping = {
            "memory": "memory_to_memory",
            "entity": "memory_to_entity",
            "concept": "memory_to_concept",
            "relationship": "memory_to_knowledge",
            "knowledge": "memory_to_knowledge",
            "source": "memory_to_source",
            "experience": "memory_to_experience",
        }

        return mapping[target_type]

    def link(
        self,
        memory_id: str,
        target_id: str,
        target_type: str,
        *,
        strength: float = 0.5,
        confidence: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> PersistentMemoryKnowledgeLinkResult:
        self._validate_id(memory_id, "memory_id")
        self._validate_id(target_id, "target_id")
        self._validate_target_type(target_type)

        association = MemoryAssociation(
            association_id=f"persistent-{memory_id}-{target_type}-{target_id}",
            source_memory_id=memory_id,
            target_id=target_id,
            target_type=target_type,
            association_type=self._association_type(
                target_type
            ),
            strength=strength,
            confidence=confidence,
            metadata=metadata or {},
        )

        existing = self._association_storage.get_association(
            source_memory_id=memory_id,
            target_id=target_id,
            target_type=target_type,
            association_type=association.association_type,
        )

        saved = self._association_storage.save_association(
            association
        )

        return PersistentMemoryKnowledgeLinkResult(
            association=saved,
            created=existing is None,
            target_exists=self._target_exists(
                target_id,
                target_type,
            ),
        )

    def links_for_memory(
        self,
        memory_id: str,
    ) -> tuple[MemoryAssociation, ...]:
        self._validate_id(memory_id, "memory_id")

        return self._association_storage.associations_for_memory(
            memory_id
        )

    def memories_for_target(
        self,
        target_id: str,
        target_type: str,
    ) -> tuple[str, ...]:
        self._validate_id(target_id, "target_id")
        self._validate_target_type(target_type)

        return self._association_storage.memories_for_target(
            target_id,
            target_type,
        )

    def association_count(self) -> int:
        return self._association_storage.association_count()

    def summary(self) -> dict[str, Any]:
        return {
            "version": (
                PERSISTENT_MEMORY_KNOWLEDGE_GRAPH_VERSION
            ),
            "association_count": self.association_count(),
            "persistent": True,
            "shared_sqlite_database": True,
            "knowledge_graph_connected": True,
            "stores_links_not_duplicate_content": True,
            "read_only_knowledge_objects": True,
            "grants_permission": False,
            "executes_actions": False,
            "modifies_constitution": False,
        }

    def close(self) -> None:
        self._association_storage.close()
        self._knowledge_storage.close()

    def __enter__(
        self,
    ) -> "PersistentMemoryKnowledgeGraph":
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()
