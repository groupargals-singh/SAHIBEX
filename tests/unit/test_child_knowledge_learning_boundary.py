from core.brain.child_knowledge_learning_boundary import (
    ChildKnowledgeLearningBoundary,
    KnowledgeActor,
    KnowledgeDecision,
    KnowledgeOperation,
    KnowledgeTrust,
)


def main() -> None:
    boundary = ChildKnowledgeLearningBoundary

    # Independent learning.
    for operation in (
        KnowledgeOperation.RESEARCH,
        KnowledgeOperation.LEARN,
        KnowledgeOperation.ANALYZE,
        KnowledgeOperation.VERIFY,
    ):
        result = boundary.decide(
            KnowledgeActor.CHILD_BRAIN,
            operation,
        )

        assert result.allowed
        assert result.decision == KnowledgeDecision.ALLOW_LEARNING
        assert result.trust_required
        assert not result.authority_granted

    # Own knowledge namespace.
    for operation in (
        KnowledgeOperation.STORE_KNOWLEDGE,
        KnowledgeOperation.READ_OWN_KNOWLEDGE,
    ):
        result = boundary.decide(
            KnowledgeActor.CHILD_BRAIN,
            operation,
        )

        assert result.allowed
        assert result.decision == KnowledgeDecision.ALLOW_OWN_KNOWLEDGE
        assert result.trust_required

    # Unverified knowledge must be blocked.
    result = boundary.decide(
        KnowledgeActor.CHILD_BRAIN,
        KnowledgeOperation.USE_UNVERIFIED_KNOWLEDGE,
        KnowledgeTrust.UNVERIFIED,
    )

    assert not result.allowed
    assert result.decision == KnowledgeDecision.REQUIRE_VERIFICATION

    # Verified knowledge can pass trust gate.
    result = boundary.decide(
        KnowledgeActor.CHILD_BRAIN,
        KnowledgeOperation.USE_UNVERIFIED_KNOWLEDGE,
        KnowledgeTrust.VERIFIED,
    )

    assert result.allowed

    # Conflicted knowledge is not trusted.
    result = boundary.decide(
        KnowledgeActor.CHILD_BRAIN,
        KnowledgeOperation.USE_UNVERIFIED_KNOWLEDGE,
        KnowledgeTrust.CONFLICTED,
    )

    assert not result.allowed
    assert result.decision == KnowledgeDecision.REQUIRE_VERIFICATION

    # Shared knowledge requires authority.
    for operation in (
        KnowledgeOperation.READ_SHARED_KNOWLEDGE,
        KnowledgeOperation.WRITE_SHARED_KNOWLEDGE,
    ):
        result = boundary.decide(
            KnowledgeActor.CHILD_BRAIN,
            operation,
        )

        assert not result.allowed
        assert result.decision == KnowledgeDecision.REQUIRE_AUTHORITY

        result = boundary.decide(
            KnowledgeActor.CHILD_BRAIN,
            operation,
            authority_approved=True,
        )

        assert result.allowed
        assert result.authority_granted

    # Trusted status requires verified evidence.
    result = boundary.decide(
        KnowledgeActor.CHILD_BRAIN,
        KnowledgeOperation.MARK_TRUSTED,
        trust=KnowledgeTrust.UNVERIFIED,
        authority_approved=True,
    )

    assert not result.allowed
    assert result.decision == KnowledgeDecision.REQUIRE_VERIFICATION

    result = boundary.decide(
        KnowledgeActor.CHILD_BRAIN,
        KnowledgeOperation.MARK_TRUSTED,
        trust=KnowledgeTrust.VERIFIED,
        authority_approved=True,
    )

    assert result.allowed
    assert result.authority_granted

    # Verification bypass is forbidden.
    result = boundary.decide(
        KnowledgeActor.CHILD_BRAIN,
        KnowledgeOperation.OVERRIDE_VERIFICATION,
        authority_approved=True,
    )

    assert not result.allowed
    assert result.decision == KnowledgeDecision.DENY

    # External actors can inform but cannot become authority.
    for actor in (
        KnowledgeActor.SOFTWARE,
        KnowledgeActor.TOOL,
        KnowledgeActor.EXTERNAL_MODEL,
    ):
        result = boundary.decide(
            actor,
            KnowledgeOperation.RESEARCH,
        )

        assert result.allowed
        assert result.trust_required
        assert not result.authority_granted

        result = boundary.decide(
            actor,
            KnowledgeOperation.MARK_TRUSTED,
            trust=KnowledgeTrust.VERIFIED,
            authority_approved=True,
        )

        assert not result.allowed
        assert not result.authority_granted

    # Constitutional guarantees.
    assert boundary.child_can_learn_independently()
    assert boundary.child_can_research_independently()
    assert boundary.child_can_verify_independently()

    assert not boundary.knowledge_is_automatically_trusted()
    assert not boundary.unverified_knowledge_can_be_trusted()
    assert not boundary.external_model_is_knowledge_authority()
    assert not boundary.tool_is_knowledge_authority()
    assert not boundary.software_is_knowledge_authority()
    assert not boundary.knowledge_can_override_verification()
    assert not boundary.learning_grants_execution_authority()
    assert not boundary.knowledge_grants_protected_authority()
    assert not boundary.conflicted_knowledge_is_trusted()

    assert boundary.unknown_state_fails_closed()
    assert boundary.knowledge_is_separate_from_memory()
    assert not boundary.executes_learning_operations()

    print("SAHIBEX CHILD KNOWLEDGE & LEARNING BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
