from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.knowledge_graph_storage import KnowledgeGraphStorage
from core.research.knowledge_registry import Concept
from core.research.relationship import Relationship


def main() -> None:
    print("SAHIBEX PHASE 3 #66 CONCEPT GRAPH TEST")

    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "concept_graph.db"

        with KnowledgeGraphStorage(database_path) as storage:
            ai = Concept(
                concept_id="concept_ai",
                name="Artificial Intelligence",
                concept_type="technology",
            )
            ml = Concept(
                concept_id="concept_ml",
                name="Machine Learning",
                concept_type="technology",
            )
            dl = Concept(
                concept_id="concept_dl",
                name="Deep Learning",
                concept_type="technology",
            )

            storage.save_concept(ai)
            storage.save_concept(ml)
            storage.save_concept(dl)

            storage.save_relationship(
                Relationship(
                    relationship_id="rel_ai_ml",
                    source_id="concept_ai",
                    source_type="concept",
                    relationship_type="includes",
                    target_id="concept_ml",
                    target_type="concept",
                )
            )

            storage.save_relationship(
                Relationship(
                    relationship_id="rel_ai_dl",
                    source_id="concept_ai",
                    source_type="concept",
                    relationship_type="includes",
                    target_id="concept_dl",
                    target_type="concept",
                )
            )

            storage.save_relationship(
                Relationship(
                    relationship_id="rel_ml_dl",
                    source_id="concept_ml",
                    source_type="concept",
                    relationship_type="related_to",
                    target_id="concept_dl",
                    target_type="concept",
                )
            )

            related = storage.concepts_related_to("concept_ai")

            assert related == (
                "concept_dl",
                "concept_ml",
            )
            print("[PASS] concept-to-concept forward retrieval")

            filtered = storage.concepts_related_to(
                "concept_ai",
                "includes",
            )

            assert filtered == (
                "concept_dl",
                "concept_ml",
            )
            print("[PASS] relationship-type filtering")

            reverse = storage.concepts_linked_to("concept_dl")

            assert reverse == (
                "concept_ai",
                "concept_ml",
            )
            print("[PASS] concept-to-concept reverse lookup")

            reverse_filtered = storage.concepts_linked_to(
                "concept_dl",
                "related_to",
            )

            assert reverse_filtered == ("concept_ml",)
            print("[PASS] reverse relationship filtering")

            relationships = storage.concept_relationships(
                "concept_ai"
            )

            assert len(relationships) == 2
            assert all(
                relationship.source_type == "concept"
                and relationship.target_type == "concept"
                for relationship in relationships
            )
            print("[PASS] concept graph relationship integrity")

            try:
                storage.concepts_related_to("missing")
            except KeyError:
                pass
            else:
                raise AssertionError(
                    "unknown concept should raise KeyError"
                )

            print("[PASS] unknown concept protection")

            try:
                storage.concepts_related_to("")
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "empty concept ID should raise ValueError"
                )

            print("[PASS] empty concept protection")

        with KnowledgeGraphStorage(database_path) as restarted:
            assert restarted.concepts_related_to("concept_ai") == (
                "concept_dl",
                "concept_ml",
            )

            assert restarted.concepts_linked_to("concept_dl") == (
                "concept_ai",
                "concept_ml",
            )

            print("[PASS] concept graph persistence across restart")

        print("SAHIBEX PHASE 3 #66 CONCEPT GRAPH TEST: PASS")


if __name__ == "__main__":
    main()
