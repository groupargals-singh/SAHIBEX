from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class MemoryCandidate:
    """
    Foundational memory object for SAHIBEX.

    A memory represents information retained for future reasoning,
    personalization, retrieval, or context reconstruction.
    """

    memory_id: str
    content: str
    memory_type: str
    source: str

    importance: float = 0.5
    confidence: float = 0.5

    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    last_accessed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.memory_id.strip():
            raise ValueError("memory_id cannot be empty")

        if not self.content.strip():
            raise ValueError("memory content cannot be empty")

        if not self.memory_type.strip():
            raise ValueError("memory_type cannot be empty")

        if not self.source.strip():
            raise ValueError("memory source cannot be empty")

        if not 0.0 <= self.importance <= 1.0:
            raise ValueError("importance must be between 0 and 1")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if not isinstance(self.tags, list):
            raise ValueError("tags must be a list")

        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")
