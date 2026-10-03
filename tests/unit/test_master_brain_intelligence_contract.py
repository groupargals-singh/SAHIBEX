from __future__ import annotations

from core.brain.master_intelligence import (
    MasterBrainIntelligence,
    MasterBrainIntelligenceResult,
)


def main() -> None:
    intelligence = MasterBrainIntelligence()

    result = intelligence.aggregate(
        intent="research",
        brain_id="brain-research-001",
        memory_ids=[
            "memory-001",
        ],
        knowledge_ids=[
            "knowledge-001",
        ],
        tool_name="search_local_files",
        modalities=[
            "text",
        ],
        verification_id="verification-001",
        trust_status="trusted",
        confidence=0.92,
        allowed=True,
        requires_confirmation=False,
        summary="Research context is ready for the master brain.",
    )

    assert isinstance(
        result,
        MasterBrainIntelligenceResult,
    )

    assert result.success is True
    assert result.intent == "research"
    assert result.brain_id == "brain-research-001"
    assert result.memory_ids == [
        "memory-001",
    ]
    assert result.knowledge_ids == [
        "knowledge-001",
    ]
    assert result.tool_name == "search_local_files"
    assert result.modalities == [
        "text",
    ]
    assert result.verification_id == "verification-001"
    assert result.trust_status == "trusted"
    assert result.confidence == 0.92
    assert result.allowed is True
    assert result.requires_confirmation is False
    assert result.summary == (
        "Research context is ready for the master brain."
    )
    assert result.intelligence_id

    second_result = intelligence.aggregate(
        intent="write",
        brain_id="brain-code-001",
        memory_ids=["memory-002"],
        knowledge_ids=["knowledge-002"],
        tool_name="write_file",
        modalities=["text", "voice"],
        verification_id="verification-002",
        trust_status="verified",
        confidence=0.80,
        allowed=False,
        requires_confirmation=True,
        summary="Protected action requires user confirmation.",
    )

    assert second_result.success is True
    assert second_result.allowed is False
    assert second_result.requires_confirmation is True
    assert second_result.intelligence_id != (
        result.intelligence_id
    )

    try:
        intelligence.aggregate(
            intent="",
            brain_id="brain-001",
            memory_ids=["memory-001"],
            knowledge_ids=["knowledge-001"],
            tool_name="read_file",
            modalities=["text"],
            verification_id="verification-001",
            trust_status="trusted",
            confidence=0.90,
            allowed=True,
            requires_confirmation=False,
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty intent must be rejected."
        )

    try:
        intelligence.aggregate(
            intent="research",
            brain_id="",
            memory_ids=["memory-001"],
            knowledge_ids=["knowledge-001"],
            tool_name="read_file",
            modalities=["text"],
            verification_id="verification-001",
            trust_status="trusted",
            confidence=0.90,
            allowed=True,
            requires_confirmation=False,
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty brain ID must be rejected."
        )

    try:
        intelligence.aggregate(
            intent="research",
            brain_id="brain-001",
            memory_ids=[],
            knowledge_ids=["knowledge-001"],
            tool_name="read_file",
            modalities=["text"],
            verification_id="verification-001",
            trust_status="trusted",
            confidence=0.90,
            allowed=True,
            requires_confirmation=False,
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty memory IDs must be rejected."
        )

    try:
        intelligence.aggregate(
            intent="research",
            brain_id="brain-001",
            memory_ids=["memory-001"],
            knowledge_ids=[],
            tool_name="read_file",
            modalities=["text"],
            verification_id="verification-001",
            trust_status="trusted",
            confidence=0.90,
            allowed=True,
            requires_confirmation=False,
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty knowledge IDs must be rejected."
        )

    try:
        intelligence.aggregate(
            intent="research",
            brain_id="brain-001",
            memory_ids=["memory-001"],
            knowledge_ids=["knowledge-001"],
            tool_name="",
            modalities=["text"],
            verification_id="verification-001",
            trust_status="trusted",
            confidence=0.90,
            allowed=True,
            requires_confirmation=False,
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty tool name must be rejected."
        )

    try:
        intelligence.aggregate(
            intent="research",
            brain_id="brain-001",
            memory_ids=["memory-001"],
            knowledge_ids=["knowledge-001"],
            tool_name="read_file",
            modalities=[],
            verification_id="verification-001",
            trust_status="trusted",
            confidence=0.90,
            allowed=True,
            requires_confirmation=False,
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty modalities must be rejected."
        )

    try:
        intelligence.aggregate(
            intent="research",
            brain_id="brain-001",
            memory_ids=["memory-001"],
            knowledge_ids=["knowledge-001"],
            tool_name="read_file",
            modalities=["text"],
            verification_id="verification-001",
            trust_status="trusted",
            confidence=1.1,
            allowed=True,
            requires_confirmation=False,
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Confidence above 1 must be rejected."
        )

    try:
        intelligence.aggregate(
            intent="research",
            brain_id="brain-001",
            memory_ids=["memory-001"],
            knowledge_ids=["knowledge-001"],
            tool_name="read_file",
            modalities=["text"],
            verification_id="verification-001",
            trust_status="trusted",
            confidence=0.90,
            allowed=True,
            requires_confirmation=False,
            summary="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty summary must be rejected."
        )

    fields = MasterBrainIntelligenceResult.__dataclass_fields__

    forbidden_fields = {
        "api_key",
        "credential",
        "authorization_token",
        "permission_grant",
    }

    assert forbidden_fields.isdisjoint(fields.keys())

    assert not hasattr(
        MasterBrainIntelligence,
        "grant_permission",
    )

    assert not hasattr(
        MasterBrainIntelligence,
        "execute_action",
    )

    assert not hasattr(
        MasterBrainIntelligence,
        "override_constitution",
    )

    print(
        "SAHIBEX 6N-9 MASTER BRAIN INTELLIGENCE "
        "CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
