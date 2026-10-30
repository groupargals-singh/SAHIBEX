from __future__ import annotations

import sqlite3

import pytest

from core.research.memory_object import MemoryCandidate
from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


def _scoped_memory(memory_id: str, *, user_id: str, task_id: str, child_id: str) -> MemoryCandidate:
    return MemoryCandidate(
        memory_id=memory_id,
        content="Orion launch schedule project note",
        memory_type="project",
        source="test",
        tags=["orion"],
        metadata={
            "scope": {
                "user_id": user_id,
                "task_id": task_id,
                "child_brain_id": child_id,
                "memory_namespace": f"namespace-{child_id}",
            }
        },
    )


def test_scoped_memory_requires_exact_user_task_child_and_namespace() -> None:
    storage = ResearchStorage(":memory:")
    storage.save_memory(_scoped_memory("memory-a", user_id="user-a", task_id="task-a", child_id="child-a"))
    storage.save_memory(_scoped_memory("memory-b", user_id="user-b", task_id="task-b", child_id="child-b"))

    own = storage.retrieve_memories(
        "Orion launch schedule",
        user_id="user-a",
        task_id="task-a",
        child_brain_id="child-a",
        memory_namespace="namespace-child-a",
    )
    assert [item.memory_id for item in own] == ["memory-a"]

    wrong_user = storage.retrieve_memories(
        "Orion launch schedule",
        user_id="user-b",
        task_id="task-a",
        child_brain_id="child-a",
        memory_namespace="namespace-child-a",
    )
    assert wrong_user == []

    wrong_task = storage.retrieve_memories(
        "Orion launch schedule",
        user_id="user-a",
        task_id="task-b",
        child_brain_id="child-a",
        memory_namespace="namespace-child-a",
    )
    assert wrong_task == []

    # An unscoped retrieval must not expose records carrying scope metadata.
    assert storage.retrieve_memories("Orion launch schedule") == []
    storage.close()


def test_memory_retrieval_rejects_single_shared_keyword_for_unrelated_query() -> None:
    storage = ResearchStorage(":memory:")
    storage.save_memory(
        MemoryCandidate(
            memory_id="sahibex-project-memory",
            content=(
                "SAHIBEX is the user's own personal AI Main Brain / AI operating system, "
                "designed to provide cognitive support across all domains."
            ),
            memory_type="project",
            source="user",
            metadata={"project": "SAHIBEX"},
        )
    )

    unrelated = storage.retrieve_memories(
        "Hello SAHIBEX, reply in one short sentence."
    )
    assert unrelated == []

    exact_project_query = storage.retrieve_memories("SAHIBEX")
    assert [item.memory_id for item in exact_project_query] == ["sahibex-project-memory"]
    storage.close()


def test_malformed_scope_metadata_fails_closed() -> None:
    storage = ResearchStorage(":memory:")
    memory = _scoped_memory("memory-malformed", user_id="user-a", task_id="task-a", child_id="child-a")
    malformed = MemoryCandidate(
        memory_id=memory.memory_id,
        content=memory.content,
        memory_type=memory.memory_type,
        source=memory.source,
        tags=memory.tags,
        metadata={"scope": "not-a-scope-object"},
    )
    storage.save_memory(malformed)
    assert storage.retrieve_memories(
        "Orion launch schedule",
        user_id="user-a",
        task_id="task-a",
        child_brain_id="child-a",
        memory_namespace="namespace-child-a",
    ) == []
    storage.close()


def test_knowledge_canonical_and_search_index_write_roll_back_together() -> None:
    storage = ResearchStorage(":memory:")
    storage._connection.execute(
        """
        CREATE TRIGGER fail_knowledge_index_state_update
        BEFORE UPDATE ON fts_index_state
        BEGIN SELECT RAISE(ABORT, 'injected partial-write failure'); END
        """
    )
    storage._connection.commit()
    candidate = KnowledgeCandidate(
        knowledge_id="atomic-write-candidate",
        statement="Atomic write recovery marker",
        confidence=0.9,
        verified=False,
    )

    with pytest.raises(sqlite3.IntegrityError, match="injected partial-write failure"):
        storage.save_knowledge(candidate)

    assert storage.get_knowledge(candidate.knowledge_id) is None
    assert storage.retrieve_knowledge("Atomic write recovery marker") == []

    storage._connection.execute("DROP TRIGGER fail_knowledge_index_state_update")
    storage._connection.commit()
    storage.save_knowledge(candidate)
    assert storage.get_knowledge(candidate.knowledge_id) is not None
    assert [item.knowledge_id for item in storage.retrieve_knowledge("Atomic write recovery marker")] == [candidate.knowledge_id]
    storage.close()


def test_corrupt_database_initialization_fails_closed_without_replacing_bytes(tmp_path) -> None:
    database = tmp_path / "corrupt.sqlite3"
    corrupt_bytes = b"not a valid sqlite database; keep this file intact"
    database.write_bytes(corrupt_bytes)

    with pytest.raises(sqlite3.DatabaseError):
        ResearchStorage(database)

    assert database.read_bytes() == corrupt_bytes



def test_scoped_request_does_not_inherit_legacy_unscoped_memory() -> None:
    storage = ResearchStorage(":memory:")
    storage.save_memory(
        MemoryCandidate(
            memory_id="legacy-unscoped",
            content="Orion launch schedule legacy note",
            memory_type="project",
            source="legacy",
            tags=["orion"],
            metadata={},
        )
    )

    assert storage.retrieve_memories(
        "Orion launch schedule",
        user_id="user-a",
        task_id="task-a",
        child_brain_id="child-a",
        memory_namespace="namespace-child-a",
    ) == []
    # Legacy/global retrieval remains available only to an unscoped caller.
    assert [item.memory_id for item in storage.retrieve_memories("Orion launch schedule")] == [
        "legacy-unscoped"
    ]
    storage.close()


def test_partial_scope_metadata_fails_closed_for_incomplete_request() -> None:
    storage = ResearchStorage(":memory:")
    storage.save_memory(
        MemoryCandidate(
            memory_id="partial-scope",
            content="Orion launch schedule partially scoped note",
            memory_type="project",
            source="test",
            tags=["orion"],
            metadata={"scope": {"user_id": "user-a"}},
        )
    )

    assert storage.retrieve_memories(
        "Orion launch schedule",
        user_id="user-a",
    ) == []
    assert storage.retrieve_memories(
        "Orion launch schedule",
        user_id="user-a",
        task_id="task-a",
        child_brain_id="child-a",
        memory_namespace="namespace-child-a",
    ) == []
    storage.close()
