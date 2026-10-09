from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from core.research.memory_object import MemoryCandidate
from core.research.storage import ResearchStorage
from core.research.working_memory import WorkingMemory


@dataclass(frozen=True)
class MemoryWriteResult:
    memory_id: str
    memory_type: str
    persisted: bool
    activated: bool


class MemoryBrain:
    """Main-Brain memory facade.

    Owns memory orchestration while deliberately having no permission,
    credential, tool-execution, or constitution authority.
    """

    MAX_MEMORY_CONTENT_CHARS = 65536
    MAX_CONVERSATION_USER_CHARS = 8192
    MAX_CONVERSATION_ASSISTANT_CHARS = 16384

    def __init__(
        self,
        *,
        storage: ResearchStorage,
        working_memory: WorkingMemory | None = None,
    ) -> None:
        if not isinstance(storage, ResearchStorage):
            raise TypeError("storage must be ResearchStorage")
        self.storage = storage
        self.working_memory = working_memory or WorkingMemory()

    def remember(
        self,
        *,
        content: str,
        memory_type: str,
        source: str,
        importance: float = 0.5,
        confidence: float = 0.5,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        priority: float = 0.5,
        memory_id: str | None = None,
    ) -> MemoryWriteResult:
        normalized_content = content.strip()
        if len(normalized_content) > self.MAX_MEMORY_CONTENT_CHARS:
            normalized_content = (
                normalized_content[: self.MAX_MEMORY_CONTENT_CHARS]
                + "\n[MEMORY_CONTENT_TRUNCATED]"
            )

        memory = MemoryCandidate(
            memory_id=memory_id or f"memory-{uuid4()}",
            content=normalized_content,
            memory_type=memory_type.strip(),
            source=source.strip(),
            importance=importance,
            confidence=confidence,
            tags=list(tags or []),
            metadata=dict(metadata or {}),
        )
        self.storage.save_memory(memory)
        self.working_memory.activate(memory, priority=priority)
        return MemoryWriteResult(
            memory_id=memory.memory_id,
            memory_type=memory.memory_type,
            persisted=True,
            activated=True,
        )

    def remember_interaction(
        self,
        *,
        user_text: str,
        assistant_text: str,
        intent: str,
        action: str,
        verification_status: str,
    ) -> MemoryWriteResult:
        normalized_user = user_text.strip()
        normalized_assistant = assistant_text.strip()

        if normalized_user.startswith(
            "MOCK MODEL RESPONSE: Received request:"
        ):
            normalized_user = (
                "[MOCK_RESPONSE_ECHO_SUPPRESSED]"
            )

        if normalized_assistant.startswith(
            "MOCK MODEL RESPONSE: Received request:"
        ):
            normalized_assistant = (
                "[MOCK_RESPONSE_ECHO_SUPPRESSED]"
            )

        normalized_user = normalized_user[
            : self.MAX_CONVERSATION_USER_CHARS
        ]
        normalized_assistant = normalized_assistant[
            : self.MAX_CONVERSATION_ASSISTANT_CHARS
        ]

        return self.remember(
            content=(
                f"User: {normalized_user}\n"
                f"SAHIBEX: {normalized_assistant}"
            ),
            memory_type="conversation",
            source="master_brain",
            importance=0.65,
            confidence=1.0 if verification_status == "VERIFIED" else 0.55,
            tags=["conversation", intent.strip(), action.strip()],
            metadata={
                "intent": intent,
                "action": action,
                "verification_status": verification_status,
            },
            priority=0.75,
        )

    def retrieve(self, query: str, **filters: Any) -> list[MemoryCandidate]:
        return list(self.storage.retrieve_memories(query, **filters))

    def summary(self) -> dict[str, Any]:
        return {
            "persistent_storage": True,
            "working_memory": self.working_memory.summary(),
            "retrieval": True,
            "provenance": True,
            "confidence": True,
            "conflict_detection": True,
            "consolidation_proposals": True,
            "grants_permission": False,
            "executes_actions": False,
            "modifies_constitution": False,
            "overrides_human_authority": False,
        }

    @staticmethod
    def capability_contract() -> dict[str, bool]:
        return {
            "working_memory": True,
            "short_term_memory": True,
            "long_term_memory": True,
            "episodic_memory": True,
            "semantic_memory": True,
            "user_context_memory": True,
            "task_project_memory": True,
            "persistent_retrieval": True,
            "relevance_ranking": True,
            "conflict_detection": True,
            "verification": True,
            "consolidation": True,
            "permission_controlled_memory": True,
            "protected_execution": False,
            "permission_grant": False,
            "constitution_override": False,
        }
