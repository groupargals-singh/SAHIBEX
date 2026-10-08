from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib, json

@dataclass(frozen=True)
class BackupManifest:
    backup_id: str
    version: str
    schema_version: int
    created_at: str
    payload_checksum: str
    source_version: str

@dataclass(frozen=True)
class MigrationResult:
    source_version: str
    target_version: str
    migrated: bool
    compatible: bool

class BackupRecoveryManager:
    VERSION = "Z-1"
    FORBIDDEN_KEYS = frozenset({"credential","credentials","token","secret","password"})
    @classmethod
    def checksum(cls, payload):
        data=json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(",", ":")).encode()
        return hashlib.sha256(data).hexdigest()
    @classmethod
    def manifest(cls, backup_id, payload, source_version, schema_version=1):
        if not backup_id.strip() or not source_version.strip(): raise ValueError("backup_id and source_version are required")
        return BackupManifest(backup_id,cls.VERSION,schema_version,datetime.now(timezone.utc).isoformat(),cls.checksum(payload),source_version)
    @classmethod
    def verify_integrity(cls,payload,manifest): return cls.checksum(payload)==manifest.payload_checksum
    @classmethod
    def sanitize_state(cls, state):
        if not isinstance(state, dict):
            raise TypeError("state must be a dictionary")
        def clean(value):
            if isinstance(value, dict):
                return {
                    k: clean(v)
                    for k, v in value.items()
                    if str(k).lower() not in cls.FORBIDDEN_KEYS
                }
            if isinstance(value, list):
                return [clean(v) for v in value]
            if isinstance(value, tuple):
                return [clean(v) for v in value]
            return value
        return clean(state)
    @staticmethod
    def compatibility(source_version,target_version): return bool(source_version.strip() and target_version.strip())
    @classmethod
    def migrate(cls,payload,source_version,target_version,*,authorized=False):
        if not cls.compatibility(source_version,target_version): raise ValueError("incompatible migration versions")
        if authorized is not True: raise PermissionError("migration requires explicit authorization")
        return MigrationResult(source_version,target_version,True,True)
    @staticmethod
    def rollback_allowed(*,authorized): return authorized is True
    @staticmethod
    def grants_permission(): return False
