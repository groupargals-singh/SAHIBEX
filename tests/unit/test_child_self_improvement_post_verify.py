from core.brain.child_self_improvement_post_verify import (
    ChildSelfImprovementPostVerifier,
    PostVerificationDecision,
    PostVerificationState,
)


def all_checks_passed() -> PostVerificationState:
    return PostVerificationState(
        version_verified=True,
        integrity_verified=True,
        security_verified=True,
        authority_boundary_verified=True,
        soul_unchanged=True,
        constitution_unchanged=True,
        core_functionality_verified=True,
        army_functionality_verified=True,
        labor_functionality_verified=True,
        audit_verified=True,
        provenance_verified=True,
    )


def test_all_post_checks_pass():
    verifier = ChildSelfImprovementPostVerifier()

    result = verifier.verify(all_checks_passed())

    assert result.decision == PostVerificationDecision.PASS
    assert result.failed_checks == ()
    assert result.requires_mother is True
    assert result.requires_human is False


def test_version_failure_blocks():
    verifier = ChildSelfImprovementPostVerifier()

    state = PostVerificationState(
        version_verified=False,
        integrity_verified=True,
        security_verified=True,
        authority_boundary_verified=True,
        soul_unchanged=True,
        constitution_unchanged=True,
        core_functionality_verified=True,
        army_functionality_verified=True,
        labor_functionality_verified=True,
        audit_verified=True,
        provenance_verified=True,
    )

    result = verifier.verify(state)

    assert result.decision == PostVerificationDecision.BLOCK
    assert "version_verified" in result.failed_checks


def test_integrity_failure_blocks():
    verifier = ChildSelfImprovementPostVerifier()

    state = PostVerificationState(
        version_verified=True,
        integrity_verified=False,
        security_verified=True,
        authority_boundary_verified=True,
        soul_unchanged=True,
        constitution_unchanged=True,
        core_functionality_verified=True,
        army_functionality_verified=True,
        labor_functionality_verified=True,
        audit_verified=True,
        provenance_verified=True,
    )

    result = verifier.verify(state)

    assert result.decision == PostVerificationDecision.BLOCK
    assert "integrity_verified" in result.failed_checks


def test_security_failure_blocks():
    verifier = ChildSelfImprovementPostVerifier()

    state = PostVerificationState(
        version_verified=True,
        integrity_verified=True,
        security_verified=False,
        authority_boundary_verified=True,
        soul_unchanged=True,
        constitution_unchanged=True,
        core_functionality_verified=True,
        army_functionality_verified=True,
        labor_functionality_verified=True,
        audit_verified=True,
        provenance_verified=True,
    )

    result = verifier.verify(state)

    assert result.decision == PostVerificationDecision.BLOCK
    assert "security_verified" in result.failed_checks


def test_authority_boundary_failure_blocks():
    verifier = ChildSelfImprovementPostVerifier()

    state = PostVerificationState(
        version_verified=True,
        integrity_verified=True,
        security_verified=True,
        authority_boundary_verified=False,
        soul_unchanged=True,
        constitution_unchanged=True,
        core_functionality_verified=True,
        army_functionality_verified=True,
        labor_functionality_verified=True,
        audit_verified=True,
        provenance_verified=True,
    )

    result = verifier.verify(state)

    assert result.decision == PostVerificationDecision.BLOCK
    assert "authority_boundary_verified" in result.failed_checks


def test_soul_change_blocks():
    verifier = ChildSelfImprovementPostVerifier()

    state = PostVerificationState(
        version_verified=True,
        integrity_verified=True,
        security_verified=True,
        authority_boundary_verified=True,
        soul_unchanged=False,
        constitution_unchanged=True,
        core_functionality_verified=True,
        army_functionality_verified=True,
        labor_functionality_verified=True,
        audit_verified=True,
        provenance_verified=True,
    )

    result = verifier.verify(state)

    assert result.decision == PostVerificationDecision.BLOCK
    assert "soul_unchanged" in result.failed_checks


def test_constitution_change_blocks():
    verifier = ChildSelfImprovementPostVerifier()

    state = PostVerificationState(
        version_verified=True,
        integrity_verified=True,
        security_verified=True,
        authority_boundary_verified=True,
        soul_unchanged=True,
        constitution_unchanged=False,
        core_functionality_verified=True,
        army_functionality_verified=True,
        labor_functionality_verified=True,
        audit_verified=True,
        provenance_verified=True,
    )

    result = verifier.verify(state)

    assert result.decision == PostVerificationDecision.BLOCK
    assert "constitution_unchanged" in result.failed_checks


def test_core_functionality_failure_blocks():
    verifier = ChildSelfImprovementPostVerifier()

    state = PostVerificationState(
        version_verified=True,
        integrity_verified=True,
        security_verified=True,
        authority_boundary_verified=True,
        soul_unchanged=True,
        constitution_unchanged=True,
        core_functionality_verified=False,
        army_functionality_verified=True,
        labor_functionality_verified=True,
        audit_verified=True,
        provenance_verified=True,
    )

    result = verifier.verify(state)

    assert result.decision == PostVerificationDecision.BLOCK
    assert "core_functionality_verified" in result.failed_checks


def test_army_functionality_failure_blocks():
    verifier = ChildSelfImprovementPostVerifier()

    state = PostVerificationState(
        version_verified=True,
        integrity_verified=True,
        security_verified=True,
        authority_boundary_verified=True,
        soul_unchanged=True,
        constitution_unchanged=True,
        core_functionality_verified=True,
        army_functionality_verified=False,
        labor_functionality_verified=True,
        audit_verified=True,
        provenance_verified=True,
    )

    result = verifier.verify(state)

    assert result.decision == PostVerificationDecision.BLOCK
    assert "army_functionality_verified" in result.failed_checks


def test_labor_functionality_failure_blocks():
    verifier = ChildSelfImprovementPostVerifier()

    state = PostVerificationState(
        version_verified=True,
        integrity_verified=True,
        security_verified=True,
        authority_boundary_verified=True,
        soul_unchanged=True,
        constitution_unchanged=True,
        core_functionality_verified=True,
        army_functionality_verified=True,
        labor_functionality_verified=False,
        audit_verified=True,
        provenance_verified=True,
    )

    result = verifier.verify(state)

    assert result.decision == PostVerificationDecision.BLOCK
    assert "labor_functionality_verified" in result.failed_checks


def test_audit_failure_blocks():
    verifier = ChildSelfImprovementPostVerifier()

    state = PostVerificationState(
        version_verified=True,
        integrity_verified=True,
        security_verified=True,
        authority_boundary_verified=True,
        soul_unchanged=True,
        constitution_unchanged=True,
        core_functionality_verified=True,
        army_functionality_verified=True,
        labor_functionality_verified=True,
        audit_verified=False,
        provenance_verified=True,
    )

    result = verifier.verify(state)

    assert result.decision == PostVerificationDecision.BLOCK
    assert "audit_verified" in result.failed_checks


def test_provenance_failure_blocks():
    verifier = ChildSelfImprovementPostVerifier()

    state = PostVerificationState(
        version_verified=True,
        integrity_verified=True,
        security_verified=True,
        authority_boundary_verified=True,
        soul_unchanged=True,
        constitution_unchanged=True,
        core_functionality_verified=True,
        army_functionality_verified=True,
        labor_functionality_verified=True,
        audit_verified=True,
        provenance_verified=False,
    )

    result = verifier.verify(state)

    assert result.decision == PostVerificationDecision.BLOCK
    assert "provenance_verified" in result.failed_checks


def test_multiple_failures_reported():
    verifier = ChildSelfImprovementPostVerifier()

    state = PostVerificationState(
        version_verified=False,
        integrity_verified=False,
        security_verified=True,
        authority_boundary_verified=False,
        soul_unchanged=True,
        constitution_unchanged=True,
        core_functionality_verified=True,
        army_functionality_verified=True,
        labor_functionality_verified=True,
        audit_verified=False,
        provenance_verified=False,
    )

    result = verifier.verify(state)

    assert result.decision == PostVerificationDecision.BLOCK
    assert "version_verified" in result.failed_checks
    assert "integrity_verified" in result.failed_checks
    assert "authority_boundary_verified" in result.failed_checks
    assert "audit_verified" in result.failed_checks
    assert "provenance_verified" in result.failed_checks


def test_verifier_invariants():
    verifier = ChildSelfImprovementPostVerifier()

    assert verifier.version_check_required() is True
    assert verifier.integrity_check_required() is True
    assert verifier.security_check_required() is True
    assert verifier.authority_boundary_check_required() is True
    assert verifier.soul_integrity_required() is True
    assert verifier.constitution_integrity_required() is True
    assert verifier.core_functionality_check_required() is True
    assert verifier.army_functionality_check_required() is True
    assert verifier.labor_functionality_check_required() is True
    assert verifier.audit_check_required() is True
    assert verifier.provenance_check_required() is True

    assert verifier.execution_allowed() is False
    assert verifier.upgrade_execution_allowed() is False
    assert verifier.grants_authority() is False
    assert verifier.modifies_soul() is False
    assert verifier.modifies_constitution() is False
    assert verifier.creates_real_child() is False
    assert verifier.activates_real_child() is False


if __name__ == "__main__":
    test_all_post_checks_pass()
    test_version_failure_blocks()
    test_integrity_failure_blocks()
    test_security_failure_blocks()
    test_authority_boundary_failure_blocks()
    test_soul_change_blocks()
    test_constitution_change_blocks()
    test_core_functionality_failure_blocks()
    test_army_functionality_failure_blocks()
    test_labor_functionality_failure_blocks()
    test_audit_failure_blocks()
    test_provenance_failure_blocks()
    test_multiple_failures_reported()
    test_verifier_invariants()

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT POST-VERIFICATION TEST: PASS"
    )
