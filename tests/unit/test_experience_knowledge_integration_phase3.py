from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.experience_memory import (
    ExperienceMemory,
    ExperienceMemoryStore,
)
from core.research.knowledge_graph_storage import KnowledgeGraphStorage
from core.research.knowledge_registry import Concept, Entity
from core.research.memory_association_storage import (
    MemoryAssociationStorage,
)
from core.research.persistent_memory_knowledge_graph import (
    PersistentMemoryKnowledgeGraph,
)


def main() -> None:
    print("SAHIBEX PHASE 3 #69 EXPERIENCE-KNOWLEDGE INTEGRATION TEST")

    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "experience_knowledge.db"

        experience_id = "experience_python_task"
        concept_id = "concept_programming"
        entity_id = "entity_python"

        # ---------------------------------------------------------
        # 1. Create Experience Memory
        # ---------------------------------------------------------
        experience = ExperienceMemory(
            experience_id=experience_id,
            task="Build a Python program",
            context="SAHIBEX development",
            action_taken="Implemented and tested Python code",
            outcome="Program passed verification",
            lesson="Verify implementation with focused tests",
            source="sahibex",
            success=True,
            confidence=0.95,
            importance=0.90,
            tags=["python", "development", "verification"],
        )

        experience_store = ExperienceMemoryStore()
        stored_experience = experience_store.store(experience)

        assert stored_experience == experience
        assert experience_store.get(experience_id) == experience

        print("[PASS] experience memory available")

        # ---------------------------------------------------------
        # 2. Create Knowledge objects
        # ---------------------------------------------------------
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

        with KnowledgeGraphStorage(database_path) as knowledge:
            knowledge.save_concept(concept)
            knowledge.save_entity(entity)

            assert knowledge.get_concept(concept_id) == concept
            assert knowledge.get_entity(entity_id) == entity

            print("[PASS] knowledge objects available")

        # ---------------------------------------------------------
        # 3. Experience -> Concept persistent link
        # ---------------------------------------------------------
        with PersistentMemoryKnowledgeGraph(database_path) as graph:
            concept_link = graph.link(
                experience_id,
                concept_id,
                "concept",
                strength=0.90,
                confidence=0.95,
                metadata={
                    "origin": "experience",
                    "relationship": "learned_from",
                },
            )

            assert concept_link.association.target_id == concept_id
            assert (
                concept_link.association.target_type
                == "concept"
            )
            assert concept_link.target_exists is True

            print("[PASS] experience-to-concept link")

        # ---------------------------------------------------------
        # 4. Experience -> Entity persistent link
        # ---------------------------------------------------------
        with PersistentMemoryKnowledgeGraph(database_path) as graph:
            entity_link = graph.link(
                experience_id,
                entity_id,
                "entity",
                strength=0.85,
                confidence=0.90,
                metadata={
                    "origin": "experience",
                    "relationship": "used_entity",
                },
            )

            assert entity_link.association.target_id == entity_id
            assert (
                entity_link.association.target_type
                == "entity"
            )
            assert entity_link.target_exists is True

            print("[PASS] experience-to-entity link")

        # ---------------------------------------------------------
        # 5. Experience target type is officially supported
        # ---------------------------------------------------------
        with PersistentMemoryKnowledgeGraph(database_path) as graph:
            experience_link = graph.link(
                "memory_learning_index",
                experience_id,
                "experience",
                strength=0.95,
                confidence=0.95,
                metadata={
                    "origin": "experience_memory",
                    "relationship": "memory_to_experience",
                },
            )

            assert (
                experience_link.association.target_id
                == experience_id
            )
            assert (
                experience_link.association.target_type
                == "experience"
            )
            assert (
                experience_link.association.association_type
                == "memory_to_experience"
            )
            assert experience_link.target_exists is True

            print("[PASS] experience target support")

        # ---------------------------------------------------------
        # 6. No duplicated experience content
        # ---------------------------------------------------------
        with MemoryAssociationStorage(database_path) as storage:
            links = storage.associations_for_memory(
                experience_id
            )

            assert len(links) == 2

            targets = {
                (
                    link.target_id,
                    link.target_type,
                )
                for link in links
            }

            assert (
                concept_id,
                "concept",
            ) in targets

            assert (
                entity_id,
                "entity",
            ) in targets

            print("[PASS] associative links without content duplication")

        # ---------------------------------------------------------
        # 7. Reverse Concept -> Experience lookup
        # ---------------------------------------------------------
        with MemoryAssociationStorage(database_path) as storage:
            reverse_concept = storage.memories_for_target(
                concept_id,
                "concept",
            )

            assert reverse_concept == (
                experience_id,
            )

            print("[PASS] reverse concept-to-experience lookup")

        # ---------------------------------------------------------
        # 8. Reverse Entity -> Experience lookup
        # ---------------------------------------------------------
        with MemoryAssociationStorage(database_path) as storage:
            reverse_entity = storage.memories_for_target(
                entity_id,
                "entity",
            )

            assert reverse_entity == (
                experience_id,
            )

            print("[PASS] reverse entity-to-experience lookup")

        # ---------------------------------------------------------
        # 9. Persistence across restart
        # ---------------------------------------------------------
        with PersistentMemoryKnowledgeGraph(database_path) as graph:
            restarted_concept = graph._knowledge_storage.get_concept(
                concept_id
            )

            restarted_entity = graph._knowledge_storage.get_entity(
                entity_id
            )

            assert restarted_concept == concept
            assert restarted_entity == entity

        with MemoryAssociationStorage(database_path) as storage:
            concept_links = storage.associations_for_memory(
                experience_id
            )

            assert len(concept_links) == 2

            restored_concept = storage.memories_for_target(
                concept_id,
                "concept",
            )

            restored_entity = storage.memories_for_target(
                entity_id,
                "entity",
            )

            assert restored_concept == (
                experience_id,
            )

            assert restored_entity == (
                experience_id,
            )

            print("[PASS] experience-knowledge links survive restart")

        # ---------------------------------------------------------
        # 10. Invalid target type protection
        # ---------------------------------------------------------
        with PersistentMemoryKnowledgeGraph(database_path) as graph:
            try:
                graph.link(
                    experience_id,
                    "invalid-target",
                    "invalid_type",
                )
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "invalid target type should be rejected"
                )

        print("[PASS] invalid target type protection")

        # ---------------------------------------------------------
        # 11. Empty experience/memory identity protection
        # ---------------------------------------------------------
        with PersistentMemoryKnowledgeGraph(database_path) as graph:
            try:
                graph.link(
                    "",
                    concept_id,
                    "concept",
                )
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "empty memory ID should be rejected"
                )

        print("[PASS] empty experience identity protection")

        # ---------------------------------------------------------
        # Final
        # ---------------------------------------------------------
        print(
            "SAHIBEX PHASE 3 #69 EXPERIENCE-KNOWLEDGE "
            "INTEGRATION TEST: PASS"
        )


if __name__ == "__main__":
    main()
