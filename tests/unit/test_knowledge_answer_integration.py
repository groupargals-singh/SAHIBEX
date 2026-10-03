from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.answer_pipeline import ResearchAnswerPipeline
from core.research.engine import ResearchEngine
from core.research.models import KnowledgeCandidate
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


def main() -> None:
    print("SAHIBEX 6H-10 KNOWLEDGE-TO-ANSWER INTEGRATION TEST")

    test_knowledge_verification_context_reaches_answer_pipeline()
    test_unresolved_conflict_context_is_preserved()
    test_knowledge_context_survives_storage_restart()

    print(
        "SAHIBEX 6H-10 KNOWLEDGE-TO-ANSWER INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
