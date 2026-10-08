from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
import hashlib
import json
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

    def __init__(self) -> None:
        self._records: dict[str, CheckpointRecord] = {}

    @classmethod
    def _sanitize(cls, state: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in state.items() if k.lower() not in cls.FORBIDDEN_KEYS}

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
        self._records[job_id] = record
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
        for item in snapshot:
            record = CheckpointRecord(
                item["job_id"], item["runtime_id"], int(item["sequence"]),
                int(item["schema_version"]), dict(item["state"]),
                item["state_hash"], item["created_at"],
            )
            if not self.verify(record):
                raise ValueError("corrupted or incompatible checkpoint snapshot")
            self._records[record.job_id] = record

    @staticmethod
    def grants_permission() -> bool:
        return False

    @staticmethod
    def executes_protected_actions() -> bool:
        return False
