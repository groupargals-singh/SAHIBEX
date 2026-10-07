from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.knowledge_graph_storage import (
    KnowledgeGraphStorage,
)
from core.research.knowledge_registry import Concept, Entity
from core.research.persistent_memory_knowledge_graph import (
    PersistentMemoryKnowledgeGraph,
    PERSISTENT_MEMORY_KNOWLEDGE_GRAPH_VERSION,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "sahibex_graph.db"

        knowledge = KnowledgeGraphStorage(
            database_path
        )

        concept = Concept(
            concept_id="concept-python",
            name="Python",
        concept_type="programming_language",
        )

        entity = Entity(
            entity_id="entity-sahibex",
            name="SAHIBEX",
            entity_type="system",
        )

        knowledge.save_concept(concept)
        knowledge.save_entity(entity)
        knowledge.close()

        graph = PersistentMemoryKnowledgeGraph(
            database_path
        )

        first = graph.link(
            memory_id="memory-001",
            target_id="concept-python",
            target_type="concept",
            strength=0.9,
            confidence=0.95,
            metadata={"shared": True},
        )

        check(
            first.association.source_memory_id
            == "memory-001",
            "memory identity persisted",
        )

        check(
            first.association.target_id
            == "concept-python",
            "concept identity preserved",
        )

        check(
            first.target_exists is True,
            "existing knowledge concept detected",
        )

        second = graph.link(
            memory_id="memory-002",
            target_id="concept-python",
            target_type="concept",
        )

        check(
            second.target_exists is True,
            "second memory resolves shared concept",
        )

        entity_link = graph.link(
            memory_id="memory-003",
            target_id="entity-sahibex",
            target_type="entity",
        )

        check(
            entity_link.target_exists is True,
            "existing knowledge entity detected",
        )

        memories = graph.memories_for_target(
            "concept-python",
            "concept",
        )

        check(
            memories == (
                "memory-001",
                "memory-002",
            ),
            "shared concept reverse lookup works",
        )

        links = graph.links_for_memory(
            "memory-001"
        )

        check(
            len(links) == 1,
            "memory link retrieval works",
        )

        duplicate = graph.link(
            memory_id="memory-001",
            target_id="concept-python",
            target_type="concept",
        )

        check(
            duplicate.created is False,
            "duplicate persistent link blocked",
        )

        check(
            graph.association_count() == 3,
            "persistent association count is correct",
        )

        summary = graph.summary()

        check(
            summary["version"]
            == PERSISTENT_MEMORY_KNOWLEDGE_GRAPH_VERSION,
            "integration version is correct",
        )

        check(
            summary["persistent"] is True,
            "persistent integration enabled",
        )

        check(
            summary["shared_sqlite_database"] is True,
            "shared SQLite database architecture works",
        )

        check(
            summary["knowledge_graph_connected"] is True,
            "knowledge graph connection is enabled",
        )

        check(
            summary["stores_links_not_duplicate_content"]
            is True,
            "links stored without content duplication",
        )

        check(
            summary["grants_permission"] is False,
            "integration grants no permission",
        )

        check(
            summary["executes_actions"] is False,
            "integration executes no actions",
        )

        check(
            summary["modifies_constitution"] is False,
            "integration cannot modify constitution",
        )

        graph.close()

        restarted = PersistentMemoryKnowledgeGraph(
            database_path
        )

        restored = restarted.memories_for_target(
            "concept-python",
            "concept",
        )

        check(
            restored == (
                "memory-001",
                "memory-002",
            ),
            "associations survive restart",
        )

        restored_links = restarted.links_for_memory(
            "memory-003"
        )

        check(
            len(restored_links) == 1,
            "entity association survives restart",
        )

        restarted.close()

        blocked = False

        try:
            PersistentMemoryKnowledgeGraph(
                database_path
            ).link(
                memory_id="memory-004",
                target_id="invalid-target",
                target_type="invalid",
            )
        except ValueError:
            blocked = True

        check(
            blocked,
            "invalid target type blocked",
        )

        print(
            "SAHIBEX PHASE 2 PERSISTENT "
            "MEMORY-KNOWLEDGE GRAPH INTEGRATION TEST: PASS"
        )


if __name__ == "__main__":
    main()
