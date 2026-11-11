from __future__ import annotations

import sqlite3
from pathlib import Path

from core.research.memory_association import MemoryAssociation


class MemoryAssociationStorage:
    """
    Persistent SQLite storage for associative memory links.

    Stores relationships between memories and shared concepts,
    entities, events, knowledge, sources and experiences.

    This layer stores links, not duplicated memory content.
    """

    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)

        if self.database_path != Path(":memory:"):
            self.database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._connection = sqlite3.connect(str(self.database_path))
        self._connection.row_factory = sqlite3.Row
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS memory_associations (
                association_id TEXT PRIMARY KEY,
                source_memory_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                target_type TEXT NOT NULL,
                association_type TEXT NOT NULL,
                strength REAL NOT NULL,
                confidence REAL NOT NULL,
                metadata TEXT NOT NULL,
                UNIQUE(
                    source_memory_id,
                    target_id,
                    target_type,
                    association_type
                )
            );

            CREATE INDEX IF NOT EXISTS
            idx_memory_assoc_source
            ON memory_associations(source_memory_id);

            CREATE INDEX IF NOT EXISTS
            idx_memory_assoc_target
            ON memory_associations(target_id);

            CREATE INDEX IF NOT EXISTS
            idx_memory_assoc_target_type
            ON memory_associations(target_type);

            CREATE INDEX IF NOT EXISTS
            idx_memory_assoc_type
            ON memory_associations(association_type);
            """
        )

        self._connection.commit()

    @staticmethod
    def _serialize_metadata(metadata: dict) -> str:
        import json

        return json.dumps(
            metadata,
            sort_keys=True,
            default=str,
        )

    @staticmethod
    def _deserialize_metadata(data: str) -> dict:
        import json

        return json.loads(data)

    def memory_exists(self, memory_id: str) -> bool:
        """Check a memory target against the canonical shared memories table."""
        if not isinstance(memory_id, str) or not memory_id.strip():
            return False
        try:
            row = self._connection.execute(
                "SELECT 1 FROM memories WHERE memory_id = ? LIMIT 1",
                (memory_id.strip(),),
            ).fetchone()
        except sqlite3.OperationalError:
            # A standalone association DB has no authoritative memory table;
            # never report an external memory target as existing in that case.
            return False
        return row is not None

    def save_association(
        self,
        association: MemoryAssociation,
    ) -> MemoryAssociation:
        if not isinstance(association, MemoryAssociation):
            raise TypeError(
                "association must be a MemoryAssociation"
            )

        existing = self.get_association(
            association.source_memory_id,
            association.target_id,
            association.target_type,
            association.association_type,
        )

        if existing is not None:
            return existing

        self._connection.execute(
            """
            INSERT INTO memory_associations (
                association_id,
                source_memory_id,
                target_id,
                target_type,
                association_type,
                strength,
                confidence,
                metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                association.association_id,
                association.source_memory_id,
                association.target_id,
                association.target_type,
                association.association_type,
                association.strength,
                association.confidence,
                self._serialize_metadata(
                    association.metadata
                ),
            ),
        )

        self._connection.commit()
        return association

    def get_association(
        self,
        source_memory_id: str,
        target_id: str,
        target_type: str,
        association_type: str,
    ) -> MemoryAssociation | None:
        row = self._connection.execute(
            """
            SELECT *
            FROM memory_associations
            WHERE source_memory_id = ?
              AND target_id = ?
              AND target_type = ?
              AND association_type = ?
            """,
            (
                source_memory_id,
                target_id,
                target_type,
                association_type,
            ),
        ).fetchone()

        if row is None:
            return None

        return self._row_to_association(row)

    def get_by_id(
        self,
        association_id: str,
    ) -> MemoryAssociation | None:
        row = self._connection.execute(
            """
            SELECT *
            FROM memory_associations
            WHERE association_id = ?
            """,
            (association_id,),
        ).fetchone()

        if row is None:
            return None

        return self._row_to_association(row)

    def associations_for_memory(
        self,
        memory_id: str,
    ) -> tuple[MemoryAssociation, ...]:
        rows = self._connection.execute(
            """
            SELECT *
            FROM memory_associations
            WHERE source_memory_id = ?
            ORDER BY association_id
            """,
            (memory_id,),
        ).fetchall()

        return tuple(
            self._row_to_association(row)
            for row in rows
        )

    def memories_for_target(
        self,
        target_id: str,
        target_type: str,
    ) -> tuple[str, ...]:
        rows = self._connection.execute(
            """
            SELECT source_memory_id
            FROM memory_associations
            WHERE target_id = ?
              AND target_type = ?
            ORDER BY source_memory_id
            """,
            (
                target_id,
                target_type,
            ),
        ).fetchall()

        return tuple(
            row["source_memory_id"]
            for row in rows
        )

    def association_count(self) -> int:
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM memory_associations
            """
        ).fetchone()

        return int(row["count"])

    def _row_to_association(
        self,
        row: sqlite3.Row,
    ) -> MemoryAssociation:
        return MemoryAssociation(
            association_id=row["association_id"],
            source_memory_id=row["source_memory_id"],
            target_id=row["target_id"],
            target_type=row["target_type"],
            association_type=row["association_type"],
            strength=float(row["strength"]),
            confidence=float(row["confidence"]),
            metadata=self._deserialize_metadata(
                row["metadata"]
            ),
        )

    def summary(self) -> dict[str, object]:
        return {
            "association_count": self.association_count(),
            "database": str(self.database_path),
            "stores_links_not_duplicate_memory_content": True,
            "grants_permission": False,
            "executes_actions": False,
            "modifies_constitution": False,
        }

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> "MemoryAssociationStorage":
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()
