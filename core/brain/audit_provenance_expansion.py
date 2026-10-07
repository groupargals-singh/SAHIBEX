from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib, json

@dataclass(frozen=True)
class AuditRecord:
    record_id: str
    actor_id: str
    event_type: str
    timestamp: str
    payload_hash: str
    provenance: dict

class AuditProvenanceEngine:
    VERSION = "AA-1"
    def __init__(self):
        self._records = []

    @staticmethod
    def _hash(payload):
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    def record(self, record_id, actor_id, event_type, payload, provenance=None):
        if not record_id or not actor_id or not event_type:
            raise ValueError("record identity is required")
        data = dict(payload or {})
        prov = dict(provenance or {})
        rec = AuditRecord(record_id, actor_id, event_type,
                          datetime.now(timezone.utc).isoformat(),
                          self._hash(data), prov)
        self._records.append(rec)
        return rec

    def records(self):
        return tuple(self._records)

    @staticmethod
    def verify(record, payload):
        return record.payload_hash == AuditProvenanceEngine._hash(payload)

    @staticmethod
    def evidence_chain(record):
        return tuple(record.provenance.get("evidence_ids", ()))

    @staticmethod
    def authority_flags(record):
        return {"grants_permission": False, "is_authority": False}

    @classmethod
    def tamper_detected(cls, record, payload):
        return not cls.verify(record, payload)
