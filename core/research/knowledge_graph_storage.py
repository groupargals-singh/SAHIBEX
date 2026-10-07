from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from core.research.fact import Fact
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
    - Facts
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

            CREATE TABLE IF NOT EXISTS knowledge_facts (
                fact_id TEXT PRIMARY KEY,
                subject_id TEXT NOT NULL,
                subject_type TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object_id TEXT,
                object_type TEXT,
                object_value TEXT,
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
            idx_facts_subject
            ON knowledge_facts(subject_id);

            CREATE INDEX IF NOT EXISTS
            idx_facts_object
            ON knowledge_facts(object_id);

            CREATE INDEX IF NOT EXISTS
            idx_facts_predicate
            ON knowledge_facts(predicate);

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
    # Facts
    # ---------------------------------------------------------

    def save_fact(
        self,
        fact: Fact,
    ) -> None:
        if not isinstance(fact, Fact):
            raise TypeError(
                "fact must be a Fact"
            )

        self._connection.execute(
            """
            INSERT OR REPLACE INTO knowledge_facts
            (
                fact_id,
                subject_id,
                subject_type,
                predicate,
                object_id,
                object_type,
                object_value,
                data
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fact.fact_id,
                fact.subject_id,
                fact.subject_type,
                fact.predicate,
                fact.object_id,
                fact.object_type,
                fact.object_value,
                self._serialize(fact),
            ),
        )

        self._connection.commit()

    def get_fact(
        self,
        fact_id: str,
    ) -> Optional[Fact]:
        row = self._connection.execute(
            """
            SELECT data
            FROM knowledge_facts
            WHERE fact_id = ?
            """,
            (fact_id,),
        ).fetchone()

        if row is None:
            return None

        return Fact(
            **self._deserialize(row["data"])
        )

    def fact_count(self) -> int:
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM knowledge_facts
            """
        ).fetchone()

        return int(row["count"])

    def facts_for_subject(
        self,
        subject_id: str,
    ) -> tuple[Fact, ...]:
        if not subject_id.strip():
            raise ValueError(
                "subject_id cannot be empty"
            )

        rows = self._connection.execute(
            """
            SELECT data
            FROM knowledge_facts
            WHERE subject_id = ?
            ORDER BY fact_id
            """,
            (subject_id,),
        ).fetchall()

        return tuple(
            Fact(
                **self._deserialize(row["data"])
            )
            for row in rows
        )

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
    # Concept Graph
    # ---------------------------------------------------------

    def concept_relationships(
        self,
        concept_id: str,
        relationship_type: Optional[str] = None,
    ) -> tuple[Relationship, ...]:
        """Return outgoing relationships from a concept."""

        if not concept_id.strip():
            raise ValueError(
                "concept_id cannot be empty"
            )

        if self.get_concept(concept_id) is None:
            raise KeyError(
                f"unknown concept: {concept_id}"
            )

        query = """
            SELECT data
            FROM knowledge_relationships
            WHERE source_id = ?
              AND source_type = 'concept'
              AND target_type = 'concept'
        """

        params: list[object] = [concept_id]

        if relationship_type is not None:
            if not relationship_type.strip():
                raise ValueError(
                    "relationship_type cannot be empty"
                )

            query += """
                AND json_extract(
                    data,
                    '$.relationship_type'
                ) = ?
            """

            params.append(relationship_type)

        query += " ORDER BY relationship_id"

        rows = self._connection.execute(
            query,
            tuple(params),
        ).fetchall()

        return tuple(
            Relationship(
                **self._deserialize(row["data"])
            )
            for row in rows
        )

    def concepts_related_to(
        self,
        concept_id: str,
        relationship_type: Optional[str] = None,
    ) -> tuple[str, ...]:
        """Return concept IDs related from the given concept."""

        relationships = self.concept_relationships(
            concept_id,
            relationship_type,
        )

        return tuple(
            relationship.target_id
            for relationship in relationships
        )

    def concepts_linked_to(
        self,
        concept_id: str,
        relationship_type: Optional[str] = None,
    ) -> tuple[str, ...]:
        """Return concept IDs having relationships to the given concept."""

        if not concept_id.strip():
            raise ValueError(
                "concept_id cannot be empty"
            )

        if self.get_concept(concept_id) is None:
            raise KeyError(
                f"unknown concept: {concept_id}"
            )

        query = """
            SELECT data
            FROM knowledge_relationships
            WHERE target_id = ?
              AND target_type = 'concept'
              AND source_type = 'concept'
        """

        params: list[object] = [concept_id]

        if relationship_type is not None:
            if not relationship_type.strip():
                raise ValueError(
                    "relationship_type cannot be empty"
                )

            query += """
                AND json_extract(
                    data,
                    '$.relationship_type'
                ) = ?
            """

            params.append(relationship_type)

        query += " ORDER BY relationship_id"

        rows = self._connection.execute(
            query,
            tuple(params),
        ).fetchall()

        return tuple(
            self._deserialize(row["data"])["source_id"]
            for row in rows
        )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    def summary(self) -> dict:
        return {
            "database": str(self.database_path),
            "entities": self.entity_count(),
            "concepts": self.concept_count(),
            "facts": self.fact_count(),
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
