from core.brain.child_self_improvement_execution import (
    ChildSelfImprovementExecution,
    ExecutionDecision,
    UpgradeExecutionRequest,
)


def make_request(**overrides):
    values = {
        "authorization_id": "upgrade-auth-001",
        "proposal_id": "proposal-001",
        "child_brain_id": "child-001",
        "target": "reasoning",
        "version_before": "1.0",
        "version_after": "1.1",
        "authorization_valid": True,
        "security_verified": True,
        "regression_verified": True,
        "verification_passed": True,
        "authority_boundary_intact": True,
        "soul_unchanged": True,
        "constitution_unchanged": True,
    }

    values.update(overrides)
    return UpgradeExecutionRequest(**values)


def test_valid_authorization_allows_execution_stage():
    execution = ChildSelfImprovementExecution()

    result = execution.evaluate(make_request())

    assert result.decision == ExecutionDecision.ALLOW
    assert result.post_verification_required is True
    assert result.actual_execution_performed is False


def test_invalid_authorization_blocks():
    execution = ChildSelfImprovementExecution()

    result = execution.evaluate(
        make_request(authorization_valid=False)
    )

    assert result.decision == ExecutionDecision.BLOCK


def test_security_failure_blocks():
    execution = ChildSelfImprovementExecution()

    result = execution.evaluate(
        make_request(security_verified=False)
    )

    assert result.decision == ExecutionDecision.BLOCK


def test_regression_failure_blocks():
    execution = ChildSelfImprovementExecution()

    result = execution.evaluate(
        make_request(regression_verified=False)
    )

    assert result.decision == ExecutionDecision.BLOCK


def test_verification_failure_blocks():
    execution = ChildSelfImprovementExecution()

    result = execution.evaluate(
        make_request(verification_passed=False)
    )

    assert result.decision == ExecutionDecision.BLOCK


def test_authority_boundary_failure_blocks():
    execution = ChildSelfImprovementExecution()

    result = execution.evaluate(
        make_request(authority_boundary_intact=False)
    )

    assert result.decision == ExecutionDecision.BLOCK


def test_soul_change_blocks():
    execution = ChildSelfImprovementExecution()

    result = execution.evaluate(
        make_request(soul_unchanged=False)
    )

    assert result.decision == ExecutionDecision.BLOCK


def test_constitution_change_blocks():
    execution = ChildSelfImprovementExecution()

    result = execution.evaluate(
        make_request(constitution_unchanged=False)
    )

    assert result.decision == ExecutionDecision.BLOCK


def test_same_version_blocks():
    execution = ChildSelfImprovementExecution()

    result = execution.evaluate(
        make_request(
            version_before="1.0",
            version_after="1.0",
        )
    )

    assert result.decision == ExecutionDecision.BLOCK


def test_no_arbitrary_command_execution():
    execution = ChildSelfImprovementExecution()

    assert execution.can_execute_arbitrary_command() is False
    assert execution.performs_live_upgrade() is False


def test_no_authority_grant():
    execution = ChildSelfImprovementExecution()

    assert execution.can_grant_authority() is False


def test_soul_and_constitution_protected():
    execution = ChildSelfImprovementExecution()

    assert execution.can_modify_soul() is False
    assert execution.can_modify_constitution() is False


def test_no_child_creation_or_activation():
    execution = ChildSelfImprovementExecution()

    assert execution.creates_real_child() is False
    assert execution.activates_real_child() is False


def test_post_verification_required():
    execution = ChildSelfImprovementExecution()

    assert execution.requires_post_verification() is True


if __name__ == "__main__":
    test_valid_authorization_allows_execution_stage()
    test_invalid_authorization_blocks()
    test_security_failure_blocks()
    test_regression_failure_blocks()
    test_verification_failure_blocks()
    test_authority_boundary_failure_blocks()
    test_soul_change_blocks()
    test_constitution_change_blocks()
    test_same_version_blocks()
    test_no_arbitrary_command_execution()
    test_no_authority_grant()
    test_soul_and_constitution_protected()
    test_no_child_creation_or_activation()
    test_post_verification_required()

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT EXECUTION BOUNDARY TEST: PASS"
    )
