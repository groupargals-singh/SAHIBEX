import tempfile
from datetime import datetime, timezone
from pathlib import Path

from core.research.knowledge_graph_storage import KnowledgeGraphStorage
from core.research.knowledge_linking import KnowledgeLinker
from core.research.knowledge_merge import (
    KnowledgeDuplicateDetector,
    KnowledgeMergeService,
)
from core.research.knowledge_registry import (
    Concept,
    Entity,
    KnowledgeRegistry,
)
from core.research.knowledge_conflict import (
    CONFLICT_TYPE_EXPLICIT_NEGATION,
    RESOLUTION_UNRESOLVED,
    KnowledgeConflictRecord,
)
from core.research.models import KnowledgeCandidate
from core.research.relationship import Relationship
from core.research.storage import ResearchStorage


def check(condition, message):
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def build_knowledge(
    knowledge_id,
    statement,
    confidence=0.9,
    verified=True,
):
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        findings=[],
        evidence=[],
        confidence=confidence,
        verified=verified,
        created_at=datetime.now(timezone.utc),
        last_verified_at=(
            datetime.now(timezone.utc)
            if verified
            else None
        ),
        metadata={},
    )


def test_knowledge_object_and_registry():
    knowledge = build_knowledge(
        "knowledge-reg-1",
        "Python is a programming language.",
    )

    registry = KnowledgeRegistry()

    entity = Entity(
        entity_id="entity-python",
        name="Python",
        entity_type="software_language",
    )

    concept = Concept(
        concept_id="concept-programming-language",
        name="Programming Language",
        concept_type="technology",
    )

    registry.register_entity(entity)
    registry.register_concept(concept)

    check(
        registry.get_entity("entity-python") == entity,
        "entity registry",
    )

    check(
        registry.get_concept(
            "concept-programming-language"
        )
        == concept,
        "concept registry",
    )

    check(
        knowledge.knowledge_id == "knowledge-reg-1",
        "knowledge object contract",
    )


def test_relationship_and_graph_storage():
    relationship = Relationship(
        relationship_id="relationship-python-language",
        source_id="knowledge-reg-1",
        source_type="knowledge",
        relationship_type="ABOUT",
        target_id="entity-python",
        target_type="entity",
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "knowledge_graph.db"

        storage = KnowledgeGraphStorage(str(db_path))

        storage.save_relationship(relationship)

        loaded = storage.get_relationship(
            "relationship-python-language"
        )

        check(
            loaded == relationship,
            "relationship graph persistence",
        )

        check(
            storage.relationship_count() == 1,
            "relationship graph count",
        )

        storage.close()


def test_knowledge_linking():
    linker = KnowledgeLinker()

    linker.link(
        "knowledge-reg-1",
        "entity-python",
        "entity",
    )

    linker.link(
        "knowledge-reg-1",
        "concept-programming-language",
        "concept",
    )

    links = linker.links_for_knowledge(
        "knowledge-reg-1"
    )

    check(
        len(links) == 2,
        "knowledge links",
    )

    reverse = linker.knowledge_for_target(
        "entity-python",
        "entity",
    )

    check(
        reverse == ["knowledge-reg-1"],
        "reverse knowledge linking",
    )


def test_duplicate_detection_and_safe_merge():
    primary = build_knowledge(
        "knowledge-primary",
        "Python is a programming language.",
    )

    duplicate = build_knowledge(
        "knowledge-duplicate",
        " Python is a programming language. ",
    )

    detector = KnowledgeDuplicateDetector()

    duplicate_result = detector.compare(
        primary.statement,
        duplicate.statement,
    )

    check(
        duplicate_result.is_duplicate,
        "duplicate knowledge detection",
    )

    merge_plan = detector.plan_merge(
        primary_knowledge_id=primary.knowledge_id,
        duplicate_knowledge_id=duplicate.knowledge_id,
        primary_statement=primary.statement,
        duplicate_statement=duplicate.statement,
    )

    check(
        merge_plan.safe_to_merge,
        "safe merge planning",
    )

    merge_service = KnowledgeMergeService()

    merged_result = merge_service.merge(
        primary,
        duplicate,
    )

    check(
        merged_result.knowledge.knowledge_id
        == primary.knowledge_id,
        "primary knowledge identity preserved",
    )

    check(
        merged_result.knowledge.statement
        == primary.statement,
        "merged knowledge statement preserved",
    )

    check(
        primary.statement
        == "Python is a programming language.",
        "primary knowledge remains unchanged",
    )

    check(
        duplicate.statement
        == " Python is a programming language. ",
        "duplicate knowledge remains unchanged",
    )


def test_conflict_persistence_and_history():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "research.db"

        storage = ResearchStorage(str(db_path))

        first = build_knowledge(
            "knowledge-online",
            "The system is online.",
            confidence=0.8,
            verified=False,
        )

        second = build_knowledge(
            "knowledge-offline",
            "The system is not online.",
            confidence=0.8,
            verified=False,
        )

        storage.save_knowledge(first)
        storage.save_knowledge(second)

        now = datetime.now(timezone.utc)

        conflict = KnowledgeConflictRecord(
            conflict_id="conflict-regression-1",
            first_knowledge_id=first.knowledge_id,
            second_knowledge_id=second.knowledge_id,
            conflict_type=CONFLICT_TYPE_EXPLICIT_NEGATION,
            conflict_reason=(
                "same context with opposite explicit negation"
            ),
            resolution_status=RESOLUTION_UNRESOLVED,
            selected_knowledge_id=None,
            evidence_score_delta=0.0,
            source_reliability_delta=0.0,
            knowledge_confidence_delta=0.0,
            resolution_reason="Regression test unresolved conflict",
            created_at=now,
            metadata={
                "test": "6H-11",
            },
        )

        storage.save_knowledge_conflict(conflict)

        loaded_conflict = storage.get_knowledge_conflict(
            "conflict-regression-1"
        )

        check(
            loaded_conflict is not None,
            "conflict persistence",
        )

        check(
            loaded_conflict.conflict_id
            == "conflict-regression-1",
            "conflict identity preserved",
        )

        history = storage.conflicts_for_knowledge(
            first.knowledge_id
        )

        check(
            len(history) == 1,
            "conflict history",
        )

        context = storage.knowledge_verification_context(
            first.knowledge_id
        )

        check(
            context["conflict_status"] == "UNRESOLVED",
            "unresolved conflict context",
        )

        storage.close()


def test_verification_lifecycle_and_restart():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "verification.db"

        storage = ResearchStorage(str(db_path))

        knowledge = build_knowledge(
            "knowledge-verification",
            "Python supports programming.",
        )

        storage.save_knowledge(knowledge)

        verified_at = datetime.now(timezone.utc)

        storage.record_knowledge_verification(
            knowledge_id=knowledge.knowledge_id,
            status="VERIFIED",
            reason="Regression verification",
            verified_at=verified_at,
            metadata={
                "test": "6H-11",
            },
        )

        lifecycle = (
            storage.knowledge_verification_lifecycle(
                knowledge.knowledge_id
            )
        )

        check(
            lifecycle["verification_status"]
            == "VERIFIED",
            "verification lifecycle status",
        )

        check(
            lifecycle["verification_event_count"] == 1,
            "verification lifecycle event count",
        )

        storage.close()

        storage = ResearchStorage(str(db_path))

        restarted = (
            storage.knowledge_verification_lifecycle(
                knowledge.knowledge_id
            )
        )

        check(
            restarted["verification_status"]
            == "VERIFIED",
            "verification survives restart",
        )

        check(
            restarted["verification_event_count"] == 1,
            "verification history survives restart",
        )

        storage.close()


def test_knowledge_retrieval():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "retrieval.db"

        storage = ResearchStorage(str(db_path))

        storage.save_knowledge(
            build_knowledge(
                "knowledge-retrieval-1",
                "Python is a programming language.",
                confidence=0.95,
                verified=True,
            )
        )

        storage.save_knowledge(
            build_knowledge(
                "knowledge-retrieval-2",
                "Python is widely used.",
                confidence=0.80,
                verified=True,
            )
        )
        for knowledge_id in ("knowledge-retrieval-1", "knowledge-retrieval-2"):
            storage.record_knowledge_verification(
                knowledge_id=knowledge_id,
                status="VERIFIED",
                reason="Test fixture includes an explicit VERIFIED lifecycle event.",
                verified_at=datetime.now(timezone.utc),
                metadata={"independent_source_count": 2},
            )

        storage.save_knowledge(
            build_knowledge(
                "knowledge-retrieval-3",
                "Python may be used for scripting.",
                confidence=0.60,
                verified=False,
            )
        )

        results = storage.retrieve_knowledge(
            "python",
        )

        check(
            len(results) == 3,
            "knowledge retrieval",
        )

        check(
            results[0].knowledge_id
            == "knowledge-retrieval-1",
            "deterministic confidence ordering",
        )

        verified_results = storage.retrieve_knowledge(
            "python",
            verified_only=True,
        )

        check(
            len(verified_results) == 2,
            "verified knowledge retrieval",
        )

        confidence_results = storage.retrieve_knowledge(
            "python",
            min_confidence=0.9,
        )

        check(
            len(confidence_results) == 1,
            "minimum confidence retrieval",
        )

        storage.close()


def main():
    print(
        "SAHIBEX 6H-11 KNOWLEDGE REGRESSION TEST"
    )

    test_knowledge_object_and_registry()
    test_relationship_and_graph_storage()
    test_knowledge_linking()
    test_duplicate_detection_and_safe_merge()
    test_conflict_persistence_and_history()
    test_verification_lifecycle_and_restart()
    test_knowledge_retrieval()

    print(
        "SAHIBEX 6H-11 KNOWLEDGE REGRESSION TEST: PASS"
    )


if __name__ == "__main__":
    main()
