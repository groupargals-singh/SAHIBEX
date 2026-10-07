from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.knowledge_graph_storage import KnowledgeGraphStorage
from core.research.knowledge_registry import Concept, Entity
from core.research.memory_association import MemoryAssociationEngine
from core.research.memory_association_storage import MemoryAssociationStorage
from core.research.persistent_memory_knowledge_graph import (
    PersistentMemoryKnowledgeGraph,
)


def main() -> None:
    print("SAHIBEX PHASE 3 #68 MEMORY-KNOWLEDGE INTEGRATION TEST")

    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "memory_knowledge.db"

        memory_storage = MemoryAssociationStorage(database_path)
        memory_engine = MemoryAssociationEngine()

        memory_id = "memory_python"
        concept_id = "concept_programming"
        entity_id = "entity_python"

        concept = Concept(
            concept_id=concept_id,
            name="Programming",
            concept_type="domain",
        )

        entity = Entity(
            entity_id=entity_id,
            name="Python",
            entity_type="programming_language",
        )

        # ---------------------------------------------------------
        # 1. Knowledge objects
        # ---------------------------------------------------------
        with KnowledgeGraphStorage(database_path) as knowledge:
            knowledge.save_concept(concept)
            knowledge.save_entity(entity)

            assert knowledge.get_concept(concept_id) == concept
            assert knowledge.get_entity(entity_id) == entity

            print("[PASS] knowledge objects available")

        # ---------------------------------------------------------
        # 2. Memory -> Concept association
        # ---------------------------------------------------------
        association = memory_engine.associate(
            source_memory_id=memory_id,
            target_id=concept_id,
            target_type="concept",
            association_type="memory_to_concept",
            strength=0.90,
            confidence=0.95,
        )

        memory_storage.save_association(association)

        print("[PASS] memory-to-concept association created")

        # ---------------------------------------------------------
        # 3. Exact association persistence
        # ---------------------------------------------------------
        stored = memory_storage.get_association(
            memory_id,
            concept_id,
            "concept",
            "memory_to_concept",
        )

        assert stored == association

        print("[PASS] association persistence")

        # ---------------------------------------------------------
        # 4. Forward retrieval: Memory -> Knowledge
        # ---------------------------------------------------------
        memory_links = memory_storage.associations_for_memory(
            memory_id
        )

        assert len(memory_links) == 1
        assert memory_links[0].target_id == concept_id
        assert memory_links[0].target_type == "concept"
        assert (
            memory_links[0].association_type
            == "memory_to_concept"
        )

        print("[PASS] memory-to-knowledge retrieval")

        # ---------------------------------------------------------
        # 5. Reverse retrieval: Knowledge -> Memory
        # ---------------------------------------------------------
        reverse = memory_storage.memories_for_target(
            concept_id,
            "concept",
        )

        assert reverse == (memory_id,)

        print("[PASS] reverse knowledge-to-memory lookup")

        # ---------------------------------------------------------
        # 6. Shared persistent Memory-Knowledge Graph
        # ---------------------------------------------------------
        with PersistentMemoryKnowledgeGraph(database_path) as graph:
            assert graph._knowledge_storage.get_concept(
                concept_id
            ) == concept

            assert graph._knowledge_storage.get_entity(
                entity_id
            ) == entity

            print("[PASS] shared persistent graph access")

        # ---------------------------------------------------------
        # 7. Restart persistence
        # ---------------------------------------------------------
        with MemoryAssociationStorage(database_path) as restarted:
            restored = restarted.memories_for_target(
                concept_id,
                "concept",
            )

            assert restored == (memory_id,)

            restored_associations = (
                restarted.associations_for_memory(
                    memory_id
                )
            )

            assert len(restored_associations) == 1
            assert (
                restored_associations[0].target_id
                == concept_id
            )
            assert (
                restored_associations[0].target_type
                == "concept"
            )

            print("[PASS] association survives restart")

        # ---------------------------------------------------------
        # 8. Empty memory identity protection
        # ---------------------------------------------------------
        try:
            memory_engine.associate(
                source_memory_id="",
                target_id=concept_id,
                target_type="concept",
                association_type="memory_to_concept",
                strength=0.5,
                confidence=0.5,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "empty memory ID should be rejected"
            )

        print("[PASS] empty memory identity protection")

        # ---------------------------------------------------------
        # 9. Empty knowledge identity protection
        # ---------------------------------------------------------
        try:
            memory_engine.associate(
                source_memory_id=memory_id,
                target_id="",
                target_type="concept",
                association_type="memory_to_concept",
                strength=0.5,
                confidence=0.5,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "empty target identity should be rejected"
            )

        print("[PASS] empty knowledge identity protection")

        # ---------------------------------------------------------
        # 10. Duplicate association protection
        # ---------------------------------------------------------
        duplicate = memory_engine.associate(
            source_memory_id=memory_id,
            target_id=concept_id,
            target_type="concept",
            association_type="memory_to_concept",
            strength=0.90,
            confidence=0.95,
        )

        try:
            memory_storage.save_association(duplicate)
        except Exception:
            pass

        assert memory_storage.association_count() == 1

        print("[PASS] duplicate association protection")

        # ---------------------------------------------------------
        # Final
        # ---------------------------------------------------------
        print(
            "SAHIBEX PHASE 3 #68 MEMORY-KNOWLEDGE "
            "INTEGRATION TEST: PASS"
        )


if __name__ == "__main__":
    main()
