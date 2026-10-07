from core.brain.child_self_improvement_regression_gate import (
    ChildSelfImprovementRegressionGate,
    RegressionDecision,
    RegressionTestState,
)


def all_tests_passed() -> RegressionTestState:
    return RegressionTestState(
        core_functionality_passed=True,
        mother_child_authority_passed=True,
        memory_passed=True,
        knowledge_passed=True,
        verification_passed=True,
        security_passed=True,
        internal_army_passed=True,
        internal_labor_passed=True,
        audit_passed=True,
    )


def test_all_regression_tests_pass():
    gate = ChildSelfImprovementRegressionGate()

    result = gate.evaluate(all_tests_passed())

    assert result.decision == RegressionDecision.PASS
    assert result.failed_tests == ()
    assert result.requires_mother is True
    assert result.requires_human is False


def test_core_functionality_failure_blocks():
    gate = ChildSelfImprovementRegressionGate()

    tests = RegressionTestState(
        core_functionality_passed=False,
        mother_child_authority_passed=True,
        memory_passed=True,
        knowledge_passed=True,
        verification_passed=True,
        security_passed=True,
        internal_army_passed=True,
        internal_labor_passed=True,
        audit_passed=True,
    )

    result = gate.evaluate(tests)

    assert result.decision == RegressionDecision.BLOCK
    assert "core_functionality_passed" in result.failed_tests


def test_authority_regression_blocks():
    gate = ChildSelfImprovementRegressionGate()

    tests = RegressionTestState(
        core_functionality_passed=True,
        mother_child_authority_passed=False,
        memory_passed=True,
        knowledge_passed=True,
        verification_passed=True,
        security_passed=True,
        internal_army_passed=True,
        internal_labor_passed=True,
        audit_passed=True,
    )

    result = gate.evaluate(tests)

    assert result.decision == RegressionDecision.BLOCK
    assert "mother_child_authority_passed" in result.failed_tests


def test_memory_regression_blocks():
    gate = ChildSelfImprovementRegressionGate()

    tests = RegressionTestState(
        core_functionality_passed=True,
        mother_child_authority_passed=True,
        memory_passed=False,
        knowledge_passed=True,
        verification_passed=True,
        security_passed=True,
        internal_army_passed=True,
        internal_labor_passed=True,
        audit_passed=True,
    )

    result = gate.evaluate(tests)

    assert result.decision == RegressionDecision.BLOCK
    assert "memory_passed" in result.failed_tests


def test_knowledge_regression_blocks():
    gate = ChildSelfImprovementRegressionGate()

    tests = RegressionTestState(
        core_functionality_passed=True,
        mother_child_authority_passed=True,
        memory_passed=True,
        knowledge_passed=False,
        verification_passed=True,
        security_passed=True,
        internal_army_passed=True,
        internal_labor_passed=True,
        audit_passed=True,
    )

    result = gate.evaluate(tests)

    assert result.decision == RegressionDecision.BLOCK
    assert "knowledge_passed" in result.failed_tests


def test_verification_regression_blocks():
    gate = ChildSelfImprovementRegressionGate()

    tests = RegressionTestState(
        core_functionality_passed=True,
        mother_child_authority_passed=True,
        memory_passed=True,
        knowledge_passed=True,
        verification_passed=False,
        security_passed=True,
        internal_army_passed=True,
        internal_labor_passed=True,
        audit_passed=True,
    )

    result = gate.evaluate(tests)

    assert result.decision == RegressionDecision.BLOCK
    assert "verification_passed" in result.failed_tests


def test_security_regression_blocks():
    gate = ChildSelfImprovementRegressionGate()

    tests = RegressionTestState(
        core_functionality_passed=True,
        mother_child_authority_passed=True,
        memory_passed=True,
        knowledge_passed=True,
        verification_passed=True,
        security_passed=False,
        internal_army_passed=True,
        internal_labor_passed=True,
        audit_passed=True,
    )

    result = gate.evaluate(tests)

    assert result.decision == RegressionDecision.BLOCK
    assert "security_passed" in result.failed_tests


def test_army_regression_blocks():
    gate = ChildSelfImprovementRegressionGate()

    tests = RegressionTestState(
        core_functionality_passed=True,
        mother_child_authority_passed=True,
        memory_passed=True,
        knowledge_passed=True,
        verification_passed=True,
        security_passed=True,
        internal_army_passed=False,
        internal_labor_passed=True,
        audit_passed=True,
    )

    result = gate.evaluate(tests)

    assert result.decision == RegressionDecision.BLOCK
    assert "internal_army_passed" in result.failed_tests


def test_labor_regression_blocks():
    gate = ChildSelfImprovementRegressionGate()

    tests = RegressionTestState(
        core_functionality_passed=True,
        mother_child_authority_passed=True,
        memory_passed=True,
        knowledge_passed=True,
        verification_passed=True,
        security_passed=True,
        internal_army_passed=True,
        internal_labor_passed=False,
        audit_passed=True,
    )

    result = gate.evaluate(tests)

    assert result.decision == RegressionDecision.BLOCK
    assert "internal_labor_passed" in result.failed_tests


def test_audit_regression_blocks():
    gate = ChildSelfImprovementRegressionGate()

    tests = RegressionTestState(
        core_functionality_passed=True,
        mother_child_authority_passed=True,
        memory_passed=True,
        knowledge_passed=True,
        verification_passed=True,
        security_passed=True,
        internal_army_passed=True,
        internal_labor_passed=True,
        audit_passed=False,
    )

    result = gate.evaluate(tests)

    assert result.decision == RegressionDecision.BLOCK
    assert "audit_passed" in result.failed_tests


def test_multiple_regressions_reported():
    gate = ChildSelfImprovementRegressionGate()

    tests = RegressionTestState(
        core_functionality_passed=False,
        mother_child_authority_passed=False,
        memory_passed=True,
        knowledge_passed=True,
        verification_passed=False,
        security_passed=True,
        internal_army_passed=True,
        internal_labor_passed=True,
        audit_passed=False,
    )

    result = gate.evaluate(tests)

    assert result.decision == RegressionDecision.BLOCK
    assert "core_functionality_passed" in result.failed_tests
    assert "mother_child_authority_passed" in result.failed_tests
    assert "verification_passed" in result.failed_tests
    assert "audit_passed" in result.failed_tests


def test_regression_invariants():
    gate = ChildSelfImprovementRegressionGate()

    assert gate.core_functionality_required() is True
    assert gate.mother_child_authority_required() is True
    assert gate.memory_contract_required() is True
    assert gate.knowledge_contract_required() is True
    assert gate.verification_contract_required() is True
    assert gate.security_contract_required() is True
    assert gate.internal_army_contract_required() is True
    assert gate.internal_labor_contract_required() is True
    assert gate.audit_contract_required() is True

    assert gate.execution_allowed() is False
    assert gate.upgrade_execution_allowed() is False
    assert gate.grants_authority() is False
    assert gate.bypass_allowed() is False
    assert gate.modifies_soul() is False
    assert gate.modifies_constitution() is False
    assert gate.creates_real_child() is False
    assert gate.activates_real_child() is False


if __name__ == "__main__":
    test_all_regression_tests_pass()
    test_core_functionality_failure_blocks()
    test_authority_regression_blocks()
    test_memory_regression_blocks()
    test_knowledge_regression_blocks()
    test_verification_regression_blocks()
    test_security_regression_blocks()
    test_army_regression_blocks()
    test_labor_regression_blocks()
    test_audit_regression_blocks()
    test_multiple_regressions_reported()
    test_regression_invariants()

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT REGRESSION GATE TEST: PASS"
    )
