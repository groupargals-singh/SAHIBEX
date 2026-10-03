from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from core.research.knowledge_registry import (
    Concept,
    Entity,
)
from core.research.relationship import Relationship
from core.research.storage import ResearchStorage


class KnowledgeGraphStorage:
    """
    Persistent SQLite storage for SAHIBEX knowledge-graph objects.

    Stores:
    - Entities
    - Concepts
    - Relationships

    This storage is intentionally separate from the existing research
    tables while using the same SQLite database architecture and
    serialization rules as ResearchStorage.
    """

    def __init__(
        self,
        database_path: Path | str,
    ) -> None:
        self.database_path = Path(database_path)

        if self.database_path != Path(":memory:"):
            self.database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._connection = sqlite3.connect(
            str(self.database_path),
        )

        self._connection.row_factory = sqlite3.Row
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS knowledge_entities (
                entity_id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS knowledge_concepts (
                concept_id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS knowledge_relationships (
                relationship_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                source_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                target_type TEXT NOT NULL,
                data TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS
            idx_relationships_source
            ON knowledge_relationships(source_id);

            CREATE INDEX IF NOT EXISTS
            idx_relationships_target
            ON knowledge_relationships(target_id);

            CREATE INDEX IF NOT EXISTS
            idx_relationships_source_type
            ON knowledge_relationships(source_type);

            CREATE INDEX IF NOT EXISTS
            idx_relationships_target_type
            ON knowledge_relationships(target_type);
            """
        )

        self._connection.commit()

    # ---------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------

    @staticmethod
    def _serialize(value: object) -> str:
        return ResearchStorage._serialize(value)

    @staticmethod
    def _deserialize(data: str) -> dict:
        return ResearchStorage._deserialize(data)

    # ---------------------------------------------------------
    # Entities
    # ---------------------------------------------------------

    def save_entity(
        self,
        entity: Entity,
    ) -> None:
        if not isinstance(entity, Entity):
            raise TypeError(
                "entity must be an Entity"
            )

        self._connection.execute(
            """
            INSERT OR REPLACE INTO knowledge_entities
            (entity_id, data)
            VALUES (?, ?)
            """,
            (
                entity.entity_id,
                self._serialize(entity),
            ),
        )

        self._connection.commit()

    def get_entity(
        self,
        entity_id: str,
    ) -> Optional[Entity]:
        row = self._connection.execute(
            """
            SELECT data
            FROM knowledge_entities
            WHERE entity_id = ?
            """,
            (entity_id,),
        ).fetchone()

        if row is None:
            return None

        return Entity(
            **self._deserialize(row["data"])
        )

    def entity_count(self) -> int:
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM knowledge_entities
            """
        ).fetchone()

        return int(row["count"])

    # ---------------------------------------------------------
    # Concepts
    # ---------------------------------------------------------

    def save_concept(
        self,
        concept: Concept,
    ) -> None:
        if not isinstance(concept, Concept):
            raise TypeError(
                "concept must be a Concept"
            )

        self._connection.execute(
            """
            INSERT OR REPLACE INTO knowledge_concepts
            (concept_id, data)
            VALUES (?, ?)
            """,
            (
                concept.concept_id,
                self._serialize(concept),
            ),
        )

        self._connection.commit()

    def get_concept(
        self,
        concept_id: str,
    ) -> Optional[Concept]:
        row = self._connection.execute(
            """
            SELECT data
            FROM knowledge_concepts
            WHERE concept_id = ?
            """,
            (concept_id,),
        ).fetchone()

        if row is None:
            return None

        return Concept(
            **self._deserialize(row["data"])
        )

    def concept_count(self) -> int:
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM knowledge_concepts
            """
        ).fetchone()

        return int(row["count"])

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    def save_relationship(
        self,
        relationship: Relationship,
    ) -> None:
        if not isinstance(relationship, Relationship):
            raise TypeError(
                "relationship must be a Relationship"
            )

        self._connection.execute(
            """
            INSERT OR REPLACE INTO knowledge_relationships
            (
                relationship_id,
                source_id,
                source_type,
                target_id,
                target_type,
                data
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                relationship.relationship_id,
                relationship.source_id,
                relationship.source_type,
                relationship.target_id,
                relationship.target_type,
                self._serialize(relationship),
            ),
        )

        self._connection.commit()

    def get_relationship(
        self,
        relationship_id: str,
    ) -> Optional[Relationship]:
        row = self._connection.execute(
            """
            SELECT data
            FROM knowledge_relationships
            WHERE relationship_id = ?
            """,
            (relationship_id,),
        ).fetchone()

        if row is None:
            return None

        return Relationship(
            **self._deserialize(row["data"])
        )

    def relationship_count(self) -> int:
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM knowledge_relationships
            """
        ).fetchone()

        return int(row["count"])

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    def summary(self) -> dict:
        return {
            "database": str(self.database_path),
            "entities": self.entity_count(),
            "concepts": self.concept_count(),
            "relationships": self.relationship_count(),
        }

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> "KnowledgeGraphStorage":
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()
