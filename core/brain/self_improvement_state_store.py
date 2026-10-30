"""Durable snapshot storage for the metadata-only self-improvement registry.

The state snapshot is integrity-checked and atomically replaced in SQLite. The
append-only audit journal remains the authoritative lifecycle history. Invalid
or unreadable state fails closed; it is never silently reset.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import threading
from pathlib import Path
from typing import Any


class SelfImprovementStateStore:
    VERSION = 1

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(str(self.database_path), timeout=10.0, check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.execute("""CREATE TABLE IF NOT EXISTS self_improvement_state (
            singleton INTEGER PRIMARY KEY CHECK(singleton=1),
            version INTEGER NOT NULL,
            revision INTEGER NOT NULL,
            payload TEXT NOT NULL,
            digest TEXT NOT NULL
        )""")
        self._db.commit()

    @staticmethod
    def _canonical(payload: dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def _digest(cls, version: int, revision: int, payload: str) -> str:
        raw = f"{version}:{revision}:{payload}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def load(self) -> dict[str, Any] | None:
        with self._lock:
            row = self._db.execute(
                "SELECT version, revision, payload, digest FROM self_improvement_state WHERE singleton=1"
            ).fetchone()
        if row is None:
            return None
        version, revision, payload, digest = row
        if version != self.VERSION or not isinstance(revision, int) or revision < 1:
            raise RuntimeError("self_improvement_state_version_or_revision_invalid")
        if not hmac.compare_digest(self._digest(version, revision, payload), digest):
            raise RuntimeError("self_improvement_state_integrity_check_failed")
        try:
            decoded = json.loads(payload)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("self_improvement_state_payload_invalid") from exc
        if not isinstance(decoded, dict) or not isinstance(decoded.get("skills"), list) or not isinstance(decoded.get("proposals"), list):
            raise RuntimeError("self_improvement_state_schema_invalid")
        decoded["_revision"] = revision
        return decoded

    def save(self, state: dict[str, Any]) -> int:
        payload_data = {key: value for key, value in state.items() if key != "_revision"}
        payload = self._canonical(payload_data)
        with self._lock:
            row = self._db.execute(
                "SELECT revision FROM self_improvement_state WHERE singleton=1"
            ).fetchone()
            revision = (int(row[0]) if row else 0) + 1
            digest = self._digest(self.VERSION, revision, payload)
            self._db.execute("BEGIN IMMEDIATE")
            try:
                self._db.execute(
                    "INSERT INTO self_improvement_state(singleton,version,revision,payload,digest) VALUES(1,?,?,?,?) "
                    "ON CONFLICT(singleton) DO UPDATE SET version=excluded.version, revision=excluded.revision, payload=excluded.payload, digest=excluded.digest",
                    (self.VERSION, revision, payload, digest),
                )
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise
        return revision

    def close(self) -> None:
        with self._lock:
            self._db.close()
