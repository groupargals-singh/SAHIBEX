from __future__ import annotations

from core.brain.master_brain import MasterBrain
from core.brain.mother_decision_context import (
    MotherDecisionContext,
)


def test_master_brain_combined_decision_context() -> None:
    brain = MasterBrain()
    brain.memory_brain.remember_interaction(
        user_text="We are building the SAHIBEX cognitive loop.",
        assistant_text="Working memory should inform the next reasoning turn.",
        intent="explain",
        action="respond",
        verification_status="STRUCTURALLY_VALID",
    )

    result = brain.process(
        "Explain SAHIBEX architecture."
    )

    # The default mock provider cannot ground this factual explanation.
    # MainBrain must return explicit uncertainty rather than treating a
    # structurally plausible generation as a factual answer.
    assert result.success is True
    assert result.verification_status == "INSUFFICIENT_EVIDENCE"
    assert "enough verified evidence" in result.message.lower()
    assert result.intent == "explain"
    operational = result.metadata["mother_operational_integration"]
    assert operational["factual_verification"] is False
    assert operational["diagnostics"]["uncertainty_disclosed"] is True

    context = result.metadata[
        "mother_decision_context"
    ]

    assert context["request"] == (
        "Explain SAHIBEX architecture."
    )
    assert context["intent"] == "explain"
    assert "conversation_summary" in context
    assert "memory_count" in context
    assert "knowledge_count" in context
    assert "memory_ids" in context
    assert "knowledge_ids" in context
    assert context["retrieval_id"]
    assert context["retrieval_summary"]
    assert context["research_available"] is True
    assert context["learning_available"] is True

    flow = result.metadata["cognitive_flow_trace"]
    assert flow["context_built"] is True
    assert flow["working_memory_available"] is True
    assert flow["working_memory_items_passed"] >= 1
    assert flow["context_passed_to_reasoning"] is True
    assert flow["context_passed_to_planning"] is True
    assert flow["reasoning_context_received"] is True
    assert flow["reasoning_context_reused"] is True
    assert flow["reasoning_assessment_needs_verification"] is True
    assert flow["planning_context_received"] is True
    assert flow["plan_context_aware"] is True
    assert flow["planning_context_reference_count"] >= 1
    assert flow["execution_authority_changed"] is False


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
    assert summary["working_memory_count"] == 0
    assert summary["working_memory_items"] == ()


if __name__ == "__main__":
    test_master_brain_combined_decision_context()
    test_mother_decision_context_is_read_only_snapshot()
    print(
        "SAHIBEX MASTER BRAIN DECISION CONTEXT TEST: PASS"
    )
