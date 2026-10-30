from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.answer_pipeline import ResearchAnswerPipeline
from core.research.engine import ResearchEngine

from core.research.models import Evidence, KnowledgeCandidate

from core.research.knowledge_conflict import (
    CONFLICT_TYPE_EXPLICIT_NEGATION,
    RESOLUTION_UNRESOLVED,
    KnowledgeConflictRecord,
)

from core.research.query import ResearchQueryEngine
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
    confidence: float = 0.95,
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


def test_knowledge_verification_context_reaches_answer_pipeline() -> None:
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"

        storage = ResearchStorage(database_path)

        knowledge = build_knowledge(
            "knowledge-python",
            "Python is widely used for software development.",
        )

        storage.save_knowledge(knowledge)

        storage.record_knowledge_verification(
            knowledge_id=knowledge.knowledge_id,
            status="VERIFIED",
            reason="Verified by research pipeline.",
            verified_at=now(),
            metadata={
                "test": "6H-10",
            },
        )

        engine = ResearchEngine()

        query_engine = ResearchQueryEngine(
            engine=engine,
            storage=storage,
        )

        pipeline = ResearchAnswerPipeline(
            query_engine=query_engine,
        )

        result = pipeline.run(
            "Python software development",
            verified_only=True,
        )

        check(
            result.answer is not None,
            "final answer is available",
        )

        check(
            result.answer.knowledge_ids == [
                knowledge.knowledge_id
            ],
            "knowledge ID reaches final answer",
        )

        check(
            knowledge.knowledge_id in result.knowledge_verification_contexts,
            "knowledge verification context reaches answer pipeline",
        )

        context = result.knowledge_verification_contexts[
            knowledge.knowledge_id
        ]

        check(
            context["verification_status"] == "VERIFIED",
            "verified knowledge status reaches final answer context",
        )

        check(
            context["verification_event_count"] == 1,
            "verification history count reaches final answer context",
        )

        check(
            context["conflict_status"] == "NO_CONFLICT",
            "conflict status reaches final answer context",
        )

        storage.close()


def test_unresolved_conflict_context_is_preserved() -> None:
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"

        storage = ResearchStorage(database_path)

        first = build_knowledge(
            "knowledge-online",
            "The system is online.",
            confidence=0.70,
        )

        second = build_knowledge(
            "knowledge-offline",
            "The system is not online.",
            confidence=0.70,
        )

        storage.save_knowledge(first)
        storage.save_knowledge(second)

        storage.record_knowledge_verification(
            knowledge_id=first.knowledge_id,
            status="CONFLICTED",
            reason="Conflicting knowledge detected.",
            verified_at=now(),
            metadata={
                "test": "6H-10",
            },
        )

        engine = ResearchEngine()

        query_engine = ResearchQueryEngine(
            engine=engine,
            storage=storage,
        )

        pipeline = ResearchAnswerPipeline(
            query_engine=query_engine,
        )

        result = pipeline.run(
            "system online",
            verified_only=False,
            limit=10,
        )

        check(
            result.answer is not None,
            "conflict query still produces safe answer result",
        )
        check(
            first.knowledge_id not in result.answer.knowledge_ids,
            "conflicted knowledge is excluded from final answer",
        )


        check(
            first.knowledge_id in result.knowledge_verification_contexts,
            "first conflicting knowledge context preserved",
        )

        context = result.knowledge_verification_contexts[
            first.knowledge_id
        ]

        check(
            context["verification_status"] == "CONFLICTED",
            "conflicted verification status preserved",
        )

        check(
            context["conflict_status"] == "NO_CONFLICT"
            or context["conflict_status"] == "UNRESOLVED",
            "conflict context remains explicitly classified",
        )

        storage.close()


def test_answer_pipeline_persists_detected_conflicts_for_future_retrieval() -> None:
    with TemporaryDirectory() as temporary_directory:
        storage = ResearchStorage(Path(temporary_directory) / "conflict-persistence.db")
        winner = build_knowledge(
            "pipeline-conflict-winner",
            "The system is online.",
            confidence=0.95,
        )
        loser = build_knowledge(
            "pipeline-conflict-loser",
            "The system is not online.",
            confidence=0.60,
        )
        for item in (winner, loser):
            storage.save_knowledge(item)
            storage.record_knowledge_verification(
                knowledge_id=item.knowledge_id,
                status="VERIFIED",
                reason="Previously verified before conflicting research.",
                verified_at=now(),
            )

        pipeline = ResearchAnswerPipeline(
            query_engine=ResearchQueryEngine(
                engine=ResearchEngine(),
                storage=storage,
            ),
        )
        result = pipeline.run("system is online", verified_only=True)

        check(
            result.aggregation.conflict_count == 1,
            "answer pipeline detects the contradictory claims",
        )
        check(
            storage.conflict_assessment_count() == 1,
            "answer pipeline persists the conflict assessment",
        )
        context = storage.knowledge_verification_context(loser.knowledge_id)
        check(
            context["conflict_count"] == 1
            and context["selected_knowledge_id"] == winner.knowledge_id,
            "persisted conflict context identifies the selected claim",
        )
        storage.close()


def test_knowledge_context_survives_storage_restart() -> None:
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"

        knowledge = build_knowledge(
            "knowledge-restart",
            "SQLite is a lightweight database.",
        )

        storage = ResearchStorage(database_path)

        storage.save_knowledge(knowledge)

        storage.record_knowledge_verification(
            knowledge_id=knowledge.knowledge_id,
            status="VERIFIED",
            reason="Restart persistence test.",
            verified_at=now(),
        )

        storage.close()

        storage = ResearchStorage(database_path)

        engine = ResearchEngine()

        query_engine = ResearchQueryEngine(
            engine=engine,
            storage=storage,
        )

        pipeline = ResearchAnswerPipeline(
            query_engine=query_engine,
        )

        result = pipeline.run(
            "SQLite lightweight database",
            verified_only=True,
        )

        context = result.knowledge_verification_contexts[
            knowledge.knowledge_id
        ]

        check(
            context["verification_status"] == "VERIFIED",
            "verification context survives restart",
        )

        check(
            context["verification_event_count"] == 1,
            "verification history survives restart",
        )

        storage.close()


def test_missing_verification_history_blocks_trusted_retrieval() -> None:
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"
        storage = ResearchStorage(database_path)

        knowledge = build_knowledge(
            "knowledge-live-no-history",
            "Python is used for software development.",
            verified=True,
        )
        storage.save_knowledge(knowledge)

        engine = ResearchEngine()
        query_engine = ResearchQueryEngine(
            engine=engine,
            storage=storage,
        )
        pipeline = ResearchAnswerPipeline(query_engine=query_engine)

        result = pipeline.run(
            "Python software development",
            verified_only=True,
        )

        check(
            result.answer is None
            or knowledge.knowledge_id not in result.answer.knowledge_ids,
            "knowledge without verification history is blocked",
        )
        check(
            result.knowledge_verification_contexts[
                knowledge.knowledge_id
            ]["verification_event_count"] == 0,
            "missing verification history is reported accurately",
        )

        storage.close()


def test_conflicted_knowledge_evidence_is_removed_before_synthesis() -> None:
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"
        storage = ResearchStorage(database_path)

        knowledge = build_knowledge(
            "knowledge-conflicted-evidence",
            "The system is online.",
            verified=True,
        )
        storage.save_knowledge(knowledge)

        storage.record_knowledge_verification(
            knowledge_id=knowledge.knowledge_id,
            status="CONFLICTED",
            reason="Regression test: conflicting claim.",
            verified_at=now(),
            metadata={"test": "verification-evidence-gate"},
        )

        evidence = Evidence(
            evidence_id="evidence-conflicted-001",
            finding_id="finding-conflicted-001",
            source_id="source-conflicted-001",
            evidence_text="The system is online.",
            supports=True,
            strength=0.95,
            metadata={
                "knowledge_id": knowledge.knowledge_id,
            },
        )

        query_engine = ResearchQueryEngine(
            engine=ResearchEngine(),
            storage=storage,
        )
        pipeline = ResearchAnswerPipeline(
            query_engine=query_engine,
        )

        original_synthesize = pipeline.synthesizer.synthesize
        captured = {}

        def capture_synthesis(
            query,
            aggregation,
            *,
            evidence_items=(),
        ):
            captured["evidence_items"] = list(evidence_items)
            return original_synthesize(
                query,
                aggregation,
                evidence_items=captured["evidence_items"],
            )

        pipeline.synthesizer.synthesize = capture_synthesis

        result = pipeline.run(
            "system online",
            verified_only=False,
            evidence_items=[evidence],
        )

        synthesized_evidence = captured["evidence_items"]

        check(
            all(
                (item.metadata or {}).get("knowledge_id")
                != knowledge.knowledge_id
                for item in synthesized_evidence
            ),
            "evidence linked to conflicted knowledge is removed before synthesis",
        )

        check(
            knowledge.knowledge_id not in result.answer.knowledge_ids,
            "conflicted knowledge is excluded from the final answer",
        )

        storage.close()


def test_persisted_unresolved_conflict_blocks_verified_candidate() -> None:
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "research.db"
        storage = ResearchStorage(database_path)

        knowledge = build_knowledge(
            "knowledge-persisted-conflict",
            "The system is online.",
            verified=True,
        )
        unrelated = build_knowledge(
            "knowledge-conflict-counterpart",
            "A separate placeholder record about gardening.",
            verified=False,
        )

        storage.save_knowledge(knowledge)
        storage.save_knowledge(unrelated)

        storage.record_knowledge_verification(
            knowledge_id=knowledge.knowledge_id,
            status="VERIFIED",
            reason="Regression test: lifecycle is verified.",
            verified_at=now(),
            metadata={"test": "persisted-conflict-gate"},
        )

        storage.save_knowledge_conflict(
            KnowledgeConflictRecord(
                conflict_id="conflict-persisted-unresolved",
                first_knowledge_id=knowledge.knowledge_id,
                second_knowledge_id=unrelated.knowledge_id,
                conflict_type=CONFLICT_TYPE_EXPLICIT_NEGATION,
                conflict_reason="Persisted conflict requiring review.",
                resolution_status=RESOLUTION_UNRESOLVED,
                selected_knowledge_id=None,
                evidence_score_delta=0.0,
                source_reliability_delta=0.0,
                knowledge_confidence_delta=0.0,
                resolution_reason="Insufficient evidence.",
                created_at=now(),
                metadata={"test": "persisted-conflict-gate"},
            )
        )

        evidence = Evidence(
            evidence_id="evidence-persisted-conflict",
            finding_id="finding-persisted-conflict",
            source_id="source-persisted-conflict",
            evidence_text="The system is online.",
            supports=True,
            strength=0.95,
            metadata={"knowledge_id": knowledge.knowledge_id},
        )

        query_engine = ResearchQueryEngine(
            engine=ResearchEngine(),
            storage=storage,
        )
        pipeline = ResearchAnswerPipeline(query_engine=query_engine)

        original_synthesize = pipeline.synthesizer.synthesize
        captured = {}

        def capture_synthesis(
            query,
            aggregation,
            *,
            evidence_items=(),
        ):
            captured["evidence_items"] = list(evidence_items)

            captured["knowledge_ids"] = [
                item.knowledge_id
                for item in aggregation.results
            ]
            return original_synthesize(
                query,
                aggregation,
                evidence_items=captured["evidence_items"],
            )

        pipeline.synthesizer.synthesize = capture_synthesis

        result = pipeline.run(
            "system online",
            verified_only=False,
            evidence_items=[evidence],
        )

        context = result.knowledge_verification_contexts[
            knowledge.knowledge_id
        ]

        check(
            context["verification_status"] == "VERIFIED",
            "persisted-conflict candidate retains VERIFIED lifecycle context",
        )
        check(
            context["conflict_status"] == "UNRESOLVED",
            "persisted unresolved conflict remains visible in audit context",
        )
        check(
            knowledge.knowledge_id not in captured.get("knowledge_ids", []),
            "persisted unresolved conflict blocks candidate before synthesis",
        )
        check(
            all(
                (item.metadata or {}).get("knowledge_id")
                != knowledge.knowledge_id
                for item in captured.get("evidence_items", [])
            ),
            "evidence linked to persisted-conflict candidate is removed",
        )
        check(
            knowledge.knowledge_id not in result.answer.knowledge_ids,
            "persisted unresolved-conflict candidate is excluded from final answer",
        )

        storage.close()


def main() -> None:
    print("SAHIBEX 6H-10 KNOWLEDGE-TO-ANSWER INTEGRATION TEST")

    test_knowledge_verification_context_reaches_answer_pipeline()
    test_unresolved_conflict_context_is_preserved()
    test_knowledge_context_survives_storage_restart()
    test_missing_verification_history_blocks_trusted_retrieval()

    print(
        "SAHIBEX 6H-10 KNOWLEDGE-TO-ANSWER INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
