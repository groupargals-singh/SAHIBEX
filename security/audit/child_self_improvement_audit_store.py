"""Persistent, append-only, tamper-evident child-improvement audit journal.

This store records decisions and provenance only. It never applies upgrades,
changes permissions, or modifies the SAHIBEX Constitution.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GENESIS_HASH = "0" * 64


class ChildSelfImprovementAuditStore:
    VERSION = "1.0"

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(
            str(self.database_path),
            timeout=10.0,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS child_improvement_audit_events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_id TEXT NOT NULL UNIQUE,
                payload TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                record_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._connection.executescript(
            """
            CREATE TRIGGER IF NOT EXISTS child_improvement_audit_no_update
            BEFORE UPDATE ON child_improvement_audit_events
            BEGIN
                SELECT RAISE(ABORT, 'audit_events_are_append_only');
            END;
            CREATE TRIGGER IF NOT EXISTS child_improvement_audit_no_delete
            BEFORE DELETE ON child_improvement_audit_events
            BEGIN
                SELECT RAISE(ABORT, 'audit_events_are_append_only');
            END;
            """
        )
        self._connection.commit()

    @staticmethod
    def _canonical(value: Any) -> str:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def _hash_record(
        cls,
        audit_id: str,
        payload: str,
        previous_hash: str,
        created_at: str,
    ) -> str:
        body = cls._canonical({
            "audit_id": audit_id,
            "payload": json.loads(payload),
            "previous_hash": previous_hash,
            "created_at": created_at,
        })
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def append(
        self,
        *,
        audit_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(audit_id, str) or not audit_id.strip():
            raise ValueError("audit_id must be non-empty")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dictionary")
        payload_text = self._canonical(payload)
        created_at = datetime.now(timezone.utc).isoformat()

        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                previous = self._connection.execute(
                    "SELECT record_hash FROM child_improvement_audit_events "
                    "ORDER BY sequence DESC LIMIT 1"
                ).fetchone()
                previous_hash = previous["record_hash"] if previous else GENESIS_HASH
                record_hash = self._hash_record(
                    audit_id, payload_text, previous_hash, created_at
                )
                cursor = self._connection.execute(
                    """
                    INSERT INTO child_improvement_audit_events
                    (audit_id, payload, previous_hash, record_hash, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (audit_id, payload_text, previous_hash, record_hash, created_at),
                )
                sequence = int(cursor.lastrowid)
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise

        return {
            "sequence": sequence,
            "audit_id": audit_id,
            "previous_hash": previous_hash,
            "record_hash": record_hash,
            "created_at": created_at,
        }

    def verify_chain(self) -> bool:
        with self._lock:
            rows = self._connection.execute(
                "SELECT audit_id, payload, previous_hash, record_hash, created_at "
                "FROM child_improvement_audit_events ORDER BY sequence"
            ).fetchall()

        expected_previous = GENESIS_HASH
        for row in rows:
            if row["previous_hash"] != expected_previous:
                return False
            try:
                expected_hash = self._hash_record(
                    row["audit_id"],
                    row["payload"],
                    row["previous_hash"],
                    row["created_at"],
                )
            except (TypeError, ValueError, json.JSONDecodeError):
                return False
            if not hmac.compare_digest(expected_hash, row["record_hash"]):
                return False
            expected_previous = row["record_hash"]
        return True

    def get_event(self, audit_id: str) -> dict[str, Any] | None:
        if not isinstance(audit_id, str) or not audit_id.strip():
            raise ValueError("audit_id must be non-empty")
        with self._lock:
            row = self._connection.execute(
                "SELECT sequence, audit_id, payload, previous_hash, record_hash, created_at "
                "FROM child_improvement_audit_events WHERE audit_id = ?",
                (audit_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "sequence": row["sequence"],
            "audit_id": row["audit_id"],
            "payload": json.loads(row["payload"]),
            "previous_hash": row["previous_hash"],
            "record_hash": row["record_hash"],
            "created_at": row["created_at"],
        }

    def list_events(self, *, limit: int = 100) -> list[dict[str, Any]]:
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 10000:
            raise ValueError("limit must be an integer between 1 and 10000")
        with self._lock:
            rows = self._connection.execute(
                "SELECT sequence, audit_id, payload, previous_hash, record_hash, created_at "
                "FROM child_improvement_audit_events ORDER BY sequence DESC LIMIT ?",
                (limit,),
            ).fetchall()
        result = []
        for row in rows:
            result.append({
                "sequence": row["sequence"],
                "audit_id": row["audit_id"],
                "payload": json.loads(row["payload"]),
                "previous_hash": row["previous_hash"],
                "record_hash": row["record_hash"],
                "created_at": row["created_at"],
            })
        return result

    def close(self) -> None:
        with self._lock:
            self._connection.close()
