from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class KnowledgeOperation(str, Enum):
    READ = "read"
    STORE = "store"
    RESEARCH = "research"
    LEARN = "learn"
    ANALYZE = "analyze"
    VERIFY = "verify"
    MARK_TRUSTED = "mark_trusted"
    DELETE = "delete"


class KnowledgeDecision(str, Enum):
    ALLOW = "allow"
    REQUIRE_AUTHORITY = "require_authority"
    REQUIRE_VERIFICATION = "require_verification"
    DENY = "deny"


@dataclass(frozen=True)
class KnowledgeResult:
    allowed: bool
    decision: KnowledgeDecision
    operation: KnowledgeOperation
    reason: str


@dataclass
class KnowledgeRecord:
    key: str
    value: Any
    verified: bool = False
    trusted: bool = False
    source: str = ""


@dataclass
class ChildKnowledgeRuntime:
    child_brain_id: str
    knowledge_namespace: str

    _knowledge: dict[str, KnowledgeRecord] = field(default_factory=dict)

    VERSION = "1.0"

    def evaluate(
        self,
        operation: KnowledgeOperation,
        verified: bool = False,
        authority_approved: bool = False,
    ) -> KnowledgeResult:
        if not isinstance(operation, KnowledgeOperation):
            return KnowledgeResult(
                False,
                KnowledgeDecision.DENY,
                operation,
                "unknown knowledge operation",
            )

        if operation in {
            KnowledgeOperation.RESEARCH,
            KnowledgeOperation.LEARN,
            KnowledgeOperation.ANALYZE,
            KnowledgeOperation.READ,
            KnowledgeOperation.VERIFY,
        }:
            return KnowledgeResult(
                True,
                KnowledgeDecision.ALLOW,
                operation,
                "independent knowledge operation allowed",
            )

        if operation == KnowledgeOperation.STORE:
            if not verified:
                return KnowledgeResult(
                    False,
                    KnowledgeDecision.REQUIRE_VERIFICATION,
                    operation,
                    "knowledge must be verified before trusted storage",
                )

            return KnowledgeResult(
                True,
                KnowledgeDecision.ALLOW,
                operation,
                "verified knowledge may be stored",
            )

        if operation == KnowledgeOperation.MARK_TRUSTED:
            if not verified:
                return KnowledgeResult(
                    False,
                    KnowledgeDecision.REQUIRE_VERIFICATION,
                    operation,
                    "verification required before trust",
                )

            if not authority_approved:
                return KnowledgeResult(
                    False,
                    KnowledgeDecision.REQUIRE_AUTHORITY,
                    operation,
                    "authority required to mark knowledge trusted",
                )

            return KnowledgeResult(
                True,
                KnowledgeDecision.REQUIRE_AUTHORITY,
                operation,
                "verified knowledge may be marked trusted",
            )

        if operation == KnowledgeOperation.DELETE:
            if not authority_approved:
                return KnowledgeResult(
                    False,
                    KnowledgeDecision.REQUIRE_AUTHORITY,
                    operation,
                    "authority required for knowledge deletion",
                )

            return KnowledgeResult(
                True,
                KnowledgeDecision.REQUIRE_AUTHORITY,
                operation,
                "knowledge deletion authorized",
            )

        return KnowledgeResult(
            False,
            KnowledgeDecision.DENY,
            operation,
            "knowledge operation denied",
        )

    def store(
        self,
        key: str,
        value: Any,
        source: str,
        verified: bool = False,
    ) -> KnowledgeResult:
        if not key or not source:
            return KnowledgeResult(
                False,
                KnowledgeDecision.DENY,
                KnowledgeOperation.STORE,
                "key and source are required",
            )

        decision = self.evaluate(
            KnowledgeOperation.STORE,
            verified=verified,
        )

        if decision.allowed:
            self._knowledge[key] = KnowledgeRecord(
                key=key,
                value=value,
                verified=True,
                trusted=False,
                source=source,
            )

        return decision

    def read(self, key: str) -> Any:
        record = self._knowledge.get(key)
        if record is None:
            return None

        return record.value

    def get_record(self, key: str) -> KnowledgeRecord | None:
        return self._knowledge.get(key)

    def mark_trusted(
        self,
        key: str,
        authority_approved: bool = False,
    ) -> KnowledgeResult:
        record = self._knowledge.get(key)

        if record is None:
            return KnowledgeResult(
                False,
                KnowledgeDecision.DENY,
                KnowledgeOperation.MARK_TRUSTED,
                "knowledge record not found",
            )

        decision = self.evaluate(
            KnowledgeOperation.MARK_TRUSTED,
            verified=record.verified,
            authority_approved=authority_approved,
        )

        if decision.allowed:
            record.trusted = True

        return decision

    def delete(
        self,
        key: str,
        authority_approved: bool = False,
    ) -> KnowledgeResult:
        decision = self.evaluate(
            KnowledgeOperation.DELETE,
            authority_approved=authority_approved,
        )

        if decision.allowed:
            self._knowledge.pop(key, None)

        return decision

    def is_trusted(self, key: str) -> bool:
        record = self._knowledge.get(key)
        return bool(record and record.trusted)

    def can_research_independently(self) -> bool:
        return True

    def can_learn_independently(self) -> bool:
        return True

    def can_analyze_independently(self) -> bool:
        return True

    def can_verify_independently(self) -> bool:
        return True

    def external_model_is_authority(self) -> bool:
        return False

    def external_tool_is_authority(self) -> bool:
        return False

    def knowledge_equals_authority(self) -> bool:
        return False

    def unknown_knowledge_is_trusted(self) -> bool:
        return False
