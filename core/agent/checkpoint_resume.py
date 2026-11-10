from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_safe(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


@dataclass(frozen=True)
class CheckpointRecord:
    job_id: str
    runtime_id: str
    sequence: int
    schema_version: int
    state: dict[str, Any]
    state_hash: str
    created_at: str


class CheckpointResumeStore:
    """Additive checkpoint/resume boundary with integrity and identity checks.

    Storage is snapshot-based and portable: callers may persist the exported
    records externally without giving this component authority or execution.
    """

    SCHEMA_VERSION = 1
    FORBIDDEN_KEYS = frozenset({
        "permission", "authority", "credentials", "credential",
        "token", "secret", "password",
    })

    def __init__(self, persistence_path: str | Path | None = None) -> None:
        self._records: dict[str, CheckpointRecord] = {}
        self.persistence_path = Path(persistence_path).expanduser() if persistence_path else None
        if self.persistence_path is not None and self.persistence_path.exists():
            self.load_file(self.persistence_path)

    @classmethod
    def _sanitize(cls, state: dict[str, Any]) -> dict[str, Any]:
        def clean(value: Any) -> Any:
            if isinstance(value, dict):
                return {
                    str(key): clean(item)
                    for key, item in value.items()
                    if not any(
                        blocked in str(key).lower()
                        for blocked in cls.FORBIDDEN_KEYS
                    )
                }
            if isinstance(value, list):
                return [clean(item) for item in value]
            return value
        return clean(state)

    @staticmethod
    def _hash(state: dict[str, Any]) -> str:
        raw = json.dumps(state, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    def save(self, job_id: str, runtime_id: str, sequence: int, state: dict[str, Any]) -> CheckpointRecord:
        if not job_id.strip() or not runtime_id.strip():
            raise ValueError("job_id and runtime_id are required")
        if sequence < 0:
            raise ValueError("sequence must be non-negative")
        safe = self._sanitize(_json_safe(dict(state)))
        record = CheckpointRecord(
            job_id, runtime_id, sequence, self.SCHEMA_VERSION,
            safe, self._hash(safe), _now(),
        )
        previous = self._records.get(job_id)
        self._records[job_id] = record
        try:
            self._persist_if_configured()
        except Exception:
            if previous is None:
                self._records.pop(job_id, None)
            else:
                self._records[job_id] = previous
            raise
        return record

    def load(self, job_id: str) -> CheckpointRecord:
        if job_id not in self._records:
            raise KeyError(job_id)
        return self._records[job_id]

    def verify(self, record: CheckpointRecord) -> bool:
        if record.schema_version != self.SCHEMA_VERSION:
            return False
        return self._hash(record.state) == record.state_hash

    def validate_resume(self, record: CheckpointRecord, *, job_id: str, runtime_id: str) -> bool:
        return (
            record.job_id == job_id
            and record.runtime_id == runtime_id
            and self.verify(record)
        )

    def resume_state(self, job_id: str, *, runtime_id: str) -> dict[str, Any]:
        record = self.load(job_id)
        if not self.validate_resume(record, job_id=job_id, runtime_id=runtime_id):
            raise ValueError("checkpoint failed identity, schema, or integrity validation")
        return dict(record.state)

    def export_snapshot(self) -> list[dict[str, Any]]:
        return [
            {
                "job_id": r.job_id,
                "runtime_id": r.runtime_id,
                "sequence": r.sequence,
                "schema_version": r.schema_version,
                "state": dict(r.state),
                "state_hash": r.state_hash,
                "created_at": r.created_at,
            }
            for r in self._records.values()
        ]

    def import_snapshot(self, snapshot: list[dict[str, Any]]) -> None:
        if not isinstance(snapshot, list):
            raise TypeError("checkpoint snapshot must be a list")
        validated: dict[str, CheckpointRecord] = {}
        for item in snapshot:
            if not isinstance(item, dict):
                raise ValueError("checkpoint snapshot item must be an object")
            record = CheckpointRecord(
                item["job_id"], item["runtime_id"], int(item["sequence"]),
                int(item["schema_version"]), dict(item["state"]),
                item["state_hash"], item["created_at"],
            )
            if not self.verify(record) or not record.job_id or not record.runtime_id:
                raise ValueError("corrupted or incompatible checkpoint snapshot")
            if record.job_id in validated:
                raise ValueError("duplicate checkpoint job identity")
            validated[record.job_id] = record
        # Commit only after every record has passed validation and durable write.
        previous = self._records
        self._records = validated
        try:
            self._persist_if_configured()
        except Exception:
            self._records = previous
            raise

    def save_file(self, path: str | Path | None = None) -> Path:
        target = Path(path).expanduser() if path is not None else self.persistence_path
        if target is None:
            raise ValueError("checkpoint persistence path is not configured")
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "records": self.export_snapshot(),
        }
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, target)
            try:
                directory_fd = os.open(str(target.parent), os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except OSError:
                pass
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return target

    def load_file(self, path: str | Path | None = None) -> None:
        target = Path(path).expanduser() if path is not None else self.persistence_path
        if target is None:
            raise ValueError("checkpoint persistence path is not configured")
        payload = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError("checkpoint file schema is incompatible")
        records = payload.get("records")
        temporary_store = CheckpointResumeStore()
        temporary_store.import_snapshot(records)
        self._records = temporary_store._records

    def _persist_if_configured(self) -> None:
        if self.persistence_path is not None:
            self.save_file(self.persistence_path)

    @staticmethod
    def grants_permission() -> bool:
        return False

    @staticmethod
    def executes_protected_actions() -> bool:
        return False
