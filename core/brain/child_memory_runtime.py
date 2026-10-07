from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


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

    VERSION = "1.0"

    def evaluate(
        self,
        operation: MemoryOperation,
        authority_approved: bool = False,
    ) -> MemoryResult:
        if not isinstance(operation, MemoryOperation):
            return MemoryResult(
                False,
                MemoryDecision.DENY,
                operation,
                "unknown memory operation",
            )

        if operation in {
            MemoryOperation.READ,
            MemoryOperation.WRITE,
        }:
            return MemoryResult(
                True,
                MemoryDecision.ALLOW,
                operation,
                "own child memory operation allowed",
            )

        if operation in {
            MemoryOperation.DELETE,
            MemoryOperation.CLEAR,
            MemoryOperation.WRITE_CREDENTIAL,
        }:
            if not authority_approved:
                return MemoryResult(
                    False,
                    MemoryDecision.REQUIRE_AUTHORITY,
                    operation,
                    "authority required for protected memory operation",
                )

            return MemoryResult(
                True,
                MemoryDecision.REQUIRE_AUTHORITY,
                operation,
                "protected memory operation authorized",
            )

        if operation == MemoryOperation.READ_CREDENTIAL:
            if not authority_approved:
                return MemoryResult(
                    False,
                    MemoryDecision.REQUIRE_AUTHORITY,
                    operation,
                    "credential memory requires authority",
                )

            return MemoryResult(
                True,
                MemoryDecision.REQUIRE_AUTHORITY,
                operation,
                "credential memory access authorized",
            )

        if operation == MemoryOperation.READ_MOTHER_PRIVATE:
            return MemoryResult(
                False,
                MemoryDecision.DENY,
                operation,
                "mother private memory is isolated",
            )

        return MemoryResult(
            False,
            MemoryDecision.DENY,
            operation,
            "memory operation denied",
        )

    def write(self, key: str, value: Any) -> MemoryResult:
        if not key:
            return MemoryResult(
                False,
                MemoryDecision.DENY,
                MemoryOperation.WRITE,
                "memory key is required",
            )

        decision = self.evaluate(MemoryOperation.WRITE)

        if decision.allowed:
            self._memory[key] = value

        return decision

    def read(self, key: str) -> Any:
        return self._memory.get(key)

    def contains(self, key: str) -> bool:
        return key in self._memory

    def delete(
        self,
        key: str,
        authority_approved: bool = False,
    ) -> MemoryResult:
        decision = self.evaluate(
            MemoryOperation.DELETE,
            authority_approved=authority_approved,
        )

        if decision.allowed:
            self._memory.pop(key, None)

        return decision

    def clear(
        self,
        authority_approved: bool = False,
    ) -> MemoryResult:
        decision = self.evaluate(
            MemoryOperation.CLEAR,
            authority_approved=authority_approved,
        )

        if decision.allowed:
            self._memory.clear()

        return decision

    def write_credential(
        self,
        key: str,
        value: Any,
        authority_approved: bool = False,
    ) -> MemoryResult:
        decision = self.evaluate(
            MemoryOperation.WRITE_CREDENTIAL,
            authority_approved=authority_approved,
        )

        if decision.allowed and key:
            self._credential_memory[key] = value

        return decision

    def read_credential(
        self,
        key: str,
        authority_approved: bool = False,
    ) -> Any:
        decision = self.evaluate(
            MemoryOperation.READ_CREDENTIAL,
            authority_approved=authority_approved,
        )

        if not decision.allowed:
            return None

        return self._credential_memory.get(key)

    def can_access_mother_private_memory(self) -> bool:
        return False

    def memory_access_grants_authority(self) -> bool:
        return False

    def credentials_are_separate(self) -> bool:
        return self._credential_memory is not self._memory

    def memory_is_child_isolated(self) -> bool:
        return True

    def can_self_authorize_memory_access(self) -> bool:
        return False

    def grants_authority(self) -> bool:
        return False
