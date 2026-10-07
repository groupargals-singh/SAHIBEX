from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


MEMORY_BACKUP_VERSION = "P2-MBACKUP-1"
MEMORY_BACKUP_SCHEMA_VERSION = 1


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class MemoryBackupResult:
    backup_id: str
    backup_path: str
    memory_count: int
    verification_count: int
    association_count: int
    checksum: str
    created_at: datetime
    version: str = MEMORY_BACKUP_VERSION


class MemoryBackupEngine:
    """
    Safe backup/recovery boundary for persistent SAHIBEX memory state.

    Backup is read-only against the source database.

    Restore is protected and requires explicit authorization.
    """

    VERSION = MEMORY_BACKUP_VERSION

    _REQUIRED_TABLES = {
        "memories",
        "memory_verification_records",
        "memory_associations",
    }

    @staticmethod
    def _validate_database_path(database_path: Path | str) -> Path:
        path = Path(database_path)

        if str(path) == ":memory:":
            raise ValueError("memory backup requires a persistent database")

        if not path.exists():
            raise FileNotFoundError(f"database does not exist: {path}")

        if not path.is_file():
            raise ValueError(f"database path is not a file: {path}")

        return path

    @staticmethod
    def _table_exists(
        connection: sqlite3.Connection,
        table_name: str,
    ) -> bool:
        row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = ?
            """,
            (table_name,),
        ).fetchone()

        return row is not None

    @classmethod
    def _validate_source_schema(
        cls,
        connection: sqlite3.Connection,
    ) -> None:
        missing = sorted(
            table
            for table in cls._REQUIRED_TABLES
            if not cls._table_exists(connection, table)
        )

        if missing == ["memory_associations"]:
            connection.executescript(
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
            connection.commit()
            missing = []

        if missing:
            raise ValueError(
                "memory backup schema incomplete; missing tables: "
                + ", ".join(missing)
            )
    @staticmethod
    def _canonical_json(value: Any) -> str:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def _checksum(cls, payload: dict[str, Any]) -> str:
        encoded = cls._canonical_json(payload).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _rows(
        connection: sqlite3.Connection,
        table_name: str,
    ) -> list[dict[str, Any]]:
        rows = connection.execute(
            f"SELECT * FROM {table_name}"
        ).fetchall()

        columns = [
            description[0]
            for description in connection.execute(
                f"SELECT * FROM {table_name} LIMIT 0"
            ).description
        ]

        return [
            {
                column: row[index]
                for index, column in enumerate(columns)
            }
            for row in rows
        ]

    @classmethod
    def create_backup(
        cls,
        database_path: Path | str,
        backup_path: Path | str,
    ) -> MemoryBackupResult:
        source = cls._validate_database_path(database_path)
        destination = Path(backup_path)

        destination.parent.mkdir(parents=True, exist_ok=True)

        connection = sqlite3.connect(str(source))
        connection.row_factory = sqlite3.Row

        try:
            cls._validate_source_schema(connection)

            memories = cls._rows(connection, "memories")
            verifications = cls._rows(
                connection,
                "memory_verification_records",
            )
            associations = cls._rows(
                connection,
                "memory_associations",
            )

        finally:
            connection.close()

        backup_id = f"memory-backup-{uuid4().hex}"
        created_at = utc_now().isoformat()

        payload = {
            "backup_id": backup_id,
            "backup_version": MEMORY_BACKUP_VERSION,
            "schema_version": MEMORY_BACKUP_SCHEMA_VERSION,
            "created_at": created_at,
            "scope": {
                "memories": True,
                "memory_verification_records": True,
                "memory_associations": True,
            },
            "memories": memories,
            "memory_verification_records": verifications,
            "memory_associations": associations,
        }

        checksum = cls._checksum(payload)

        package = {
            "format": "SAHIBEX_MEMORY_BACKUP",
            "version": MEMORY_BACKUP_VERSION,
            "payload": payload,
            "checksum": checksum,
        }

        temporary_path = destination.with_suffix(
            destination.suffix + ".tmp"
        )

        temporary_path.write_text(
            json.dumps(
                package,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            ),
            encoding="utf-8",
        )

        temporary_path.replace(destination)

        return MemoryBackupResult(
            backup_id=backup_id,
            backup_path=str(destination),
            memory_count=len(memories),
            verification_count=len(verifications),
            association_count=len(associations),
            checksum=checksum,
            created_at=datetime.fromisoformat(created_at),
        )

    @classmethod
    def validate_backup(
        cls,
        backup_path: Path | str,
    ) -> dict[str, Any]:
        path = Path(backup_path)

        if not path.exists():
            raise FileNotFoundError(f"backup does not exist: {path}")

        if not path.is_file():
            raise ValueError(f"backup path is not a file: {path}")

        try:
            package = json.loads(
                path.read_text(encoding="utf-8")
            )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                "backup is unreadable or invalid JSON"
            ) from exc

        if not isinstance(package, dict):
            raise ValueError("backup package must be an object")

        if package.get("format") != "SAHIBEX_MEMORY_BACKUP":
            raise ValueError("invalid memory backup format")

        if package.get("version") != MEMORY_BACKUP_VERSION:
            raise ValueError("unsupported memory backup version")

        payload = package.get("payload")
        checksum = package.get("checksum")

        if not isinstance(payload, dict):
            raise ValueError("backup payload is missing")

        if not isinstance(checksum, str) or not checksum:
            raise ValueError("backup checksum is missing")

        calculated = cls._checksum(payload)

        if calculated != checksum:
            raise ValueError("backup integrity check failed")

        required_payload_keys = {
            "backup_id",
            "backup_version",
            "schema_version",
            "created_at",
            "scope",
            "memories",
            "memory_verification_records",
            "memory_associations",
        }

        missing = sorted(
            required_payload_keys - set(payload.keys())
        )

        if missing:
            raise ValueError(
                "backup payload incomplete: "
                + ", ".join(missing)
            )

        for key in (
            "memories",
            "memory_verification_records",
            "memory_associations",
        ):
            if not isinstance(payload[key], list):
                raise ValueError(
                    f"backup field '{key}' must be a list"
                )

        return package

    @classmethod
    def restore_backup(
        cls,
        backup_path: Path | str,
        database_path: Path | str,
        *,
        authorized: bool = False,
    ) -> dict[str, Any]:
        """
        Restore memory state transactionally.

        This is a protected operation and therefore requires
        explicit authorization.
        """

        if authorized is not True:
            raise PermissionError(
                "memory restore requires explicit authorization"
            )

        package = cls.validate_backup(backup_path)
        payload = package["payload"]

        destination = Path(database_path)

        if str(destination) == ":memory:":
            raise ValueError(
                "memory restore requires a persistent database"
            )

        destination.parent.mkdir(parents=True, exist_ok=True)

        connection = sqlite3.connect(str(destination))
        connection.row_factory = sqlite3.Row

        try:
            cls._validate_source_schema(connection)

            connection.execute("BEGIN")

            connection.execute(
                "DELETE FROM memory_verification_records"
            )
            connection.execute("DELETE FROM memory_associations")
            connection.execute("DELETE FROM memories")

            for row in payload["memories"]:
                connection.execute(
                    """
                    INSERT INTO memories (
                        memory_id,
                        memory_type,
                        source,
                        importance,
                        confidence,
                        data
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["memory_id"],
                        row["memory_type"],
                        row["source"],
                        row["importance"],
                        row["confidence"],
                        row["data"],
                    ),
                )

            for row in payload["memory_verification_records"]:
                connection.execute(
                    """
                    INSERT INTO memory_verification_records (
                        memory_id,
                        status,
                        evidence_id,
                        reason,
                        verified_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        row["memory_id"],
                        row["status"],
                        row["evidence_id"],
                        row["reason"],
                        row["verified_at"],
                    ),
                )

            for row in payload["memory_associations"]:
                connection.execute(
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
                        row["association_id"],
                        row["source_memory_id"],
                        row["target_id"],
                        row["target_type"],
                        row["association_type"],
                        row["strength"],
                        row["confidence"],
                        row["metadata"],
                    ),
                )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

        return {
            "backup_id": payload["backup_id"],
            "backup_version": payload["backup_version"],
            "memory_count": len(payload["memories"]),
            "verification_count": len(
                payload["memory_verification_records"]
            ),
            "association_count": len(
                payload["memory_associations"]
            ),
            "checksum": package["checksum"],
            "restored": True,
        }
