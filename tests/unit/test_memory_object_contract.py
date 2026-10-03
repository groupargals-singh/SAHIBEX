"""
SAHIBEX 6I-1 MEMORY OBJECT CONTRACT TEST

Validates the foundational contract for a SAHIBEX memory object.
This test intentionally does not require production memory storage yet.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass(frozen=True)
class MemoryCandidate:
    memory_id: str
    content: str
    memory_type: str
    source: str
    importance: float = 0.5
    confidence: float = 0.5
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    last_accessed_at: datetime | None = None

    def __post_init__(self):
        if not self.memory_id.strip():
            raise ValueError("memory_id cannot be empty")

        if not self.content.strip():
            raise ValueError("content cannot be empty")

        if not self.memory_type.strip():
            raise ValueError("memory_type cannot be empty")

        if not self.source.strip():
            raise ValueError("source cannot be empty")

        if not 0.0 <= self.importance <= 1.0:
            raise ValueError("importance must be between 0 and 1")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if not isinstance(self.tags, list):
            raise ValueError("tags must be a list")

        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    print("SAHIBEX 6I-1 MEMORY OBJECT CONTRACT TEST")

    now = datetime.now(timezone.utc)

    memory = MemoryCandidate(
        memory_id="mem-001",
        content="User prefers step-by-step development instructions.",
        memory_type="USER_PREFERENCE",
        source="user",
        importance=0.9,
        confidence=0.95,
        tags=["preference", "development"],
        metadata={"domain": "software"},
        created_at=now,
        updated_at=now,
        last_accessed_at=now,
    )

    check(
        memory.memory_id == "mem-001",
        "required memory ID",
    )

    check(
        memory.content == "User prefers step-by-step development instructions.",
        "memory content preserved",
    )

    check(
        memory.memory_type == "USER_PREFERENCE",
        "memory type preserved",
    )

    check(
        memory.source == "user",
        "memory source preserved",
    )

    check(
        memory.importance == 0.9,
        "importance preserved",
    )

    check(
        memory.confidence == 0.95,
        "confidence preserved",
    )

    check(
        memory.tags == ["preference", "development"],
        "memory tags preserved",
    )

    check(
        memory.metadata["domain"] == "software",
        "memory metadata preserved",
    )

    check(
        isinstance(memory.created_at, datetime),
        "created timestamp",
    )

    check(
        isinstance(memory.updated_at, datetime),
        "updated timestamp",
    )

    check(
        isinstance(memory.last_accessed_at, datetime),
        "last accessed timestamp",
    )

    # Default values
    default_memory = MemoryCandidate(
        memory_id="mem-default",
        content="Default memory.",
        memory_type="FACT",
        source="system",
    )

    check(
        default_memory.importance == 0.5,
        "default importance",
    )

    check(
        default_memory.confidence == 0.5,
        "default confidence",
    )

    check(
        default_memory.tags == [],
        "default tags",
    )

    check(
        default_memory.metadata == {},
        "default metadata",
    )

    check(
        default_memory.last_accessed_at is None,
        "default last accessed timestamp",
    )

    # Empty ID protection
    try:
        MemoryCandidate(
            memory_id="",
            content="Valid content",
            memory_type="FACT",
            source="system",
        )
        raise AssertionError("empty memory ID was accepted")
    except ValueError:
        print("[PASS] empty memory ID protection")

    # Empty content protection
    try:
        MemoryCandidate(
            memory_id="mem-invalid",
            content="",
            memory_type="FACT",
            source="system",
        )
        raise AssertionError("empty memory content was accepted")
    except ValueError:
        print("[PASS] empty memory content protection")

    # Empty type protection
    try:
        MemoryCandidate(
            memory_id="mem-invalid",
            content="Valid content",
            memory_type="",
            source="system",
        )
        raise AssertionError("empty memory type was accepted")
    except ValueError:
        print("[PASS] empty memory type protection")

    # Empty source protection
    try:
        MemoryCandidate(
            memory_id="mem-invalid",
            content="Valid content",
            memory_type="FACT",
            source="",
        )
        raise AssertionError("empty memory source was accepted")
    except ValueError:
        print("[PASS] empty memory source protection")

    # Importance validation
    try:
        MemoryCandidate(
            memory_id="mem-invalid",
            content="Valid content",
            memory_type="FACT",
            source="system",
            importance=1.1,
        )
        raise AssertionError("invalid importance was accepted")
    except ValueError:
        print("[PASS] importance range validation")

    # Confidence validation
    try:
        MemoryCandidate(
            memory_id="mem-invalid",
            content="Valid content",
            memory_type="FACT",
            source="system",
            confidence=-0.1,
        )
        raise AssertionError("invalid confidence was accepted")
    except ValueError:
        print("[PASS] confidence range validation")

    # Frozen / immutable contract
    try:
        memory.content = "modified"
        raise AssertionError("memory object is mutable")
    except Exception:
        print("[PASS] memory immutability")

    print("SAHIBEX 6I-1 MEMORY OBJECT CONTRACT TEST: PASS")


if __name__ == "__main__":
    main()
