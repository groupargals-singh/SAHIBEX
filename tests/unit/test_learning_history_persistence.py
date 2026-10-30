from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.brain.mother_learning_integration import MotherLearningIntegration
from core.research.storage import ResearchStorage


def test_learning_history_survives_storage_restart_and_preserves_order(
    tmp_path: Path,
) -> None:
    database = tmp_path / "learning-history.db"
    storage = ResearchStorage(database)
    first = storage.record_learning_history(
        topic="alpha",
        success=False,
        status="insufficient_verified_knowledge",
        verification_status="INSUFFICIENT_VERIFIED_KNOWLEDGE",
        research_job_id="job-1",
        research_execution_id="execution-1",
        learned_knowledge_ids=("k-unverified",),
        verified_knowledge_ids=(),
        error="No verified knowledge items.",
        created_at=datetime(2026, 10, 16, 10, 0, tzinfo=timezone.utc),
    )
    second = storage.record_learning_history(
        topic="alpha",
        success=True,
        status="completed",
        verification_status="VERIFIED",
        research_job_id="job-2",
        research_execution_id="execution-2",
        learned_knowledge_ids=("k-verified",),
        verified_knowledge_ids=("k-verified",),
        created_at=datetime(2026, 10, 16, 10, 0, tzinfo=timezone.utc),
    )
    storage.close()

    restarted = ResearchStorage(database)
    history = restarted.learning_history(topic="alpha")
    assert restarted.learning_history_count() == 2
    assert [event["event_id"] for event in history] == [
        first["event_id"], second["event_id"]
    ]
    assert history[0]["success"] is False
    assert history[0]["verified_knowledge_ids"] == ()
    assert history[0]["error"] == "No verified knowledge items."
    assert history[1]["success"] is True
    assert history[1]["verified_knowledge_ids"] == ("k-verified",)
    assert history[0]["created_at"].tzinfo is not None
    assert restarted.learning_history(limit=1)[0]["event_id"] == first["event_id"]
    restarted.close()


def test_mother_learning_persists_rejected_attempt(tmp_path: Path) -> None:
    storage = ResearchStorage(tmp_path / "learning-bridge.db")
    context = SimpleNamespace(
        answer=SimpleNamespace(
            arbitration=SimpleNamespace(accepted=False),
            answer=SimpleNamespace(knowledge_ids=("k-weak",), evidence=()),
            knowledge_verification_contexts={
                "k-weak": {"verification_status": "UNVERIFIED"}
            },
        )
    )

    class FakeResearch:
        def __init__(self) -> None:
            self.storage = storage
            self.research_pipeline = SimpleNamespace(
                context_for=lambda _job_id: context
            )

        def research(self, *, query: str, confirmation: bool = False):
            return SimpleNamespace(
                success=True,
                status="completed",
                answer="Candidate answer",
                job_id="job-rejected",
                execution_id="execution-rejected",
                verification_status="VERIFIED",
                error="",
            )

    result = MotherLearningIntegration(research=FakeResearch()).learn(
        topic="reject weak claim"
    )
    assert result.success is False
    assert result.verification_status == "INSUFFICIENT_VERIFIED_KNOWLEDGE"
    history = storage.learning_history()
    assert len(history) == 1
    assert history[0]["topic"] == "reject weak claim"
    assert history[0]["success"] is False
    assert history[0]["research_job_id"] == "job-rejected"
    assert history[0]["verified_knowledge_ids"] == ()
    storage.close()


def test_research_exception_is_recorded_as_failed_learning(tmp_path: Path) -> None:
    storage = ResearchStorage(tmp_path / "learning-exception.db")

    class BrokenResearch:
        def __init__(self) -> None:
            self.storage = storage

        def research(self, *, query: str, confirmation: bool = False):
            raise RuntimeError("provider crashed")

    result = MotherLearningIntegration(research=BrokenResearch()).learn(
        topic="record failed research"
    )
    assert result.success is False
    assert result.status == "research_execution_failed"
    assert result.verification_status == "FAILED"
    history = storage.learning_history()
    assert len(history) == 1
    assert history[0]["success"] is False
    assert history[0]["status"] == "research_execution_failed"
    assert "provider crashed" in history[0]["error"]
    storage.close()


def test_learning_history_rejects_invalid_arguments() -> None:
    storage = ResearchStorage(":memory:")
    with pytest.raises(ValueError):
        storage.record_learning_history(
            topic=" ", success=False, status="failed",
            verification_status="FAILED"
        )
    with pytest.raises(ValueError):
        storage.learning_history(limit=0)
    with pytest.raises(ValueError):
        storage.learning_history(topic=" ")
    storage.close()
