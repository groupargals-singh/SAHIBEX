from __future__ import annotations

from core.brain.master_brain import MasterBrain
from core.brain.mother_decision_context import (
    MotherDecisionContext,
)


def test_master_brain_combined_decision_context() -> None:
    brain = MasterBrain()

    result = brain.process(
        "Explain SAHIBEX architecture."
    )

    # The default mock provider intentionally echoes its prompt; the
    # answer-quality gate must reject it while preserving diagnostics.
    assert result.success is False
    assert result.verification_status == "QUALITY_REJECTED"
    assert result.metadata["failure_stage"] == "mother_operational"
    assert result.intent == "explain"

    context = result.metadata[
        "mother_decision_context"
    ]

    assert context["request"] == (
        "Explain SAHIBEX architecture."
    )
    assert context["intent"] == "explain"
    assert "conversation" in context
    assert "memory_count" in context
    assert "knowledge_count" in context
    assert "memory_ids" in context
    assert "knowledge_ids" in context
    assert context["retrieval_id"]
    assert context["retrieval_summary"]
    assert context["research_available"] is True
    assert context["learning_available"] is True


def test_mother_decision_context_is_read_only_snapshot() -> None:
    context = MotherDecisionContext(
        request="test request",
        intent="explain",
        conversation_summary={
            "turn_count": 0,
            "recent_intents": [],
        },
        memory_ids=("memory-1",),
        knowledge_ids=("knowledge-1",),
        memory_items=("memory-item",),
        knowledge_items=("knowledge-item",),
        retrieval_id="retrieval-1",
        retrieval_summary="Test retrieval.",
    )

    assert context.memory_count == 1
    assert context.knowledge_count == 1

    summary = context.summary()

    assert summary["memory_count"] == 1
    assert summary["knowledge_count"] == 1
    assert summary["retrieval_id"] == "retrieval-1"


if __name__ == "__main__":
    test_master_brain_combined_decision_context()
    test_mother_decision_context_is_read_only_snapshot()
    print(
        "SAHIBEX MASTER BRAIN DECISION CONTEXT TEST: PASS"
    )
