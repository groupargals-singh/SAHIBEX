from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from core.research.answer_pipeline import ResearchAnswerPipeline
from core.research.engine import ResearchEngine
from core.research.knowledge_conflict import (
    CONFLICT_TYPE_EXPLICIT_NEGATION,
    RESOLUTION_UNRESOLVED,
    KnowledgeConflictRecord,
)
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
from core.research.models import KnowledgeCandidate
from core.research.query import ResearchQueryEngine
from core.research.relationship import Relationship
from core.research.storage import ResearchStorage


def now() -> datetime:
    return datetime.now(timezone.utc)


def check(condition: bool, message: str) -> None:
    assert condition, message
    print(f"[PASS] {message}")


def build_knowledge(
    knowledge_id: str,
    statement: str,
    *,
    confidence: float = 0.90,
    verified: bool = True,
) -> KnowledgeCandidate:
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        findings=[],
        evidence=[],
        confidence=confidence,
        verified=verified,
        created_at=now(),
        last_verified_at=now() if verified else None,
        metadata={},
    )


def test_full_knowledge_intelligence_integration() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)

        research_db = root / "research.db"
        graph_db = root / "knowledge_graph.db"

        # =========================================================
        # 1. Knowledge Object
        # =========================================================

        knowledge = build_knowledge(
            "knowledge-full-001",
            "Python is a programming language.",
            confidence=0.95,
            verified=True,
        )

        check(
            knowledge.knowledge_id == "knowledge-full-001",
            "knowledge object created",
        )

        check(
            knowledge.statement
            == "Python is a programming language.",
            "knowledge statement preserved",
        )

        # =========================================================
        # 2. Entity + Concept Registry
        # =========================================================

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
            "entity registered",
        )

        check(
            registry.get_concept(
                "concept-programming-language"
            )
            == concept,
            "concept registered",
        )

        # =========================================================
        # 3. Relationship + Graph Storage
        # =========================================================

        relationship = Relationship(
            relationship_id="relationship-python-language",
            source_id=knowledge.knowledge_id,
            source_type="knowledge",
            relationship_type="ABOUT",
            target_id=entity.entity_id,
            target_type="entity",
            metadata={
                "test": "6H-12",
            },
        )

        graph_storage = KnowledgeGraphStorage(
            str(graph_db)
        )

        graph_storage.save_relationship(relationship)

        loaded_relationship = graph_storage.get_relationship(
            relationship.relationship_id
        )

        check(
            loaded_relationship == relationship,
            "relationship persisted in knowledge graph",
        )

        check(
            graph_storage.relationship_count() == 1,
            "knowledge graph relationship count",
        )

        graph_storage.close()

        # =========================================================
        # 4. Knowledge Linking
        # =========================================================

        linker = KnowledgeLinker()

        linker.link(
            knowledge.knowledge_id,
            entity.entity_id,
            "entity",
        )

        linker.link(
            knowledge.knowledge_id,
            concept.concept_id,
            "concept",
        )

        links = linker.links_for_knowledge(
            knowledge.knowledge_id
        )

        check(
            len(links) == 2,
            "knowledge linked to entity and concept",
        )

        reverse_links = linker.knowledge_for_target(
            entity.entity_id,
            "entity",
        )

        check(
            reverse_links == [knowledge.knowledge_id],
            "reverse knowledge link preserved",
        )

        # =========================================================
        # 5. Duplicate Detection + Safe Merge
        # =========================================================

        duplicate = build_knowledge(
            "knowledge-full-002",
            " Python is a programming language. ",
            confidence=0.90,
            verified=True,
        )

        detector = KnowledgeDuplicateDetector()

        duplicate_result = detector.compare(
            knowledge.statement,
            duplicate.statement,
        )

        check(
            duplicate_result.is_duplicate,
            "knowledge duplicate detected",
        )

        merge_plan = detector.plan_merge(
            primary_knowledge_id=knowledge.knowledge_id,
            duplicate_knowledge_id=duplicate.knowledge_id,
            primary_statement=knowledge.statement,
            duplicate_statement=duplicate.statement,
        )

        check(
            merge_plan.safe_to_merge,
            "safe knowledge merge planned",
        )

        merge_service = KnowledgeMergeService()

        merged_result = merge_service.merge(
            knowledge,
            duplicate,
        )

        check(
            merged_result.merged is True,
            "knowledge merge completed",
        )

        check(
            merged_result.safe_to_merge is True,
            "knowledge merge marked safe",
        )

        check(
            merged_result.knowledge.knowledge_id
            == knowledge.knowledge_id,
            "merged primary identity preserved",
        )

        check(
            merged_result.knowledge.statement
            == knowledge.statement,
            "merged knowledge statement preserved",
        )

        # =========================================================
        # 6. Research Storage
        # =========================================================

        storage = ResearchStorage(str(research_db))

        storage.save_knowledge(
            merged_result.knowledge
        )

        stored_knowledge = storage.get_knowledge(
            knowledge.knowledge_id
        )

        check(
            stored_knowledge is not None,
            "merged knowledge persisted to research storage",
        )

        check(
            stored_knowledge.knowledge_id
            == knowledge.knowledge_id,
            "stored knowledge identity preserved",
        )

        # =========================================================
        # 7. Conflict Record
        # =========================================================

        conflicting = build_knowledge(
            "knowledge-full-conflict",
            "Python is not a programming language.",
            confidence=0.70,
            verified=False,
        )

        storage.save_knowledge(conflicting)

        conflict = KnowledgeConflictRecord(
            conflict_id="conflict-full-001",
            first_knowledge_id=knowledge.knowledge_id,
            second_knowledge_id=conflicting.knowledge_id,
            conflict_type=CONFLICT_TYPE_EXPLICIT_NEGATION,
            conflict_reason=(
                "same context with opposite explicit negation"
            ),
            resolution_status=RESOLUTION_UNRESOLVED,
            selected_knowledge_id=None,
            evidence_score_delta=0.0,
            source_reliability_delta=0.0,
            knowledge_confidence_delta=0.25,
            resolution_reason=(
                "Integration test unresolved conflict"
            ),
            created_at=now(),
            metadata={
                "test": "6H-12",
            },
        )

        storage.save_knowledge_conflict(conflict)

        loaded_conflict = storage.get_knowledge_conflict(
            "conflict-full-001"
        )

        check(
            loaded_conflict is not None,
            "knowledge conflict persisted",
        )

        conflict_context = (
            storage.knowledge_verification_context(
                knowledge.knowledge_id
            )
        )

        check(
            conflict_context["conflict_status"]
            == "UNRESOLVED",
            "unresolved conflict context preserved",
        )

        # =========================================================
        # 8. Verification Lifecycle
        # =========================================================

        verification_time = now()

        storage.record_knowledge_verification(
            knowledge_id=knowledge.knowledge_id,
            status="VERIFIED",
            reason="6H-12 integration verification",
            verified_at=verification_time,
            metadata={
                "test": "6H-12",
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
            "verification lifecycle status preserved",
        )

        check(
            lifecycle["verification_event_count"] == 1,
            "verification lifecycle event persisted",
        )

        # =========================================================
        # 9. Knowledge Retrieval
        # =========================================================

        retrieved = storage.retrieve_knowledge(
            "Python is a programming language",
            verified_only=True,
        )

        retrieved_ids = [
            item.knowledge_id
            for item in retrieved
        ]

        check(
            knowledge.knowledge_id in retrieved_ids,
            "verified knowledge retrieved",
        )

        # =========================================================
        # 10. Final Answer Pipeline
        # =========================================================

        engine = ResearchEngine()

        query_engine = ResearchQueryEngine(
            engine=engine,
            storage=storage,
        )

        pipeline = ResearchAnswerPipeline(
            query_engine=query_engine,
        )

        result = pipeline.run(
            "Python programming language",
            verified_only=True,
            limit=10,
        )

        check(
            result.answer is not None,
            "final answer produced",
        )

        check(
            knowledge.knowledge_id
            in result.answer.knowledge_ids,
            "knowledge reaches final answer",
        )

        check(
            knowledge.knowledge_id
            in result.knowledge_verification_contexts,
            "verification context reaches final answer",
        )

        answer_context = (
            result.knowledge_verification_contexts[
                knowledge.knowledge_id
            ]
        )

        check(
            answer_context["verification_status"]
            == "VERIFIED",
            "verified status reaches final answer",
        )

        check(
            answer_context["verification_event_count"]
            == 1,
            "verification history reaches final answer",
        )

        check(
            answer_context["conflict_status"]
            == "UNRESOLVED",
            "conflict status reaches final answer",
        )

        # =========================================================
        # 11. Traceability
        # =========================================================

        check(
            result.traceability is not None,
            "traceability attached to final result",
        )

        check(
            result.traceability.status
            in {
                "TRACEABLE",
                "NO_TRACEABLE_EVIDENCE",
                "EVIDENCE_WITHOUT_SOURCE",
            },
            "traceability status remains explicitly classified",
        )

        # =========================================================
        # 12. Persistence Restart
        # =========================================================

        storage.close()

        restarted_storage = ResearchStorage(
            str(research_db)
        )

        restarted_knowledge = (
            restarted_storage.get_knowledge(
                knowledge.knowledge_id
            )
        )

        check(
            restarted_knowledge is not None,
            "knowledge survives restart",
        )

        restarted_lifecycle = (
            restarted_storage.knowledge_verification_lifecycle(
                knowledge.knowledge_id
            )
        )

        check(
            restarted_lifecycle[
                "verification_status"
            ]
            == "VERIFIED",
            "verification status survives restart",
        )

        restarted_conflict = (
            restarted_storage.get_knowledge_conflict(
                "conflict-full-001"
            )
        )

        check(
            restarted_conflict is not None,
            "conflict survives restart",
        )

        restarted_context = (
            restarted_storage.knowledge_verification_context(
                knowledge.knowledge_id
            )
        )

        check(
            restarted_context["conflict_status"]
            == "UNRESOLVED",
            "conflict context survives restart",
        )

        restarted_storage.close()


def main() -> None:
    print(
        "SAHIBEX 6H-12 FULL KNOWLEDGE INTELLIGENCE "
        "INTEGRATION TEST"
    )

    test_full_knowledge_intelligence_integration()

    print(
        "SAHIBEX 6H-12 FULL KNOWLEDGE INTELLIGENCE "
        "INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
