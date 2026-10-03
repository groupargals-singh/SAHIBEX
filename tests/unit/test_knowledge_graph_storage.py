from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.knowledge_registry import (
    Concept,
    Entity,
)
from core.research.relationship import Relationship
from core.research.knowledge_graph_storage import (
    KnowledgeGraphStorage,
)


def main() -> None:
    print("SAHIBEX 6H-4 KNOWLEDGE GRAPH STORAGE TEST")

    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "knowledge_graph.db"

        with KnowledgeGraphStorage(database_path) as storage:
            entity = Entity(
                entity_id="entity_001",
                name="SAHIBEX",
                entity_type="system",
            )

            concept = Concept(
                concept_id="concept_001",
                name="Artificial Intelligence",
                concept_type="technology",
            )

            relationship = Relationship(
                relationship_id="rel_001",
                source_id="entity_001",
                source_type="entity",
                relationship_type="implements",
                target_id="concept_001",
                target_type="concept",
                metadata={
                    "confidence": 0.95,
                    "origin": "research",
                },
            )

            # -------------------------------------------------
            # Entity persistence
            # -------------------------------------------------

            storage.save_entity(entity)

            loaded_entity = storage.get_entity(
                "entity_001"
            )

            assert loaded_entity == entity

            print("[PASS] entity persistence")

            assert storage.entity_count() == 1

            print("[PASS] entity count")

            # -------------------------------------------------
            # Concept persistence
            # -------------------------------------------------

            storage.save_concept(concept)

            loaded_concept = storage.get_concept(
                "concept_001"
            )

            assert loaded_concept == concept

            print("[PASS] concept persistence")

            assert storage.concept_count() == 1

            print("[PASS] concept count")

            # -------------------------------------------------
            # Relationship persistence
            # -------------------------------------------------

            storage.save_relationship(relationship)

            loaded_relationship = (
                storage.get_relationship("rel_001")
            )

            assert loaded_relationship == relationship

            print("[PASS] relationship persistence")

            assert storage.relationship_count() == 1

            print("[PASS] relationship count")

            # -------------------------------------------------
            # Summary
            # -------------------------------------------------

            summary = storage.summary()

            assert summary["entities"] == 1
            assert summary["concepts"] == 1
            assert summary["relationships"] == 1

            print("[PASS] graph storage summary")

        # -----------------------------------------------------
        # Persistence across restart
        # -----------------------------------------------------

        with KnowledgeGraphStorage(database_path) as restarted:
            assert (
                restarted.get_entity("entity_001")
                == entity
            )

            assert (
                restarted.get_concept("concept_001")
                == concept
            )

            assert (
                restarted.get_relationship("rel_001")
                == relationship
            )

            print("[PASS] persistence across restart")

            assert restarted.entity_count() == 1
            assert restarted.concept_count() == 1
            assert restarted.relationship_count() == 1

            print("[PASS] counts after restart")

    print("SAHIBEX 6H-4 KNOWLEDGE GRAPH STORAGE TEST: PASS")


if __name__ == "__main__":
    main()
