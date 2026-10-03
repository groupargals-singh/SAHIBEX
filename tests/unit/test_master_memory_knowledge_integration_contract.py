from __future__ import annotations

from core.brain.memory_knowledge_integration import (
    MasterMemoryKnowledgeIntegration,
    MasterMemoryKnowledgeResult,
)


def main() -> None:
    integration = MasterMemoryKnowledgeIntegration()

    result = integration.integrate(
        memory_ids=[
            "memory-001",
            "memory-002",
        ],
        knowledge_ids=[
            "knowledge-001",
        ],
        summary="Relevant memory and knowledge prepared for the master brain.",
    )

    assert isinstance(
        result,
        MasterMemoryKnowledgeResult,
    )

    assert result.success is True
    assert result.memory_ids == [
        "memory-001",
        "memory-002",
    ]
    assert result.knowledge_ids == [
        "knowledge-001",
    ]
    assert result.summary == (
        "Relevant memory and knowledge prepared for the master brain."
    )
    assert result.integration_id

    second_result = integration.integrate(
        memory_ids=["memory-003"],
        knowledge_ids=["knowledge-002"],
        summary="Additional context prepared.",
    )

    assert second_result.success is True
    assert second_result.integration_id != result.integration_id

    try:
        integration.integrate(
            memory_ids=[],
            knowledge_ids=["knowledge-001"],
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty memory_ids must be rejected."
        )

    try:
        integration.integrate(
            memory_ids=["memory-001"],
            knowledge_ids=[],
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty knowledge_ids must be rejected."
        )

    try:
        integration.integrate(
            memory_ids=[""],
            knowledge_ids=["knowledge-001"],
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty memory ID must be rejected."
        )

    try:
        integration.integrate(
            memory_ids=["memory-001"],
            knowledge_ids=[""],
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty knowledge ID must be rejected."
        )

    try:
        integration.integrate(
            memory_ids=["memory-001"],
            knowledge_ids=["knowledge-001"],
            summary="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty summary must be rejected."
        )

    fields = MasterMemoryKnowledgeResult.__dataclass_fields__

    forbidden_fields = {
        "api_key",
        "credential",
        "authorization_token",
        "permission_grant",
    }

    assert forbidden_fields.isdisjoint(fields.keys())

    assert not hasattr(
        MasterMemoryKnowledgeIntegration,
        "grant_permission",
    )

    assert not hasattr(
        MasterMemoryKnowledgeIntegration,
        "delete_memory",
    )

    print(
        "SAHIBEX 6N-4 MEMORY KNOWLEDGE INTEGRATION CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
