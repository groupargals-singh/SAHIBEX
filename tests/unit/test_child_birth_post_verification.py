from core.brain.child_birth_post_verification import (
    ChildBirthPostVerification,
    ChildBirthPostVerificationRequest,
    PostBirthDecision,
)


def make_request(**overrides):
    values = {
        "brain_id": "child-brain-001",
        "soul_id": "child-soul-001",
        "constitution_id": "child-constitution-001",
        "memory_namespace": "child-memory-001",
        "security_identity": "child-security-001",
        "audit_identity": "child-audit-001",
        "identity_verified": True,
        "soul_verified": True,
        "constitution_verified": True,
        "memory_isolated": True,
        "security_isolated": True,
        "audit_enabled": True,
        "authority_boundaries_verified": True,
        "no_forbidden_inheritance": True,
    }

    values.update(overrides)
    return ChildBirthPostVerificationRequest(**values)


def main() -> None:
    verifier = ChildBirthPostVerification()

    result = verifier.verify(make_request())

    assert result.allowed is True
    assert result.decision == PostBirthDecision.VERIFIED

    result = verifier.verify(
        make_request(identity_verified=False)
    )
    assert result.allowed is False

    result = verifier.verify(
        make_request(soul_verified=False)
    )
    assert result.allowed is False

    result = verifier.verify(
        make_request(constitution_verified=False)
    )
    assert result.allowed is False

    result = verifier.verify(
        make_request(memory_isolated=False)
    )
    assert result.allowed is False

    result = verifier.verify(
        make_request(security_isolated=False)
    )
    assert result.allowed is False

    result = verifier.verify(
        make_request(audit_enabled=False)
    )
    assert result.allowed is False

    result = verifier.verify(
        make_request(authority_boundaries_verified=False)
    )
    assert result.allowed is False

    result = verifier.verify(
        make_request(no_forbidden_inheritance=False)
    )
    assert result.allowed is False

    result = verifier.verify(
        make_request(brain_id="")
    )
    assert result.allowed is False

    assert verifier.can_mark_child_verified()
    assert not verifier.can_activate_child()
    assert not verifier.can_create_child()
    assert not verifier.can_modify_soul()
    assert not verifier.can_modify_constitution()
    assert not verifier.can_grant_authority()
    assert verifier.requires_all_checks()
    assert verifier.fails_closed()

    print("SAHIBEX CHILD BIRTH POST-VERIFICATION TEST: PASS")


if __name__ == "__main__":
    main()
