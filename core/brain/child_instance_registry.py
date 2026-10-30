"""Persistent registry for Child Brain identities and lifecycle metadata.

The registry does not run child code or grant tool/financial/system authority.
Birth and activation require explicit approvals; every mutation is recorded in
an append-only hash chain. Runtime resource telemetry is intentionally rebuilt
on restore rather than treated as persistent identity.
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
from uuid import uuid4

from core.brain.root_identity import SahibexRootIdentity
from core.brain.specialist_brain import (
    BrainCapability,
    BrainStatus,
    SpecialistBrain,
)
from core.brain.verification import BrainTrustStatus
from core.policies.constitution import BrainRole


_GENESIS = "0" * 64


class ChildInstanceRegistry:
    VERSION = "1.0"

    def __init__(
        self,
        database_path: str | Path,
        *,
        root_identity: SahibexRootIdentity | None = None,
    ) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.root_identity = root_identity or SahibexRootIdentity()
        if not self.root_identity.validate():
            raise ValueError("invalid_sahibex_root_identity")
        self._lock = threading.RLock()
        self._db = sqlite3.connect(
            str(self.database_path), timeout=10.0, check_same_thread=False
        )
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS child_instances (
                brain_id TEXT PRIMARY KEY,
                parent_brain_id TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                revision INTEGER NOT NULL,
                record_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS child_instance_events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                brain_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                record_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TRIGGER IF NOT EXISTS child_instance_events_no_update
            BEFORE UPDATE ON child_instance_events BEGIN
                SELECT RAISE(ABORT, 'child_instance_events_are_append_only');
            END;
            CREATE TRIGGER IF NOT EXISTS child_instance_events_no_delete
            BEFORE DELETE ON child_instance_events BEGIN
                SELECT RAISE(ABORT, 'child_instance_events_are_append_only');
            END;
            """
        )
        self._db.commit()

    @staticmethod
    def _canonical(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def _data_hash(cls, data: dict[str, Any]) -> str:
        return hashlib.sha256(cls._canonical(data).encode("utf-8")).hexdigest()

    @classmethod
    def _event_hash(
        cls, event_id: str, brain_id: str, event_type: str,
        payload: str, previous_hash: str, created_at: str,
    ) -> str:
        canonical = cls._canonical({
            "event_id": event_id,
            "brain_id": brain_id,
            "event_type": event_type,
            "payload": json.loads(payload),
            "previous_hash": previous_hash,
            "created_at": created_at,
        })
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _append_event_locked(self, brain_id: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        previous = self._db.execute(
            "SELECT record_hash FROM child_instance_events ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        previous_hash = previous["record_hash"] if previous else _GENESIS
        event_id = f"child-event-{uuid4()}"
        created_at = datetime.now(timezone.utc).isoformat()
        payload_text = self._canonical(payload)
        record_hash = self._event_hash(
            event_id, brain_id, event_type, payload_text, previous_hash, created_at
        )
        cursor = self._db.execute(
            "INSERT INTO child_instance_events "
            "(event_id, brain_id, event_type, payload, previous_hash, record_hash, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (event_id, brain_id, event_type, payload_text, previous_hash, record_hash, created_at),
        )
        return {
            "sequence": int(cursor.lastrowid), "event_id": event_id,
            "record_hash": record_hash, "previous_hash": previous_hash,
            "created_at": created_at,
        }

    def _save_data_locked(self, brain: SpecialistBrain, *, created_at: str | None = None, revision: int = 1) -> tuple[str, str, str]:
        now = datetime.now(timezone.utc).isoformat()
        existing = self._db.execute(
            "SELECT created_at, revision FROM child_instances WHERE brain_id=?",
            (brain.brain_id,),
        ).fetchone()
        first_created = created_at or (existing["created_at"] if existing else now)
        next_revision = revision if existing is None else int(existing["revision"]) + 1
        data = {
            "brain_id": brain.brain_id,
            "name": brain.name,
            "description": brain.description,
            "specialization": brain.specialization,
            "capabilities": sorted(cap.value for cap in brain.capabilities),
            "status": brain.status.value,
            "trust_status": brain.trust_status.value,
            "trust_evidence": brain.trust_evidence,
            "brain_role": brain.brain_role.value,
            "parent_brain_id": brain.parent_brain_id,
        }
        data_text = self._canonical(data)
        record_hash = self._data_hash(data)
        self._db.execute(
            "INSERT OR REPLACE INTO child_instances "
            "(brain_id,parent_brain_id,data,created_at,updated_at,revision,record_hash) "
            "VALUES (?,?,?,?,?,?,?)",
            (brain.brain_id, brain.parent_brain_id or "", data_text, first_created, now, next_revision, record_hash),
        )
        return data_text, first_created, now

    def register(
        self,
        brain: SpecialistBrain,
        *,
        mother_approved: bool,
        human_approved: bool,
        authorization_valid: bool,
    ) -> dict[str, Any]:
        if not isinstance(brain, SpecialistBrain):
            raise TypeError("brain must be SpecialistBrain")
        if brain.brain_role != BrainRole.CHILD_BRAIN:
            raise ValueError("registry_only_accepts_child_brains")
        if brain.brain_id == self.root_identity.BRAIN_ID:
            raise ValueError("mother_brain_id_is_reserved")
        if brain.status != BrainStatus.REGISTERED:
            raise ValueError("new_child_must_start_registered")
        if not brain.parent_brain_id:
            raise ValueError("child_parent_identity_required")
        if not (mother_approved and human_approved and authorization_valid):
            raise PermissionError("mother_and_human_approval_with_valid_authorization_required")
        if brain.parent_brain_id != self.root_identity.BRAIN_ID:
            parent = self.get(brain.parent_brain_id)
            if parent is None or parent.status not in {BrainStatus.READY, BrainStatus.ACTIVE}:
                raise ValueError("parent_child_brain_must_exist_and_be_ready")
            if parent.trust_status != BrainTrustStatus.VERIFIED or not parent.trust_evidence:
                raise PermissionError("parent_child_brain_must_have_verified_trust")
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                if self._db.execute(
                    "SELECT 1 FROM child_instances WHERE brain_id=?", (brain.brain_id,)
                ).fetchone():
                    raise ValueError("child_brain_id_already_registered")
                data_text, created_at, updated_at = self._save_data_locked(brain)
                event = self._append_event_locked(brain.brain_id, "registered", {
                    "parent_brain_id": brain.parent_brain_id,
                    "mother_approved": True,
                    "human_approved": True,
                    "authorization_valid": True,
                    "record_hash": self._data_hash(json.loads(data_text)),
                })
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise
        return {"brain_id": brain.brain_id, "status": brain.status.value, "created_at": created_at, "updated_at": updated_at, "event": event}

    def get(self, brain_id: str) -> SpecialistBrain | None:
        if not isinstance(brain_id, str) or not brain_id.strip():
            raise ValueError("brain_id must be non-empty")
        with self._lock:
            row = self._db.execute(
                "SELECT data, record_hash FROM child_instances WHERE brain_id=?", (brain_id,)
            ).fetchone()
        if row is None:
            return None
        data = json.loads(row["data"])
        if not hmac.compare_digest(self._data_hash(data), row["record_hash"]):
            raise ValueError("child_instance_record_integrity_failure")
        return SpecialistBrain(
            name=data["name"],
            description=data["description"],
            specialization=data["specialization"],
            capabilities={BrainCapability(value) for value in data["capabilities"]},
            brain_id=data["brain_id"],
            status=BrainStatus(data["status"]),
            trust_status=BrainTrustStatus(data["trust_status"]),
            trust_evidence=data["trust_evidence"],
            brain_role=BrainRole(data["brain_role"]),
            parent_brain_id=data["parent_brain_id"],
        )

    def transition(
        self,
        brain_id: str,
        target_status: BrainStatus,
        *,
        mother_approved: bool = False,
        human_approved: bool = False,
        verification_passed: bool = False,
        reason: str,
    ) -> dict[str, Any]:
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("transition_reason_required")
        brain = self.get(brain_id)
        if brain is None:
            raise KeyError("child_brain_not_found")
        if target_status == BrainStatus.ACTIVE:
            if not (mother_approved and human_approved and verification_passed):
                raise PermissionError("child_activation_requires_mother_human_and_verification")
            if brain.trust_status != BrainTrustStatus.VERIFIED or not brain.trust_evidence:
                raise PermissionError("verified_trust_evidence_required_for_activation")
        elif target_status == BrainStatus.READY:
            if not mother_approved or not verification_passed:
                raise PermissionError("mother_approval_and_verification_required_for_ready_transition")
        elif target_status == BrainStatus.PAUSED:
            # Safe stop must remain available even when verification is failing.
            if not (mother_approved or human_approved):
                raise PermissionError("mother_or_human_approval_required_to_pause_child")
        elif target_status == BrainStatus.DISABLED:
            if not (mother_approved and human_approved):
                raise PermissionError("mother_and_human_approval_required_to_disable_child")
        old_status = brain.status
        brain.transition_to(target_status)
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                data_text, _, updated_at = self._save_data_locked(brain)
                event = self._append_event_locked(brain_id, "status_transition", {
                    "from_status": old_status.value,
                    "to_status": target_status.value,
                    "mother_approved": mother_approved,
                    "human_approved": human_approved,
                    "verification_passed": verification_passed,
                    "reason": reason.strip(),
                    "record_hash": self._data_hash(json.loads(data_text)),
                })
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise
        return {"brain_id": brain_id, "from_status": old_status.value, "to_status": target_status.value, "updated_at": updated_at, "event": event}

    def update_trust(
        self,
        brain_id: str,
        target_status: BrainTrustStatus,
        *,
        evidence: str | None,
        mother_approved: bool,
        human_approved: bool,
        reason: str,
    ) -> dict[str, Any]:
        if not (mother_approved and human_approved):
            raise PermissionError("mother_and_human_approval_required_for_trust_change")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("trust_change_reason_required")
        brain = self.get(brain_id)
        if brain is None:
            raise KeyError("child_brain_not_found")
        old_status = brain.trust_status
        brain.set_trust_status(target_status, evidence=evidence)
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                data_text, _, updated_at = self._save_data_locked(brain)
                event = self._append_event_locked(brain_id, "trust_transition", {
                    "from_trust_status": old_status.value,
                    "to_trust_status": target_status.value,
                    "mother_approved": True,
                    "human_approved": True,
                    "reason": reason.strip(),
                    "record_hash": self._data_hash(json.loads(data_text)),
                })
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise
        return {"brain_id": brain_id, "trust_status": target_status.value, "updated_at": updated_at, "event": event}

    def verify_integrity(self) -> bool:
        with self._lock:
            children = self._db.execute(
                "SELECT brain_id, data, record_hash FROM child_instances"
            ).fetchall()
            events = self._db.execute(
                "SELECT event_id,brain_id,event_type,payload,previous_hash,record_hash,created_at "
                "FROM child_instance_events ORDER BY sequence"
            ).fetchall()
        child_hashes: dict[str, str] = {}
        for row in children:
            try:
                data = json.loads(row["data"])
            except (TypeError, ValueError, json.JSONDecodeError):
                return False
            if data.get("brain_id") != row["brain_id"]:
                return False
            if not hmac.compare_digest(self._data_hash(data), row["record_hash"]):
                return False
            child_hashes[row["brain_id"]] = row["record_hash"]

        latest_state_hash: dict[str, str] = {}
        previous = _GENESIS
        for row in events:
            if row["previous_hash"] != previous:
                return False
            try:
                expected = self._event_hash(
                    row["event_id"], row["brain_id"], row["event_type"],
                    row["payload"], row["previous_hash"], row["created_at"],
                )
                payload = json.loads(row["payload"])
            except (TypeError, ValueError, json.JSONDecodeError):
                return False
            if not hmac.compare_digest(expected, row["record_hash"]):
                return False
            if row["event_type"] in {"registered", "status_transition", "trust_transition"}:
                state_hash = payload.get("record_hash")
                if not isinstance(state_hash, str) or len(state_hash) != 64:
                    return False
                latest_state_hash[row["brain_id"]] = state_hash
            previous = row["record_hash"]

        # Tie each mutable current-state row back to its latest immutable event.
        if set(child_hashes) != set(latest_state_hash):
            return False
        for brain_id, current_hash in child_hashes.items():
            if not hmac.compare_digest(current_hash, latest_state_hash[brain_id]):
                return False
        return True

    def list_children(self) -> list[SpecialistBrain]:
        """Return integrity-checked child identities; this never restores handlers."""
        with self._lock:
            rows = self._db.execute(
                "SELECT brain_id FROM child_instances ORDER BY created_at, brain_id"
            ).fetchall()
        children: list[SpecialistBrain] = []
        for row in rows:
            child = self.get(str(row["brain_id"]))
            if child is not None:
                children.append(child)
        return children

    def list_events(self, *, limit: int = 100) -> list[dict[str, Any]]:
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 10000:
            raise ValueError("limit must be between 1 and 10000")
        with self._lock:
            rows = self._db.execute(
                "SELECT sequence,event_id,brain_id,event_type,payload,previous_hash,record_hash,created_at "
                "FROM child_instance_events ORDER BY sequence DESC LIMIT ?", (limit,)
            ).fetchall()
        return [{
            "sequence": row["sequence"], "event_id": row["event_id"],
            "brain_id": row["brain_id"], "event_type": row["event_type"],
            "payload": json.loads(row["payload"]), "previous_hash": row["previous_hash"],
            "record_hash": row["record_hash"], "created_at": row["created_at"],
        } for row in rows]

    def close(self) -> None:
        with self._lock:
            self._db.close()
