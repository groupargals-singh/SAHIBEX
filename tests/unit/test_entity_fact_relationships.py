from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.fact import Fact
from core.research.knowledge_graph_storage import KnowledgeGraphStorage
from core.research.knowledge_registry import Entity
from core.research.relationship import Relationship


def main() -> None:
    print("SAHIBEX PHASE 3 #67 ENTITY-FACT RELATIONSHIPS TEST")

    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "entity_fact.db"

        with KnowledgeGraphStorage(database_path) as storage:
            python = Entity(
                entity_id="entity_python",
                name="Python",
                entity_type="programming_language",
            )

            sahibex = Entity(
                entity_id="entity_sahibex",
                name="SAHIBEX",
                entity_type="ai_system",
            )

            storage.save_entity(python)
            storage.save_entity(sahibex)

            fact_python = Fact(
                fact_id="fact_python_language",
                subject_id="entity_python",
                subject_type="entity",
                predicate="is_programming_language",
                object_value="true",
                confidence=0.98,
                verified=True,
                metadata={
                    "source": "test",
                },
            )

            fact_sahibex = Fact(
                fact_id="fact_sahibex_uses_python",
                subject_id="entity_sahibex",
                subject_type="entity",
                predicate="uses",
                object_id="entity_python",
                object_type="entity",
                confidence=0.95,
                verified=True,
            )

            storage.save_fact(fact_python)
            storage.save_fact(fact_sahibex)

            assert storage.fact_count() == 2
            print("[PASS] fact persistence and count")

            loaded = storage.get_fact(
                "fact_python_language"
            )

            assert loaded == fact_python
            print("[PASS] fact retrieval")

            assert storage.get_fact("missing_fact") is None
            print("[PASS] unknown fact lookup")

            python_facts = storage.facts_for_subject(
                "entity_python"
            )

            assert python_facts == (
                fact_python,
            )
            print("[PASS] entity-to-fact subject retrieval")

            sahibex_facts = storage.facts_for_subject(
                "entity_sahibex"
            )

            assert sahibex_facts == (
                fact_sahibex,
            )
            print("[PASS] second entity fact retrieval")

            storage.save_relationship(
                Relationship(
                    relationship_id="rel_python_fact",
                    source_id="entity_python",
                    source_type="entity",
                    relationship_type="has_fact",
                    target_id="fact_python_language",
                    target_type="fact",
                )
            )

            storage.save_relationship(
                Relationship(
                    relationship_id="rel_sahibex_fact",
                    source_id="entity_sahibex",
                    source_type="entity",
                    relationship_type="has_fact",
                    target_id="fact_sahibex_uses_python",
                    target_type="fact",
                )
            )

            storage.save_relationship(
                Relationship(
                    relationship_id="rel_fact_python",
                    source_id="fact_sahibex_uses_python",
                    source_type="fact",
                    relationship_type="about",
                    target_id="entity_python",
                    target_type="entity",
                )
            )

            assert storage.get_relationship(
                "rel_python_fact"
            ) is not None

            assert storage.get_relationship(
                "rel_sahibex_fact"
            ) is not None

            assert storage.get_relationship(
                "rel_fact_python"
            ) is not None

            print("[PASS] entity-fact relationships persisted")

            python_fact_relationship = storage.get_relationship(
                "rel_python_fact"
            )

            assert python_fact_relationship.source_type == "entity"
            assert python_fact_relationship.target_type == "fact"
            assert python_fact_relationship.target_id == (
                "fact_python_language"
            )
            print("[PASS] entity-to-fact relationship integrity")

            fact_entity_relationship = storage.get_relationship(
                "rel_fact_python"
            )

            assert fact_entity_relationship.source_type == "fact"
            assert fact_entity_relationship.target_type == "entity"
            assert fact_entity_relationship.target_id == (
                "entity_python"
            )
            print("[PASS] fact-to-entity relationship integrity")

            assert (
                storage.get_relationship(
                    "rel_sahibex_fact"
                ).target_id
                == "fact_sahibex_uses_python"
            )
            print("[PASS] multiple entity-fact links")

            try:
                storage.facts_for_subject("")
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "empty subject ID should raise ValueError"
                )

            print("[PASS] empty subject protection")

            try:
                Fact(
                    fact_id="invalid_fact",
                    subject_id="entity_python",
                    subject_type="entity",
                    predicate="invalid",
                )
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "fact without object should be rejected"
                )

            print("[PASS] invalid fact protection")

            try:
                Fact(
                    fact_id="invalid_fact_confidence",
                    subject_id="entity_python",
                    subject_type="entity",
                    predicate="invalid",
                    object_value="true",
                    confidence=1.01,
                )
            except ValueError:
                pass
            else:
                raise AssertionError(
                    "invalid fact confidence should be rejected"
                )

            print("[PASS] fact confidence protection")

        with KnowledgeGraphStorage(database_path) as restarted:
            assert restarted.fact_count() == 2

            assert (
                restarted.get_fact(
                    "fact_python_language"
                )
                == fact_python
            )

            assert (
                restarted.get_fact(
                    "fact_sahibex_uses_python"
                )
                == fact_sahibex
            )

            assert restarted.get_relationship(
                "rel_python_fact"
            ) is not None

            assert restarted.get_relationship(
                "rel_sahibex_fact"
            ) is not None

            assert restarted.get_relationship(
                "rel_fact_python"
            ) is not None

            print("[PASS] fact and relationship persistence across restart")

        print("SAHIBEX PHASE 3 #67 ENTITY-FACT RELATIONSHIPS TEST: PASS")


if __name__ == "__main__":
    main()
