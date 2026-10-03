from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class MasterMemoryKnowledgeResult:
    """
    Result of integrating memory and knowledge references.

    This object represents contextual integration only.
    It does not modify, delete, or persist memory or knowledge.
    """

    success: bool
    memory_ids: list[str]
    knowledge_ids: list[str]
    summary: str
    integration_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")

        if not isinstance(self.memory_ids, list):
            raise TypeError("memory_ids must be a list.")

        if not self.memory_ids:
            raise ValueError(
                "memory_ids must contain at least one memory ID."
            )

        for memory_id in self.memory_ids:
            if not isinstance(memory_id, str):
                raise TypeError(
                    "every memory ID must be a string."
                )

            if not memory_id.strip():
                raise ValueError(
                    "memory IDs must not be empty."
                )

        if not isinstance(self.knowledge_ids, list):
            raise TypeError("knowledge_ids must be a list.")

        if not self.knowledge_ids:
            raise ValueError(
                "knowledge_ids must contain at least one knowledge ID."
            )

        for knowledge_id in self.knowledge_ids:
            if not isinstance(knowledge_id, str):
                raise TypeError(
                    "every knowledge ID must be a string."
                )

            if not knowledge_id.strip():
                raise ValueError(
                    "knowledge IDs must not be empty."
                )

        if not isinstance(self.summary, str):
            raise TypeError("summary must be a string.")

        if not self.summary.strip():
            raise ValueError(
                "summary must be a non-empty string."
            )

        if (
            not isinstance(self.integration_id, str)
            or not self.integration_id.strip()
        ):
            raise ValueError(
                "integration_id must be a non-empty string."
            )


class MasterMemoryKnowledgeIntegration:
    """
    Contract-level integration of memory and knowledge
    references for the master brain.

    This layer validates and normalizes references only.
    It does not modify persistent memory, delete knowledge,
    grant permissions, or execute external actions.
    """

    def integrate(
        self,
        *,
        memory_ids: list[str],
        knowledge_ids: list[str],
        summary: str,
    ) -> MasterMemoryKnowledgeResult:
        if not isinstance(memory_ids, list):
            raise TypeError("memory_ids must be a list.")

        if not memory_ids:
            raise ValueError(
                "memory_ids must contain at least one memory ID."
            )

        normalized_memory_ids: list[str] = []

        for memory_id in memory_ids:
            if not isinstance(memory_id, str):
                raise TypeError(
                    "every memory ID must be a string."
                )

            normalized = memory_id.strip()

            if not normalized:
                raise ValueError(
                    "memory IDs must not be empty."
                )

            if normalized not in normalized_memory_ids:
                normalized_memory_ids.append(normalized)

        if not isinstance(knowledge_ids, list):
            raise TypeError("knowledge_ids must be a list.")

        if not knowledge_ids:
            raise ValueError(
                "knowledge_ids must contain at least one knowledge ID."
            )

        normalized_knowledge_ids: list[str] = []

        for knowledge_id in knowledge_ids:
            if not isinstance(knowledge_id, str):
                raise TypeError(
                    "every knowledge ID must be a string."
                )

            normalized = knowledge_id.strip()

            if not normalized:
                raise ValueError(
                    "knowledge IDs must not be empty."
                )

            if normalized not in normalized_knowledge_ids:
                normalized_knowledge_ids.append(normalized)

        if not isinstance(summary, str):
            raise TypeError("summary must be a string.")

        if not summary.strip():
            raise ValueError(
                "summary must be a non-empty string."
            )

        return MasterMemoryKnowledgeResult(
            success=True,
            memory_ids=normalized_memory_ids,
            knowledge_ids=normalized_knowledge_ids,
            summary=summary,
        )
