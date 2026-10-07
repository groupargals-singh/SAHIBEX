from core.brain.child_knowledge_runtime import (
    ChildKnowledgeRuntime,
    KnowledgeDecision,
    KnowledgeOperation,
)


def main() -> None:
    knowledge = ChildKnowledgeRuntime(
        child_brain_id="child-brain-test",
        knowledge_namespace="child-knowledge-test",
    )

    result = knowledge.evaluate(
        KnowledgeOperation.RESEARCH
    )
    assert result.allowed is True

    result = knowledge.evaluate(
        KnowledgeOperation.LEARN
    )
    assert result.allowed is True

    result = knowledge.evaluate(
        KnowledgeOperation.ANALYZE
    )
    assert result.allowed is True

    result = knowledge.store(
        key="python",
        value="Programming language",
        source="verified-source",
        verified=True,
    )
    assert result.allowed is True

    assert knowledge.read("python") == "Programming language"

    result = knowledge.mark_trusted(
        "python",
        authority_approved=False,
    )
    assert result.allowed is False
    assert result.decision == KnowledgeDecision.REQUIRE_AUTHORITY

    result = knowledge.mark_trusted(
        "python",
        authority_approved=True,
    )
    assert result.allowed is True
    assert knowledge.is_trusted("python")

    result = knowledge.store(
        key="unverified",
        value="unknown information",
        source="unknown-source",
        verified=False,
    )
    assert result.allowed is False
    assert result.decision == KnowledgeDecision.REQUIRE_VERIFICATION

    result = knowledge.delete(
        "python",
        authority_approved=False,
    )
    assert result.allowed is False

    result = knowledge.delete(
        "python",
        authority_approved=True,
    )
    assert result.allowed is True
    assert knowledge.read("python") is None

    assert knowledge.can_research_independently()
    assert knowledge.can_learn_independently()
    assert knowledge.can_analyze_independently()
    assert knowledge.can_verify_independently()

    assert not knowledge.external_model_is_authority()
    assert not knowledge.external_tool_is_authority()
    assert not knowledge.knowledge_equals_authority()
    assert not knowledge.unknown_knowledge_is_trusted()

    print("SAHIBEX CHILD KNOWLEDGE RUNTIME TEST: PASS")


if __name__ == "__main__":
    main()
