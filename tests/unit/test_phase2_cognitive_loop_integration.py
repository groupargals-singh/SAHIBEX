from __future__ import annotations

from core.brain.master_brain import MasterBrain


def test_fast_path_includes_perception_attention_and_working_memory_trace():
    brain = MasterBrain()
    result = brain.process("sahibaks kya hai?")

    assert result.success is True
    assert result.verification_status == "CURATED_KNOWLEDGE"
    assert result.metadata["input_understanding"]["original_text"] == "sahibaks kya hai?"
    attention = result.metadata["cognitive_attention"]
    assert attention["decision"] in {"focus", "hold", "ignore"}
    assert attention["advisory_only"] is True
    assert attention["permission_granted"] is False
    assert attention["action_executed"] is False
    assert attention["execution_gated_by_attention"] is False
    working = result.metadata["working_memory"]
    assert working["bounded"] is True
    assert working["active_count"] >= 1
    assert working["long_term_storage"] is False
    assert working["grants_permission"] is False


def test_normal_master_brain_path_preserves_input_trace_and_cognitive_snapshot():
    brain = MasterBrain()
    result = brain.process("Please explain the purpose of an attention system.")

    assert "input_understanding" in result.metadata
    assert result.metadata["input_understanding"]["raw_input_preserved"] is True
    assert "cognitive_attention" in result.metadata
    assert "working_memory" in result.metadata
    assert result.metadata["cognitive_attention"]["execution_gated_by_attention"] is False


def test_attention_is_advisory_and_never_changes_permission_or_execution():
    brain = MasterBrain()
    result = brain.process("Please explain a general concept.")

    attention = result.metadata["cognitive_attention"]
    assert attention["advisory_only"] is True
    assert attention["execution_gated_by_attention"] is False
    assert result.permission_allowed is not None
    assert result.metadata["cognitive_attention"]["permission_granted"] is False
