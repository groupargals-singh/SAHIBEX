from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MotherDecisionContext:
    """
    Read-only cognitive context assembled by the SAHIBEX Mother Brain.

    This object contains contextual evidence only.
    It grants no authority and cannot execute protected actions.
    """

    request: str
    intent: str
    conversation_summary: dict[str, Any]
    memory_ids: tuple[str, ...]
    knowledge_ids: tuple[str, ...]
    memory_items: tuple[Any, ...]
    knowledge_items: tuple[Any, ...]
    retrieval_id: str
    retrieval_summary: str
    research_available: bool = True
    learning_available: bool = True
    working_memory_ids: tuple[str, ...] = ()
    working_memory_items: tuple[dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.request, str) or not self.request.strip():
            raise ValueError("request must be a non-empty string")

        if not isinstance(self.intent, str) or not self.intent.strip():
            raise ValueError("intent must be a non-empty string")

        if not isinstance(self.conversation_summary, dict):
            raise TypeError("conversation_summary must be a dict")

        if not isinstance(self.memory_ids, tuple):
            raise TypeError("memory_ids must be a tuple")

        if not isinstance(self.knowledge_ids, tuple):
            raise TypeError("knowledge_ids must be a tuple")

        if not isinstance(self.memory_items, tuple):
            raise TypeError("memory_items must be a tuple")

        if not isinstance(self.knowledge_items, tuple):
            raise TypeError("knowledge_items must be a tuple")
        if not isinstance(self.working_memory_ids, tuple):
            raise TypeError("working_memory_ids must be a tuple")
        if not isinstance(self.working_memory_items, tuple):
            raise TypeError("working_memory_items must be a tuple")
        if len(self.working_memory_ids) != len(self.working_memory_items):
            raise ValueError("working_memory_ids must correspond to working_memory_items")

        if len(self.memory_ids) != len(self.memory_items):
            raise ValueError(
                "memory_ids must correspond to memory_items"
            )

        if len(self.knowledge_ids) != len(self.knowledge_items):
            raise ValueError(
                "knowledge_ids must correspond to knowledge_items"
            )

        if not isinstance(self.retrieval_id, str):
            raise TypeError("retrieval_id must be a string")

        if not self.retrieval_id.strip():
            raise ValueError("retrieval_id must not be empty")

        if not isinstance(self.retrieval_summary, str):
            raise TypeError("retrieval_summary must be a string")

        if not self.retrieval_summary.strip():
            raise ValueError(
                "retrieval_summary must not be empty"
            )

        if not isinstance(self.research_available, bool):
            raise TypeError(
                "research_available must be a boolean"
            )

        if not isinstance(self.learning_available, bool):
            raise TypeError(
                "learning_available must be a boolean"
            )

    @property
    def memory_count(self) -> int:
        return len(self.memory_items)

    @property
    def knowledge_count(self) -> int:
        return len(self.knowledge_items)

    def summary(self) -> dict[str, Any]:
        return {
            "request": self.request,
            "intent": self.intent,
            "conversation": self.conversation_summary,
            "memory_count": self.memory_count,
            "knowledge_count": self.knowledge_count,
            "memory_ids": self.memory_ids,
            "knowledge_ids": self.knowledge_ids,
            "working_memory_count": len(self.working_memory_ids),
            "working_memory_ids": self.working_memory_ids,
            "working_memory_items": self.working_memory_items,
            "retrieval_id": self.retrieval_id,
            "retrieval_summary": self.retrieval_summary,
            "research_available": self.research_available,
            "learning_available": self.learning_available,
        }
