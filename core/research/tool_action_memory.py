from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


VERSION = "P2-TAM-1"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ToolActionMemory:
    """
    Immutable memory of a completed or attempted tool/action experience.

    This is a memory-only record.
    It has no execution, permission, retry, credential,
    constitution, or authority capability.
    """

    memory_id: str
    tool: str
    action: str
    context: str
    input_summary: str
    result_summary: str
    success: bool
    verification_status: str
    error: Optional[str]
    lesson: str
    source: str
    confidence: float = 0.5
    importance: float = 0.5
    provenance: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    occurred_at: datetime = field(default_factory=utc_now)
    recorded_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        required_strings = {
            "memory_id": self.memory_id,
            "tool": self.tool,
            "action": self.action,
            "context": self.context,
            "input_summary": self.input_summary,
            "result_summary": self.result_summary,
            "verification_status": self.verification_status,
            "lesson": self.lesson,
            "source": self.source,
        }

        for name, value in required_strings.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")

        if self.error is not None and not isinstance(self.error, str):
            raise TypeError("error must be a string or None.")

        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")

        if not isinstance(self.confidence, (int, float)):
            raise TypeError("confidence must be numeric.")

        if not isinstance(self.importance, (int, float)):
            raise TypeError("importance must be numeric.")

        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1.")

        if not 0.0 <= float(self.importance) <= 1.0:
            raise ValueError("importance must be between 0 and 1.")

        if not isinstance(self.provenance, dict):
            raise TypeError("provenance must be a dictionary.")

        if not isinstance(self.tags, list):
            raise TypeError("tags must be a list.")

        if any(
            not isinstance(tag, str) or not tag.strip()
            for tag in self.tags
        ):
            raise ValueError("tags must contain non-empty strings.")

        if self.success and self.error is not None:
            raise ValueError(
                "Successful tool action memory cannot contain an error."
            )

        if not self.success and not self.error:
            raise ValueError(
                "Failed tool action memory must preserve an error."
            )


class ToolActionMemoryStore:
    """
    Bounded in-process store for ToolActionMemory.

    Memory only:
    - no execution
    - no permission
    - no retry
    - no credential access
    - no constitution modification
    - no authority
    """

    VERSION = VERSION

    def __init__(self, capacity: int = 256) -> None:
        if not isinstance(capacity, int):
            raise TypeError("capacity must be an integer.")

        if capacity <= 0:
            raise ValueError("capacity must be greater than zero.")

        self.capacity = capacity
        self._memories: dict[str, ToolActionMemory] = {}

    def store(self, memory: ToolActionMemory) -> ToolActionMemory:
        if not isinstance(memory, ToolActionMemory):
            raise TypeError(
                "memory must be a ToolActionMemory instance."
            )

        if memory.memory_id in self._memories:
            raise ValueError(
                f"Tool action memory already exists: {memory.memory_id}"
            )

        self._memories[memory.memory_id] = memory
        self._evict_if_needed()

        return memory

    def get(self, memory_id: str) -> ToolActionMemory:
        try:
            return self._memories[memory_id]
        except KeyError as exc:
            raise KeyError(
                f"Unknown tool action memory: {memory_id}"
            ) from exc

    def contains(self, memory_id: str) -> bool:
        return memory_id in self._memories

    def by_tool(self, tool: str) -> List[ToolActionMemory]:
        if not isinstance(tool, str) or not tool.strip():
            raise ValueError("tool must be a non-empty string.")

        return sorted(
            (
                memory
                for memory in self._memories.values()
                if memory.tool == tool
            ),
            key=self._ranking_key,
            reverse=True,
        )

    def by_action(self, action: str) -> List[ToolActionMemory]:
        if not isinstance(action, str) or not action.strip():
            raise ValueError("action must be a non-empty string.")

        return sorted(
            (
                memory
                for memory in self._memories.values()
                if memory.action == action
            ),
            key=self._ranking_key,
            reverse=True,
        )

    def by_success(self, success: bool) -> List[ToolActionMemory]:
        if not isinstance(success, bool):
            raise TypeError("success must be a boolean.")

        return sorted(
            (
                memory
                for memory in self._memories.values()
                if memory.success is success
            ),
            key=self._ranking_key,
            reverse=True,
        )

    def by_verification(
        self,
        verification_status: str,
    ) -> List[ToolActionMemory]:
        if (
            not isinstance(verification_status, str)
            or not verification_status.strip()
        ):
            raise ValueError(
                "verification_status must be a non-empty string."
            )

        return sorted(
            (
                memory
                for memory in self._memories.values()
                if memory.verification_status == verification_status
            ),
            key=self._ranking_key,
            reverse=True,
        )

    def by_tag(self, tag: str) -> List[ToolActionMemory]:
        if not isinstance(tag, str) or not tag.strip():
            raise ValueError("tag must be a non-empty string.")

        return sorted(
            (
                memory
                for memory in self._memories.values()
                if tag in memory.tags
            ),
            key=self._ranking_key,
            reverse=True,
        )

    def search(self, text: str) -> List[ToolActionMemory]:
        if not isinstance(text, str):
            raise TypeError("text must be a string.")

        query = text.strip().lower()

        if not query:
            raise ValueError("Search text cannot be empty.")

        matches: List[ToolActionMemory] = []

        for memory in self._memories.values():
            searchable = " ".join(
                [
                    memory.tool,
                    memory.action,
                    memory.context,
                    memory.input_summary,
                    memory.result_summary,
                    memory.verification_status,
                    memory.error or "",
                    memory.lesson,
                    memory.source,
                    " ".join(memory.tags),
                ]
            ).lower()

            if query in searchable:
                matches.append(memory)

        return sorted(
            matches,
            key=self._ranking_key,
            reverse=True,
        )

    def lessons(self) -> List[str]:
        return [
            memory.lesson
            for memory in self.recent()
            if memory.lesson.strip()
        ]

    def effective_actions(
        self,
        minimum_confidence: float = 0.0,
    ) -> List[ToolActionMemory]:
        if not 0.0 <= minimum_confidence <= 1.0:
            raise ValueError(
                "minimum_confidence must be between 0 and 1."
            )

        return sorted(
            (
                memory
                for memory in self._memories.values()
                if memory.success
                and memory.confidence >= minimum_confidence
            ),
            key=self._ranking_key,
            reverse=True,
        )

    def recent(self, limit: int = 10) -> List[ToolActionMemory]:
        if not isinstance(limit, int):
            raise TypeError("limit must be an integer.")

        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        return sorted(
            self._memories.values(),
            key=lambda memory: (
                memory.occurred_at,
                memory.recorded_at,
                memory.memory_id,
            ),
            reverse=True,
        )[:limit]

    def all(self) -> List[ToolActionMemory]:
        return list(self._memories.values())

    def count(self) -> int:
        return len(self._memories)

    def remove(self, memory_id: str) -> ToolActionMemory:
        try:
            return self._memories.pop(memory_id)
        except KeyError as exc:
            raise KeyError(
                f"Unknown tool action memory: {memory_id}"
            ) from exc

    def clear(self) -> None:
        self._memories.clear()

    def summary(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "capacity": self.capacity,
            "memory_count": len(self._memories),
            "execution_allowed": False,
            "permission_allowed": False,
            "credential_access": False,
            "constitution_change_allowed": False,
            "authority": False,
        }

    def _ranking_key(
        self,
        memory: ToolActionMemory,
    ) -> tuple[float, float, float, datetime, str]:
        score = (
            (1.0 if memory.success else 0.0) * 0.35
            + memory.confidence * 0.30
            + memory.importance * 0.35
        )

        return (
            score,
            memory.confidence,
            memory.importance,
            memory.occurred_at,
            memory.memory_id,
        )

    def _evict_if_needed(self) -> None:
        while len(self._memories) > self.capacity:
            oldest = min(
                self._memories.values(),
                key=lambda memory: (
                    memory.occurred_at,
                    memory.recorded_at,
                    memory.memory_id,
                ),
            )

            del self._memories[oldest.memory_id]
