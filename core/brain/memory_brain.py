
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
    status: str = "PERSISTED"
    reason: str = ""


class MemoryBrain:
    """Main-Brain memory facade.

    Owns memory orchestration while deliberately having no permission,
    credential, tool-execution, or constitution authority.
    """

    MAX_MEMORY_CONTENT_CHARS = 65536
    MAX_CONVERSATION_USER_CHARS = 8192
    MAX_CONVERSATION_ASSISTANT_CHARS = 16384

    VERIFIED_FACT_MEMORY_TYPES = frozenset({
        "research_fact",
        "learned_fact",
        "research_knowledge",
        "learned_knowledge",
        "verified_knowledge",
        "web_fact",
        "factual_knowledge",
        "semantic_fact",
    })

    @staticmethod
    def _has_provenance_ids(value: Any) -> bool:
        return (
            isinstance(value, (list, tuple, set, frozenset))
            and bool(value)
            and all(
                isinstance(item, str) and item.strip()
                for item in value
            )
        )

    @classmethod
    def _requires_verified_fact_provenance(
        cls,
        memory_type: str,
        source: str,
        metadata: dict[str, Any],
    ) -> bool:
        normalized_type = memory_type.strip().lower()

        # Explicitly user-confirmed project facts retain their existing path.
        if (
            normalized_type == "project_fact"
            and source.strip().lower() == "user-confirmed"
            and metadata.get("verified_by") == "user"
        ):
            return False

        if normalized_type in cls.VERIFIED_FACT_MEMORY_TYPES:
            return True

        # Fail closed for factual aliases not yet registered above.
        return any(
            token in normalized_type
            for token in (
                "_fact",
                "fact_",
                "_knowledge",
                "knowledge_",
                "semantic",
            )
        )

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

        normalized_type = memory_type.strip().lower()
        normalized_metadata = dict(metadata or {})
        candidate_memory_id = memory_id or f"memory-{uuid4()}"

        requires_provenance = self._requires_verified_fact_provenance(
            normalized_type,
            source,
            normalized_metadata,
        )

        evidence_ids = normalized_metadata.get("evidence_ids")
        source_ids = normalized_metadata.get("source_ids")

        if requires_provenance:
            verification_status = str(
                normalized_metadata.get("verification_status", "")
            ).strip().upper()

            provenance_ok = (
                normalized_metadata.get("verified") is True
                and verification_status == "VERIFIED"
                and self._has_provenance_ids(evidence_ids)
                and self._has_provenance_ids(source_ids)
            )

            normalized_evidence_ids: list[str] = []
            normalized_source_ids: list[str] = []

            if provenance_ok:
                normalized_evidence_ids = [
                    item.strip() for item in evidence_ids
                ]
                normalized_source_ids = [
                    item.strip() for item in source_ids
                ]

                provenance_ok = (
                    all(normalized_evidence_ids)
                    and all(normalized_source_ids)
                )

            if provenance_ok:
                # Each referenced evidence and source must actually exist.
                stored_sources = {
                    source_id: self.storage.get_source(source_id)
                    for source_id in normalized_source_ids
                }
                stored_evidence = {
                    evidence_id: self.storage.get_evidence(evidence_id)
                    for evidence_id in normalized_evidence_ids
                }

                provenance_ok = (
                    all(item is not None for item in stored_sources.values())
                    and all(item is not None for item in stored_evidence.values())
                )

                # Each evidence item must refer to one of the declared sources.
                if provenance_ok:
                    provenance_ok = all(
                        getattr(evidence, "source_id", None)
                        in stored_sources
                        for evidence in stored_evidence.values()
                    )

            if not provenance_ok:
                return MemoryWriteResult(
                    memory_id=candidate_memory_id,
                    memory_type=normalized_type,
                    persisted=False,
                    activated=False,
                    status="REJECTED_UNVERIFIED_FACT",
                    reason=(
                        "Factual memory requires VERIFIED metadata, "
                        "stored evidence, and stored source provenance "
                        "with matching evidence-to-source links."
                    ),
                )

            # Store normalized JSON-friendly ID lists in memory metadata.
            normalized_metadata["evidence_ids"] = normalized_evidence_ids
            normalized_metadata["source_ids"] = normalized_source_ids

        # Build the memory object before attempting persistence.
        memory = MemoryCandidate(
            memory_id=candidate_memory_id,
            content=normalized_content,
            memory_type=normalized_type,
            source=source.strip(),
            importance=importance,
            confidence=confidence,
            tags=list(tags or []),
            metadata=normalized_metadata,
        )

        self.storage.save_memory(memory)

        # Record verification before activating factual memory.
        # If this raises an error, activation will not occur.
        if requires_provenance:
            self.storage.record_memory_verification(
                memory_id=memory.memory_id,
                status="VERIFIED",
                evidence_id=normalized_evidence_ids[0],
                reason=(
                    "Verified factual memory has validated stored "
                    "evidence and source provenance."
                ),
            )

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
            normalized_user = "[MOCK_RESPONSE_ECHO_SUPPRESSED]"

        if normalized_assistant.startswith(
            "MOCK MODEL RESPONSE: Received request:"
        ):
            normalized_assistant = "[MOCK_RESPONSE_ECHO_SUPPRESSED]"

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
            confidence=(
                1.0 if verification_status == "VERIFIED" else 0.55
            ),
            tags=["conversation", intent.strip(), action.strip()],
            metadata={
                "intent": intent,
                "action": action,
                "verification_status": verification_status,
            },
            priority=0.75,
        )

    @classmethod
    def _is_memory_trusted_for_retrieval(
        cls,
        memory: MemoryCandidate,
        storage: ResearchStorage,
    ) -> bool:
        memory_type = str(getattr(memory, "memory_type", "")).strip().lower()
        source = str(getattr(memory, "source", ""))
        metadata = getattr(memory, "metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        # Ordinary memories and explicitly user-confirmed project facts
        # retain their existing retrieval behavior.
        if not cls._requires_verified_fact_provenance(
            memory_type, source, metadata
        ):
            return True

        if metadata.get("verified") is not True:
            return False
        if str(metadata.get("verification_status", "")).strip().upper() != "VERIFIED":
            return False

        evidence_ids = metadata.get("evidence_ids")
        source_ids = metadata.get("source_ids")
        if not cls._has_provenance_ids(evidence_ids):
            return False
        if not cls._has_provenance_ids(source_ids):
            return False

        normalized_evidence_ids = [item.strip() for item in evidence_ids]
        normalized_source_ids = [item.strip() for item in source_ids]

        if not all(normalized_evidence_ids) or not all(normalized_source_ids):
            return False

        verification = storage.get_memory_verification(memory.memory_id)
        if not verification:
            return False
        if str(verification.get("status", "")).strip().upper() != "VERIFIED":
            return False

        registry_evidence_id = str(verification.get("evidence_id", "")).strip()
        if not registry_evidence_id or registry_evidence_id not in normalized_evidence_ids:
            return False

        stored_sources = {
            source_id: storage.get_source(source_id)
            for source_id in normalized_source_ids
        }
        if any(source_record is None for source_record in stored_sources.values()):
            return False

        stored_evidence = {
            evidence_id: storage.get_evidence(evidence_id)
            for evidence_id in normalized_evidence_ids
        }
        if any(evidence_record is None for evidence_record in stored_evidence.values()):
            return False

        for evidence_record in stored_evidence.values():
            if evidence_record.source_id not in stored_sources:
                return False
            if stored_sources[evidence_record.source_id] is None:
                return False
            if evidence_record.supports is not True:
                return False

        return True

    def retrieve(
        self,
        query: str,
        **filters: Any,
    ) -> list[MemoryCandidate]:
        memories = self.storage.retrieve_memories(query, **filters)
        return [
            memory
            for memory in memories
            if self._is_memory_trusted_for_retrieval(memory, self.storage)
        ]

    def summary(self) -> dict[str, Any]:
        return {
            "persistent_storage": True,
            "working_memory": self.working_memory.summary(),
            "retrieval": True,
            "provenance": True,
            "verified_fact_provenance_required": True,
            "unverified_factual_memory_blocked": True,
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
            "unverified_factual_memory_blocked": True,
            "verified_fact_provenance_required": True,
            "protected_execution": False,
            "permission_grant": False,
            "constitution_override": False,
        }
