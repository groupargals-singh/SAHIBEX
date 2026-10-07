from core.brain.child_self_improvement_end_to_end import (
    ChildSelfImprovementEndToEnd,
    EndToEndGateState,
)


def make_state(**overrides):
    controller = ChildSelfImprovementEndToEnd()

    values = {
        gate: True
        for gate in controller.GATES
    }

    values.update(overrides)

    return EndToEndGateState(**values)


def test_complete_pipeline_ready():
    controller = ChildSelfImprovementEndToEnd()

    result = controller.evaluate(make_state())

    assert result.ready is True
    assert result.failed_gates == ()
    assert result.execution_performed is False
    assert result.commit_performed is False
    assert result.recovery_required is False


def test_every_gate_is_required():
    controller = ChildSelfImprovementEndToEnd()

    assert controller.gate_count() == 20
    assert controller.all_gates_required() is True


def test_proposal_failure_blocks():
    controller = ChildSelfImprovementEndToEnd()

    result = controller.evaluate(
        make_state(proposal_valid=False)
    )

    assert result.ready is False
    assert "proposal_valid" in result.failed_gates
    assert result.recovery_required is True


def test_security_failure_blocks():
    controller = ChildSelfImprovementEndToEnd()

    result = controller.evaluate(
        make_state(security_passed=False)
    )

    assert result.ready is False
    assert "security_passed" in result.failed_gates
    assert result.recovery_required is True


def test_mother_approval_failure_blocks():
    controller = ChildSelfImprovementEndToEnd()

    result = controller.evaluate(
        make_state(mother_approved=False)
    )

    assert result.ready is False
    assert "mother_approved" in result.failed_gates


def test_human_approval_failure_blocks():
    controller = ChildSelfImprovementEndToEnd()

    result = controller.evaluate(
        make_state(human_approved=False)
    )

    assert result.ready is False
    assert "human_approved" in result.failed_gates


def test_authorization_failure_blocks():
    controller = ChildSelfImprovementEndToEnd()

    result = controller.evaluate(
        make_state(authorization_valid=False)
    )

    assert result.ready is False
    assert "authorization_valid" in result.failed_gates


def test_post_verification_failure_blocks():
    controller = ChildSelfImprovementEndToEnd()

    result = controller.evaluate(
        make_state(post_verification_passed=False)
    )

    assert result.ready is False
    assert "post_verification_passed" in result.failed_gates


def test_atomic_commit_failure_blocks():
    controller = ChildSelfImprovementEndToEnd()

    result = controller.evaluate(
        make_state(atomic_commit_ready=False)
    )

    assert result.ready is False
    assert "atomic_commit_ready" in result.failed_gates


def test_audit_failure_blocks():
    controller = ChildSelfImprovementEndToEnd()

    result = controller.evaluate(
        make_state(audit_complete=False)
    )

    assert result.ready is False
    assert "audit_complete" in result.failed_gates


def test_provenance_failure_blocks():
    controller = ChildSelfImprovementEndToEnd()

    result = controller.evaluate(
        make_state(provenance_complete=False)
    )

    assert result.ready is False
    assert "provenance_complete" in result.failed_gates


def test_recovery_failure_blocks():
    controller = ChildSelfImprovementEndToEnd()

    result = controller.evaluate(
        make_state(recovery_ready=False)
    )

    assert result.ready is False
    assert "recovery_ready" in result.failed_gates


def test_soul_change_blocks():
    controller = ChildSelfImprovementEndToEnd()

    result = controller.evaluate(
        make_state(soul_unchanged=False)
    )

    assert result.ready is False
    assert "soul_unchanged" in result.failed_gates


def test_constitution_change_blocks():
    controller = ChildSelfImprovementEndToEnd()

    result = controller.evaluate(
        make_state(constitution_unchanged=False)
    )

    assert result.ready is False
    assert "constitution_unchanged" in result.failed_gates


def test_authority_boundary_failure_blocks():
    controller = ChildSelfImprovementEndToEnd()

    result = controller.evaluate(
        make_state(authority_boundary_intact=False)
    )

    assert result.ready is False
    assert "authority_boundary_intact" in result.failed_gates


def test_no_live_execution():
    controller = ChildSelfImprovementEndToEnd()

    assert controller.executes_upgrade() is False
    assert controller.performs_commit() is False


def test_no_authority_grant():
    controller = ChildSelfImprovementEndToEnd()

    assert controller.grants_authority() is False


def test_soul_constitution_protected():
    controller = ChildSelfImprovementEndToEnd()

    assert controller.modifies_soul() is False
    assert controller.modifies_constitution() is False


def test_no_child_creation_or_activation():
    controller = ChildSelfImprovementEndToEnd()

    assert controller.creates_real_child() is False
    assert controller.activates_real_child() is False


if __name__ == "__main__":
    test_complete_pipeline_ready()
    test_every_gate_is_required()
    test_proposal_failure_blocks()
    test_security_failure_blocks()
    test_mother_approval_failure_blocks()
    test_human_approval_failure_blocks()
    test_authorization_failure_blocks()
    test_post_verification_failure_blocks()
    test_atomic_commit_failure_blocks()
    test_audit_failure_blocks()
    test_provenance_failure_blocks()
    test_recovery_failure_blocks()
    test_soul_change_blocks()
    test_constitution_change_blocks()
    test_authority_boundary_failure_blocks()
    test_no_live_execution()
    test_no_authority_grant()
    test_soul_constitution_protected()
    test_no_child_creation_or_activation()

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT END-TO-END TEST: PASS"
    )
