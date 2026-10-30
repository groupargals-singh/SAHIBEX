from __future__ import annotations

from core.research.memory_object import MemoryCandidate
from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


def test_restart_repairs_same_count_but_stale_knowledge_search_index(tmp_path):
    database = tmp_path / "task34-knowledge-index.db"
    storage = ResearchStorage(database)
    storage.save_knowledge(
        KnowledgeCandidate(
            knowledge_id="knowledge-1",
            statement="verified orchid taxonomy",
            confidence=0.95,
            verified=True,
        )
    )
    # Simulate a legacy writer/crash that committed the canonical record but
    # did not refresh its FTS companion. Counts remain equal.
    storage._connection.execute(
        "UPDATE knowledge_candidates SET data = json_set(data, '$.statement', ?) "
        "WHERE knowledge_id = ?",
        ("verified orchid taxonomy updated", "knowledge-1"),
    )
    storage._connection.commit()
    storage.close()

    restarted = ResearchStorage(database)
    assert [
        item.knowledge_id
        for item in restarted.retrieve_knowledge(
            "orchid taxonomy updated", verified_only=True
        )
    ] == ["knowledge-1"]
    restarted.close()


def test_restart_repairs_same_count_but_stale_memory_search_index(tmp_path):
    database = tmp_path / "task34-memory-index.db"
    storage = ResearchStorage(database)
    storage.save_memory(
        MemoryCandidate(
            memory_id="memory-1",
            content="remember sapphire protocol",
            memory_type="fact",
            source="verified_test",
            tags=["restart"],
        )
    )
    # Simulate a canonical-record update without a matching FTS update.
    # The canonical-table trigger marks the index dirty transactionally.
    storage._connection.execute(
        "UPDATE memories SET data = json_set(data, '$.content', ?) "
        "WHERE memory_id = ?",
        ("remember sapphire protocol updated", "memory-1"),
    )
    storage._connection.commit()
    storage.close()

    restarted = ResearchStorage(database)
    matches = restarted.retrieve_memories("sapphire protocol updated")
    assert [item.memory_id for item in matches] == ["memory-1"]
    restarted.close()
