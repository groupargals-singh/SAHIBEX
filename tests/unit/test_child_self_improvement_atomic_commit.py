from core.brain.child_self_improvement_atomic_commit import (
    AtomicCommitRequest,
    ChildSelfImprovementAtomicCommit,
    CommitDecision,
)


def make_request(**overrides):
    values = {
        "authorization_valid": True,
        "execution_completed": True,
        "post_verification_passed": True,
        "integrity_verified": True,
        "soul_unchanged": True,
        "constitution_unchanged": True,
        "authority_boundary_intact": True,
        "audit_complete": True,
        "provenance_complete": True,
        "version_verified": True,
    }

    values.update(overrides)
    return AtomicCommitRequest(**values)


def test_all_gates_ready():
    commit = ChildSelfImprovementAtomicCommit()

    result = commit.evaluate(make_request())

    assert result.decision == CommitDecision.READY
    assert result.rollback_required is False
    assert result.commit_performed is False


def test_authorization_failure_blocks():
    commit = ChildSelfImprovementAtomicCommit()

    result = commit.evaluate(
        make_request(authorization_valid=False)
    )

    assert result.decision == CommitDecision.BLOCK
    assert result.rollback_required is True


def test_execution_failure_blocks():
    commit = ChildSelfImprovementAtomicCommit()

    result = commit.evaluate(
        make_request(execution_completed=False)
    )

    assert result.decision == CommitDecision.BLOCK


def test_post_verification_failure_blocks():
    commit = ChildSelfImprovementAtomicCommit()

    result = commit.evaluate(
        make_request(post_verification_passed=False)
    )

    assert result.decision == CommitDecision.BLOCK


def test_integrity_failure_blocks():
    commit = ChildSelfImprovementAtomicCommit()

    result = commit.evaluate(
        make_request(integrity_verified=False)
    )

    assert result.decision == CommitDecision.BLOCK


def test_soul_change_blocks():
    commit = ChildSelfImprovementAtomicCommit()

    result = commit.evaluate(
        make_request(soul_unchanged=False)
    )

    assert result.decision == CommitDecision.BLOCK


def test_constitution_change_blocks():
    commit = ChildSelfImprovementAtomicCommit()

    result = commit.evaluate(
        make_request(constitution_unchanged=False)
    )

    assert result.decision == CommitDecision.BLOCK


def test_authority_boundary_failure_blocks():
    commit = ChildSelfImprovementAtomicCommit()

    result = commit.evaluate(
        make_request(authority_boundary_intact=False)
    )

    assert result.decision == CommitDecision.BLOCK


def test_audit_failure_blocks():
    commit = ChildSelfImprovementAtomicCommit()

    result = commit.evaluate(
        make_request(audit_complete=False)
    )

    assert result.decision == CommitDecision.BLOCK


def test_provenance_failure_blocks():
    commit = ChildSelfImprovementAtomicCommit()

    result = commit.evaluate(
        make_request(provenance_complete=False)
    )

    assert result.decision == CommitDecision.BLOCK


def test_version_failure_blocks():
    commit = ChildSelfImprovementAtomicCommit()

    result = commit.evaluate(
        make_request(version_verified=False)
    )

    assert result.decision == CommitDecision.BLOCK


def test_partial_commit_forbidden():
    commit = ChildSelfImprovementAtomicCommit()

    assert commit.commit_is_atomic() is True
    assert commit.partial_commit_allowed() is False


def test_commit_is_not_performed_here():
    commit = ChildSelfImprovementAtomicCommit()

    assert commit.commit_performed() is False
    assert commit.executes_upgrade() is False


def test_no_authority_grant():
    commit = ChildSelfImprovementAtomicCommit()

    assert commit.grants_authority() is False


def test_soul_and_constitution_protected():
    commit = ChildSelfImprovementAtomicCommit()

    assert commit.modifies_soul() is False
    assert commit.modifies_constitution() is False


def test_no_child_creation_or_activation():
    commit = ChildSelfImprovementAtomicCommit()

    assert commit.creates_real_child() is False
    assert commit.activates_real_child() is False


if __name__ == "__main__":
    test_all_gates_ready()
    test_authorization_failure_blocks()
    test_execution_failure_blocks()
    test_post_verification_failure_blocks()
    test_integrity_failure_blocks()
    test_soul_change_blocks()
    test_constitution_change_blocks()
    test_authority_boundary_failure_blocks()
    test_audit_failure_blocks()
    test_provenance_failure_blocks()
    test_version_failure_blocks()
    test_partial_commit_forbidden()
    test_commit_is_not_performed_here()
    test_no_authority_grant()
    test_soul_and_constitution_protected()
    test_no_child_creation_or_activation()

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT ATOMIC COMMIT TEST: PASS"
    )
