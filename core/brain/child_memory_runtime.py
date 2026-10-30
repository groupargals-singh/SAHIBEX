from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
import json
import sqlite3


class MemoryOperation(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    CLEAR = "clear"
    READ_CREDENTIAL = "read_credential"
    WRITE_CREDENTIAL = "write_credential"
    READ_MOTHER_PRIVATE = "read_mother_private"


class MemoryDecision(str, Enum):
    ALLOW = "allow"
    REQUIRE_AUTHORITY = "require_authority"
    DENY = "deny"


@dataclass(frozen=True)
class MemoryResult:
    allowed: bool
    decision: MemoryDecision
    operation: MemoryOperation
    reason: str


@dataclass
class ChildMemoryRuntime:
    child_brain_id: str
    memory_namespace: str
    _memory: dict[str, Any] = field(default_factory=dict)
    _credential_memory: dict[str, Any] = field(default_factory=dict)
    database_path: str | Path | None = None
    _db: sqlite3.Connection | None = field(default=None, init=False, repr=False, compare=False)

    VERSION = "1.1"

    def __post_init__(self) -> None:
        if not isinstance(self.child_brain_id, str) or not self.child_brain_id.strip():
            raise ValueError("child_brain_id_required")
        if not isinstance(self.memory_namespace, str) or not self.memory_namespace.strip():
            raise ValueError("memory_namespace_required")
        if self.database_path is None:
            return
        path = Path(self.database_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), timeout=10.0, check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS child_memory ("
            "child_brain_id TEXT NOT NULL, memory_namespace TEXT NOT NULL, "
            "memory_key TEXT NOT NULL, value_json TEXT NOT NULL, "
            "PRIMARY KEY(child_brain_id, memory_namespace, memory_key))"
        )
        self._db.commit()
        rows = self._db.execute(
            "SELECT memory_key, value_json FROM child_memory "
            "WHERE child_brain_id=? AND memory_namespace=?",
            (self.child_brain_id, self.memory_namespace),
        ).fetchall()
        self._memory.update({str(key): json.loads(value) for key, value in rows})

    def close(self) -> None:
        if self._db is not None:
            self._db.close()
            self._db = None

    def evaluate(
        self,
        operation: MemoryOperation,
        authority_approved: bool = False,
    ) -> MemoryResult:
        if not isinstance(operation, MemoryOperation):
            return MemoryResult(False, MemoryDecision.DENY, operation, "unknown memory operation")
        if operation in {MemoryOperation.READ, MemoryOperation.WRITE}:
            return MemoryResult(True, MemoryDecision.ALLOW, operation, "own child memory operation allowed")
        if operation in {MemoryOperation.DELETE, MemoryOperation.CLEAR, MemoryOperation.WRITE_CREDENTIAL}:
            if not authority_approved:
                return MemoryResult(False, MemoryDecision.REQUIRE_AUTHORITY, operation, "authority required for protected memory operation")
            return MemoryResult(True, MemoryDecision.REQUIRE_AUTHORITY, operation, "protected memory operation authorized")
        if operation == MemoryOperation.READ_CREDENTIAL:
            if not authority_approved:
                return MemoryResult(False, MemoryDecision.REQUIRE_AUTHORITY, operation, "credential memory requires authority")
            return MemoryResult(True, MemoryDecision.REQUIRE_AUTHORITY, operation, "credential memory access authorized")
        if operation == MemoryOperation.READ_MOTHER_PRIVATE:
            return MemoryResult(False, MemoryDecision.DENY, operation, "mother private memory is isolated")
        return MemoryResult(False, MemoryDecision.DENY, operation, "memory operation denied")

    def write(self, key: str, value: Any) -> MemoryResult:
        if not isinstance(key, str) or not key.strip():
            return MemoryResult(False, MemoryDecision.DENY, MemoryOperation.WRITE, "memory key is required")
        decision = self.evaluate(MemoryOperation.WRITE)
        try:
            encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        except (TypeError, ValueError):
            return MemoryResult(False, MemoryDecision.DENY, MemoryOperation.WRITE, "value_not_json_serializable")
        if decision.allowed:
            if self._db is not None:
                self._db.execute(
                    "INSERT INTO child_memory(child_brain_id,memory_namespace,memory_key,value_json) "
                    "VALUES(?,?,?,?) ON CONFLICT(child_brain_id,memory_namespace,memory_key) "
                    "DO UPDATE SET value_json=excluded.value_json",
                    (self.child_brain_id, self.memory_namespace, key, encoded),
                )
                self._db.commit()
            self._memory[key] = value
        return decision

    def read(self, key: str) -> Any:
        return self._memory.get(key)

    def contains(self, key: str) -> bool:
        return key in self._memory

    def delete(self, key: str, authority_approved: bool = False) -> MemoryResult:
        decision = self.evaluate(MemoryOperation.DELETE, authority_approved=authority_approved)
        if decision.allowed:
            self._memory.pop(key, None)
            if self._db is not None:
                self._db.execute(
                    "DELETE FROM child_memory WHERE child_brain_id=? AND memory_namespace=? AND memory_key=?",
                    (self.child_brain_id, self.memory_namespace, key),
                )
                self._db.commit()
        return decision

    def clear(self, authority_approved: bool = False) -> MemoryResult:
        decision = self.evaluate(MemoryOperation.CLEAR, authority_approved=authority_approved)
        if decision.allowed:
            self._memory.clear()
            if self._db is not None:
                self._db.execute(
                    "DELETE FROM child_memory WHERE child_brain_id=? AND memory_namespace=?",
                    (self.child_brain_id, self.memory_namespace),
                )
                self._db.commit()
        return decision

    def write_credential(self, key: str, value: Any, authority_approved: bool = False) -> MemoryResult:
        decision = self.evaluate(MemoryOperation.WRITE_CREDENTIAL, authority_approved=authority_approved)
        if decision.allowed and key:
            # Credentials deliberately remain in-memory. Durable secret storage needs
            # an approved encrypted secret store, not ordinary child-memory SQLite.
            self._credential_memory[key] = value
        return decision

    def read_credential(self, key: str, authority_approved: bool = False) -> Any:
        decision = self.evaluate(MemoryOperation.READ_CREDENTIAL, authority_approved=authority_approved)
        if not decision.allowed:
            return None
        return self._credential_memory.get(key)

    def can_access_mother_private_memory(self) -> bool:
        return False

    def memory_access_grants_authority(self) -> bool:
        return False

    def credentials_are_separate(self) -> bool:
        return self._memory is not self._credential_memory

    def memory_is_child_isolated(self) -> bool:
        return bool(self.child_brain_id and self.memory_namespace)

    def can_self_authorize_memory_access(self) -> bool:
        return False

    def grants_authority(self) -> bool:
        return False
