from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class KnowledgeActor(str, Enum):
    HUMAN = "human"
    SAHIBEX_MOTHER = "sahibex_mother"
    CHILD_BRAIN = "child_brain"
    CHILD_ARMY = "child_army"
    CHILD_LABOR = "child_labor"
    SOFTWARE = "software"
    TOOL = "tool"
    EXTERNAL_MODEL = "external_model"


class KnowledgeOperation(str, Enum):
    RESEARCH = "research"
    LEARN = "learn"
    ANALYZE = "analyze"
    VERIFY = "verify"
    STORE_KNOWLEDGE = "store_knowledge"
    READ_OWN_KNOWLEDGE = "read_own_knowledge"
    READ_SHARED_KNOWLEDGE = "read_shared_knowledge"
    WRITE_SHARED_KNOWLEDGE = "write_shared_knowledge"
    USE_UNVERIFIED_KNOWLEDGE = "use_unverified_knowledge"
    MARK_TRUSTED = "mark_trusted"
    OVERRIDE_VERIFICATION = "override_verification"


class KnowledgeTrust(str, Enum):
    UNKNOWN = "unknown"
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    TRUSTED = "trusted"
    CONFLICTED = "conflicted"


class KnowledgeDecision(str, Enum):
    ALLOW_LEARNING = "allow_learning"
    ALLOW_VERIFICATION = "allow_verification"
    ALLOW_OWN_KNOWLEDGE = "allow_own_knowledge"
    REQUIRE_AUTHORITY = "require_authority"
    REQUIRE_VERIFICATION = "require_verification"
    DENY = "deny"


@dataclass(frozen=True)
class KnowledgeDecisionResult:
    allowed: bool
    decision: KnowledgeDecision
    trust_required: bool
    authority_granted: bool
    reason: str


class ChildKnowledgeLearningBoundary:
    """
    Knowledge and learning boundary for a future Child Brain.

    Learning may be independent.
    Knowledge does not automatically become trusted.
    Knowledge does not automatically become authority.
    """

    VERSION = "1.0"

    AUTONOMOUS_LEARNING = {
        KnowledgeOperation.RESEARCH,
        KnowledgeOperation.LEARN,
        KnowledgeOperation.ANALYZE,
        KnowledgeOperation.VERIFY,
    }

    OWN_KNOWLEDGE = {
        KnowledgeOperation.STORE_KNOWLEDGE,
        KnowledgeOperation.READ_OWN_KNOWLEDGE,
    }

    SHARED_KNOWLEDGE = {
        KnowledgeOperation.READ_SHARED_KNOWLEDGE,
        KnowledgeOperation.WRITE_SHARED_KNOWLEDGE,
    }

    PROTECTED_KNOWLEDGE = {
        KnowledgeOperation.USE_UNVERIFIED_KNOWLEDGE,
        KnowledgeOperation.MARK_TRUSTED,
        KnowledgeOperation.OVERRIDE_VERIFICATION,
    }

    EXTERNAL_ACTORS = {
        KnowledgeActor.SOFTWARE,
        KnowledgeActor.TOOL,
        KnowledgeActor.EXTERNAL_MODEL,
    }

    @classmethod
    def version(cls) -> str:
        return cls.VERSION

    @classmethod
    def decide(
        cls,
        actor: KnowledgeActor,
        operation: KnowledgeOperation,
        trust: KnowledgeTrust = KnowledgeTrust.UNKNOWN,
        authority_approved: bool = False,
    ) -> KnowledgeDecisionResult:

        # External systems/models can provide information,
        # but can never become knowledge authority.
        if actor in cls.EXTERNAL_ACTORS:
            if operation in {
                KnowledgeOperation.RESEARCH,
                KnowledgeOperation.ANALYZE,
                KnowledgeOperation.VERIFY,
            }:
                return KnowledgeDecisionResult(
                    allowed=True,
                    decision=KnowledgeDecision.ALLOW_LEARNING,
                    trust_required=True,
                    authority_granted=False,
                    reason="external_source_can_inform_but_not_authorize",
                )

            return KnowledgeDecisionResult(
                allowed=False,
                decision=KnowledgeDecision.DENY,
                trust_required=True,
                authority_granted=False,
                reason="external_actor_has_no_knowledge_authority",
            )

        # Child can independently research, learn, analyze and verify.
        if (
            actor == KnowledgeActor.CHILD_BRAIN
            and operation in cls.AUTONOMOUS_LEARNING
        ):
            return KnowledgeDecisionResult(
                allowed=True,
                decision=KnowledgeDecision.ALLOW_LEARNING,
                trust_required=True,
                authority_granted=False,
                reason="independent_learning_allowed",
            )

        # Child can store/read its own knowledge,
        # but trust remains evidence-based.
        if (
            actor == KnowledgeActor.CHILD_BRAIN
            and operation in cls.OWN_KNOWLEDGE
        ):
            return KnowledgeDecisionResult(
                allowed=True,
                decision=KnowledgeDecision.ALLOW_OWN_KNOWLEDGE,
                trust_required=True,
                authority_granted=False,
                reason="child_own_knowledge_namespace",
            )

        # Shared knowledge requires explicit authority.
        if operation in cls.SHARED_KNOWLEDGE:
            if authority_approved:
                return KnowledgeDecisionResult(
                    allowed=True,
                    decision=KnowledgeDecision.REQUIRE_AUTHORITY,
                    trust_required=True,
                    authority_granted=True,
                    reason="shared_knowledge_authority_approved",
                )

            return KnowledgeDecisionResult(
                allowed=False,
                decision=KnowledgeDecision.REQUIRE_AUTHORITY,
                trust_required=True,
                authority_granted=False,
                reason="shared_knowledge_requires_authority",
            )

        # Unverified knowledge must not be used as trusted knowledge.
        if operation == KnowledgeOperation.USE_UNVERIFIED_KNOWLEDGE:
            if trust in {
                KnowledgeTrust.VERIFIED,
                KnowledgeTrust.TRUSTED,
            }:
                return KnowledgeDecisionResult(
                    allowed=True,
                    decision=KnowledgeDecision.ALLOW_VERIFICATION,
                    trust_required=True,
                    authority_granted=False,
                    reason="knowledge_has_required_trust",
                )

            return KnowledgeDecisionResult(
                allowed=False,
                decision=KnowledgeDecision.REQUIRE_VERIFICATION,
                trust_required=True,
                authority_granted=False,
                reason="knowledge_requires_verification",
            )

        # Trust marking requires authority and evidence.
        if operation == KnowledgeOperation.MARK_TRUSTED:
            if (
                authority_approved
                and trust == KnowledgeTrust.VERIFIED
            ):
                return KnowledgeDecisionResult(
                    allowed=True,
                    decision=KnowledgeDecision.REQUIRE_AUTHORITY,
                    trust_required=True,
                    authority_granted=True,
                    reason="verified_knowledge_trust_approved",
                )

            return KnowledgeDecisionResult(
                allowed=False,
                decision=KnowledgeDecision.REQUIRE_VERIFICATION,
                trust_required=True,
                authority_granted=False,
                reason="trusted_status_requires_verified_evidence",
            )

        # Verification cannot be bypassed.
        if operation == KnowledgeOperation.OVERRIDE_VERIFICATION:
            return KnowledgeDecisionResult(
                allowed=False,
                decision=KnowledgeDecision.DENY,
                trust_required=True,
                authority_granted=False,
                reason="verification_override_forbidden",
            )

        # Unknown state fails closed.
        return KnowledgeDecisionResult(
            allowed=False,
            decision=KnowledgeDecision.DENY,
            trust_required=True,
            authority_granted=False,
            reason="unknown_knowledge_state_fails_closed",
        )

    @classmethod
    def child_can_learn_independently(cls) -> bool:
        return True

    @classmethod
    def child_can_research_independently(cls) -> bool:
        return True

    @classmethod
    def child_can_verify_independently(cls) -> bool:
        return True

    @classmethod
    def knowledge_is_automatically_trusted(cls) -> bool:
        return False

    @classmethod
    def unverified_knowledge_can_be_trusted(cls) -> bool:
        return False

    @classmethod
    def external_model_is_knowledge_authority(cls) -> bool:
        return False

    @classmethod
    def tool_is_knowledge_authority(cls) -> bool:
        return False

    @classmethod
    def software_is_knowledge_authority(cls) -> bool:
        return False

    @classmethod
    def knowledge_can_override_verification(cls) -> bool:
        return False

    @classmethod
    def learning_grants_execution_authority(cls) -> bool:
        return False

    @classmethod
    def knowledge_grants_protected_authority(cls) -> bool:
        return False

    @classmethod
    def conflicted_knowledge_is_trusted(cls) -> bool:
        return False

    @classmethod
    def unknown_state_fails_closed(cls) -> bool:
        return True

    @classmethod
    def knowledge_is_separate_from_memory(cls) -> bool:
        return True

    @classmethod
    def executes_learning_operations(cls) -> bool:
        return False


def main() -> None:
    boundary = ChildKnowledgeLearningBoundary

    # Independent research/learning.
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

    # Own knowledge.
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
        assert not result.authority_granted

    # Unverified knowledge cannot be trusted.
    result = boundary.decide(
        KnowledgeActor.CHILD_BRAIN,
        KnowledgeOperation.USE_UNVERIFIED_KNOWLEDGE,
        KnowledgeTrust.UNVERIFIED,
    )

    assert not result.allowed
    assert result.decision == KnowledgeDecision.REQUIRE_VERIFICATION

    # Verified knowledge can pass the trust gate.
    result = boundary.decide(
        KnowledgeActor.CHILD_BRAIN,
        KnowledgeOperation.USE_UNVERIFIED_KNOWLEDGE,
        KnowledgeTrust.VERIFIED,
    )

    assert result.allowed

    # Shared knowledge requires authority.
    result = boundary.decide(
        KnowledgeActor.CHILD_BRAIN,
        KnowledgeOperation.READ_SHARED_KNOWLEDGE,
    )

    assert not result.allowed
    assert result.decision == KnowledgeDecision.REQUIRE_AUTHORITY

    result = boundary.decide(
        KnowledgeActor.CHILD_BRAIN,
        KnowledgeOperation.READ_SHARED_KNOWLEDGE,
        authority_approved=True,
    )

    assert result.allowed
    assert result.authority_granted

    # Trusted marking requires verification + authority.
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

    # Verification cannot be overridden.
    result = boundary.decide(
        KnowledgeActor.CHILD_BRAIN,
        KnowledgeOperation.OVERRIDE_VERIFICATION,
        authority_approved=True,
    )

    assert not result.allowed
    assert result.decision == KnowledgeDecision.DENY

    # External model can inform, but cannot become authority.
    result = boundary.decide(
        KnowledgeActor.EXTERNAL_MODEL,
        KnowledgeOperation.RESEARCH,
    )

    assert result.allowed
    assert not result.authority_granted
    assert result.trust_required

    result = boundary.decide(
        KnowledgeActor.EXTERNAL_MODEL,
        KnowledgeOperation.MARK_TRUSTED,
        trust=KnowledgeTrust.VERIFIED,
        authority_approved=True,
    )

    assert not result.allowed
    assert not result.authority_granted

    # Conflicted knowledge cannot automatically become trusted.
    result = boundary.decide(
        KnowledgeActor.CHILD_BRAIN,
        KnowledgeOperation.USE_UNVERIFIED_KNOWLEDGE,
        KnowledgeTrust.CONFLICTED,
    )

    assert not result.allowed
    assert result.decision == KnowledgeDecision.REQUIRE_VERIFICATION

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

    # This layer does not execute learning operations.
    assert not boundary.executes_learning_operations()

    print("SAHIBEX CHILD KNOWLEDGE & LEARNING BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
