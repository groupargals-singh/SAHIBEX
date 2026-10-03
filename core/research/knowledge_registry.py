from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

from core.research.models import KnowledgeCandidate


@dataclass(frozen=True)
class Entity:
    """
    An identifiable real-world or system-level entity.
    """

    entity_id: str
    name: str
    entity_type: str

    def __post_init__(self) -> None:
        if not self.entity_id.strip():
            raise ValueError("entity_id cannot be empty")

        if not self.name.strip():
            raise ValueError("entity name cannot be empty")

        if not self.entity_type.strip():
            raise ValueError("entity_type cannot be empty")


@dataclass(frozen=True)
class Concept:
    """
    An abstract concept, topic, idea, or domain term.
    """

    concept_id: str
    name: str
    concept_type: str

    def __post_init__(self) -> None:
        if not self.concept_id.strip():
            raise ValueError("concept_id cannot be empty")

        if not self.name.strip():
            raise ValueError("concept name cannot be empty")

        if not self.concept_type.strip():
            raise ValueError("concept_type cannot be empty")


@dataclass(frozen=True)
class EntityRegistration:
    entity: Entity
    is_new: bool


@dataclass(frozen=True)
class ConceptRegistration:
    concept: Concept
    is_new: bool


class KnowledgeRegistry:
    """
    In-memory registry for knowledge entities and concepts.

    Responsibilities:
    - Register entities.
    - Register concepts.
    - Prevent duplicate identities.
    - Retrieve entities and concepts by ID.
    - Provide registry counts and summaries.

    Relationship modeling, persistence, and knowledge linking
    are intentionally outside this component.
    """

    def __init__(self) -> None:
        self._entities: Dict[str, Entity] = {}
        self._concepts: Dict[str, Concept] = {}

    def register_entity(
        self,
        entity: Entity,
    ) -> EntityRegistration:
        if not isinstance(entity, Entity):
            raise TypeError("entity must be an Entity")

        existing = self._entities.get(entity.entity_id)

        if existing is not None:
            return EntityRegistration(
                entity=existing,
                is_new=False,
            )

        self._entities[entity.entity_id] = entity

        return EntityRegistration(
            entity=entity,
            is_new=True,
        )

    def register_concept(
        self,
        concept: Concept,
    ) -> ConceptRegistration:
        if not isinstance(concept, Concept):
            raise TypeError("concept must be a Concept")

        existing = self._concepts.get(concept.concept_id)

        if existing is not None:
            return ConceptRegistration(
                concept=existing,
                is_new=False,
            )

        self._concepts[concept.concept_id] = concept

        return ConceptRegistration(
            concept=concept,
            is_new=True,
        )

    def get_entity(
        self,
        entity_id: str,
    ) -> Entity | None:
        return self._entities.get(entity_id)

    def require_entity(
        self,
        entity_id: str,
    ) -> Entity:
        entity = self.get_entity(entity_id)

        if entity is None:
            raise KeyError(
                f"Unknown entity: {entity_id}"
            )

        return entity

    def get_concept(
        self,
        concept_id: str,
    ) -> Concept | None:
        return self._concepts.get(concept_id)

    def require_concept(
        self,
        concept_id: str,
    ) -> Concept:
        concept = self.get_concept(concept_id)

        if concept is None:
            raise KeyError(
                f"Unknown concept: {concept_id}"
            )

        return concept

    def contains_entity(
        self,
        entity_id: str,
    ) -> bool:
        return entity_id in self._entities

    def contains_concept(
        self,
        concept_id: str,
    ) -> bool:
        return concept_id in self._concepts

    def all_entities(self) -> Iterable[Entity]:
        return tuple(self._entities.values())

    def all_concepts(self) -> Iterable[Concept]:
        return tuple(self._concepts.values())

    def entity_count(self) -> int:
        return len(self._entities)

    def concept_count(self) -> int:
        return len(self._concepts)

    def clear(self) -> None:
        self._entities.clear()
        self._concepts.clear()

    def summary(self) -> dict:
        return {
            "entity_count": self.entity_count(),
            "concept_count": self.concept_count(),
        }
