from __future__ import annotations

import sqlite3

import pytest

from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


def test_knowledge_index_write_failure_rolls_back_canonical_update(tmp_path):
    database = tmp_path / "task35-knowledge-rollback.db"
    storage = ResearchStorage(database)
    original = KnowledgeCandidate(
        knowledge_id="stable-knowledge",
        statement="original verified claim",
        confidence=0.9,
        verified=True,
    )
    storage.save_knowledge(original)
    storage._connection.execute("DROP TABLE knowledge_search")
    storage._connection.commit()

    updated = KnowledgeCandidate(
        knowledge_id="stable-knowledge",
        statement="replacement claim must not partially persist",
        confidence=0.99,
        verified=True,
    )
    with pytest.raises(sqlite3.OperationalError, match="no such table: knowledge_search"):
        storage.save_knowledge(updated)

    # Restore the derived table after injecting a storage-layer failure.
    # A subsequent successful commit must not persist the failed update.
    storage._connection.execute(
        "CREATE VIRTUAL TABLE knowledge_search USING fts5(knowledge_id UNINDEXED, searchable_text)"
    )
    storage._connection.execute(
        "INSERT INTO knowledge_search(knowledge_id, searchable_text) VALUES (?, ?)",
        ("stable-knowledge", original.statement),
    )
    storage._connection.execute(
        "UPDATE fts_index_state SET dirty = 0 WHERE id = 1"
    )
    storage._connection.commit()
    storage.save_knowledge(
        KnowledgeCandidate(
            knowledge_id="unrelated-knowledge",
            statement="unrelated committed claim",
            confidence=0.8,
            verified=True,
        )
    )
    storage.close()

    recovered = ResearchStorage(database)
    assert recovered.get_knowledge("stable-knowledge") == original
    assert [
        item.knowledge_id
        for item in recovered.retrieve_knowledge(
            "original verified claim", verified_only=True
        )
    ] == ["stable-knowledge"]
    assert recovered.retrieve_knowledge(
        "replacement claim", verified_only=True
    ) == []
    recovered.close()


def test_memory_index_write_failure_rolls_back_canonical_update(tmp_path):
    from core.research.memory_object import MemoryCandidate

    database = tmp_path / "task35-memory-rollback.db"
    storage = ResearchStorage(database)
    original = MemoryCandidate(
        memory_id="stable-memory",
        content="original memory fact",
        memory_type="fact",
        source="verified_test",
        tags=["recovery"],
    )
    storage.save_memory(original)
    storage._connection.execute("DROP TABLE memory_search")
    storage._connection.commit()

    updated = MemoryCandidate(
        memory_id="stable-memory",
        content="replacement memory must not persist",
        memory_type="fact",
        source="verified_test",
        tags=["recovery"],
    )
    with pytest.raises(sqlite3.OperationalError, match="no such table: memory_search"):
        storage.save_memory(updated)

    storage._connection.execute(
        "CREATE VIRTUAL TABLE memory_search USING fts5(memory_id UNINDEXED, searchable_text)"
    )
    storage._connection.execute(
        "INSERT INTO memory_search(memory_id, searchable_text) VALUES (?, ?)",
        (
            "stable-memory",
            " ".join(
                [
                    original.content,
                    original.memory_type,
                    original.source,
                    " ".join(original.tags),
                    storage._serialize(original.metadata),
                ]
            ),
        ),
    )
    storage._connection.execute(
        "UPDATE fts_index_state SET dirty = 0 WHERE id = 1"
    )
    storage._connection.commit()
    storage.save_memory(
        MemoryCandidate(
            memory_id="unrelated-memory",
            content="unrelated safe memory",
            memory_type="fact",
            source="verified_test",
            tags=[],
        )
    )
    storage.close()

    recovered = ResearchStorage(database)
    assert recovered.get_memory("stable-memory") == original
    recovered_memory_ids = {
        item.memory_id
        for item in recovered.retrieve_memories("original memory fact")
    }
    assert "stable-memory" in recovered_memory_ids
    assert recovered.retrieve_memories("replacement memory") == []
    recovered.close()
