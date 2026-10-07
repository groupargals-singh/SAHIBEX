from core.brain.child_verification_trust_boundary import (
    ChildVerificationTrustBoundary,
    TrustLevel,
    VerificationActor,
    VerificationDecision,
    VerificationOperation,
)


def main() -> None:
    boundary = ChildVerificationTrustBoundary

    # Child, Army and Labor can verify independently.
    for actor in (
        VerificationActor.CHILD_BRAIN,
        VerificationActor.CHILD_ARMY,
        VerificationActor.CHILD_LABOR,
    ):
        result = boundary.decide(
            actor,
            VerificationOperation.SUBMIT_EVIDENCE,
        )

        assert result.allowed
        assert result.trust_level == TrustLevel.UNVERIFIED
        assert not result.authority_granted

        result = boundary.decide(
            actor,
            VerificationOperation.VERIFY_EVIDENCE,
            evidence_verified=True,
        )

        assert result.allowed
        assert result.trust_level == TrustLevel.VERIFIED
        assert not result.authority_granted

    # Unverified result cannot be accepted as trusted.
    result = boundary.decide(
        VerificationActor.CHILD_BRAIN,
        VerificationOperation.ACCEPT_RESULT,
        current_trust=TrustLevel.UNVERIFIED,
    )

    assert not result.allowed
    assert result.decision == VerificationDecision.REQUIRE_VERIFICATION

    # Conflicted result cannot be accepted as trusted.
    result = boundary.decide(
        VerificationActor.CHILD_BRAIN,
        VerificationOperation.ACCEPT_RESULT,
        current_trust=TrustLevel.CONFLICTED,
    )

    assert not result.allowed

    # Trusted marking requires authority.
    result = boundary.decide(
        VerificationActor.CHILD_BRAIN,
        VerificationOperation.MARK_TRUSTED,
        current_trust=TrustLevel.VERIFIED,
        evidence_verified=True,
    )

    assert not result.allowed
    assert result.decision == VerificationDecision.REQUIRE_AUTHORITY

    result = boundary.decide(
        VerificationActor.CHILD_BRAIN,
        VerificationOperation.MARK_TRUSTED,
        current_trust=TrustLevel.VERIFIED,
        evidence_verified=True,
        authority_approved=True,
    )

    assert result.allowed
    assert result.trust_level == TrustLevel.TRUSTED
    assert result.authority_granted

    # Internal Army cannot override verification.
    result = boundary.decide(
        VerificationActor.CHILD_ARMY,
        VerificationOperation.OVERRIDE_VERIFICATION,
    )

    assert not result.allowed
    assert result.decision == VerificationDecision.DENY

    # External actors can submit information but cannot become authority.
    for actor in (
        VerificationActor.SOFTWARE,
        VerificationActor.TOOL,
        VerificationActor.EXTERNAL_MODEL,
    ):
        result = boundary.decide(
            actor,
            VerificationOperation.SUBMIT_EVIDENCE,
        )

        assert result.allowed
        assert result.trust_level == TrustLevel.UNVERIFIED
        assert not result.authority_granted

        result = boundary.decide(
            actor,
            VerificationOperation.MARK_TRUSTED,
            current_trust=TrustLevel.VERIFIED,
            evidence_verified=True,
            authority_approved=True,
        )

        assert not result.allowed

    # Constitutional guarantees.
    assert boundary.can_child_verify_independently()
    assert boundary.can_army_verify_independently()
    assert boundary.can_labor_verify_independently()

    assert not boundary.unverified_knowledge_can_be_trusted()
    assert not boundary.conflicted_knowledge_can_be_trusted()
    assert not boundary.rejected_knowledge_can_be_trusted()

    assert not boundary.verification_creates_execution_authority()
    assert not boundary.capability_creates_trust()
    assert not boundary.self_declared_trust_is_valid()
    assert not boundary.external_model_is_verification_authority()
    assert not boundary.verification_override_without_authority()

    assert boundary.verification_failure_blocks_trust()
    assert boundary.unknown_state_fails_closed()

    assert not boundary.creates_child_brain()
    assert not boundary.activates_child_brain()
    assert not boundary.executes_actions()

    print("SAHIBEX CHILD VERIFICATION & TRUST BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
