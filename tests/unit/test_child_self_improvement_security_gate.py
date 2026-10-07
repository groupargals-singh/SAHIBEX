from core.brain.child_self_improvement_security_gate import (
    ChildSelfImprovementSecurityGate,
    SecurityDecision,
    SecurityTestState,
)


def all_security_tests_passed() -> SecurityTestState:
    return SecurityTestState(
        prompt_injection_passed=True,
        credential_protection_passed=True,
        sandbox_escape_passed=True,
        authority_escalation_passed=True,
        network_abuse_passed=True,
        security_boundary_passed=True,
        fail_closed_passed=True,
    )


def test_all_security_tests_pass():
    gate = ChildSelfImprovementSecurityGate()

    result = gate.evaluate(all_security_tests_passed())

    assert result.decision == SecurityDecision.PASS
    assert result.failed_tests == ()
    assert result.requires_mother is True
    assert result.requires_human is False


def test_prompt_injection_failure_blocks():
    gate = ChildSelfImprovementSecurityGate()

    tests = SecurityTestState(
        prompt_injection_passed=False,
        credential_protection_passed=True,
        sandbox_escape_passed=True,
        authority_escalation_passed=True,
        network_abuse_passed=True,
        security_boundary_passed=True,
        fail_closed_passed=True,
    )

    result = gate.evaluate(tests)

    assert result.decision == SecurityDecision.BLOCK
    assert "prompt_injection_passed" in result.failed_tests


def test_credential_failure_blocks():
    gate = ChildSelfImprovementSecurityGate()

    tests = SecurityTestState(
        prompt_injection_passed=True,
        credential_protection_passed=False,
        sandbox_escape_passed=True,
        authority_escalation_passed=True,
        network_abuse_passed=True,
        security_boundary_passed=True,
        fail_closed_passed=True,
    )

    result = gate.evaluate(tests)

    assert result.decision == SecurityDecision.BLOCK
    assert "credential_protection_passed" in result.failed_tests


def test_sandbox_escape_failure_blocks():
    gate = ChildSelfImprovementSecurityGate()

    tests = SecurityTestState(
        prompt_injection_passed=True,
        credential_protection_passed=True,
        sandbox_escape_passed=False,
        authority_escalation_passed=True,
        network_abuse_passed=True,
        security_boundary_passed=True,
        fail_closed_passed=True,
    )

    result = gate.evaluate(tests)

    assert result.decision == SecurityDecision.BLOCK
    assert "sandbox_escape_passed" in result.failed_tests


def test_authority_escalation_failure_blocks():
    gate = ChildSelfImprovementSecurityGate()

    tests = SecurityTestState(
        prompt_injection_passed=True,
        credential_protection_passed=True,
        sandbox_escape_passed=True,
        authority_escalation_passed=False,
        network_abuse_passed=True,
        security_boundary_passed=True,
        fail_closed_passed=True,
    )

    result = gate.evaluate(tests)

    assert result.decision == SecurityDecision.BLOCK
    assert "authority_escalation_passed" in result.failed_tests


def test_network_abuse_failure_blocks():
    gate = ChildSelfImprovementSecurityGate()

    tests = SecurityTestState(
        prompt_injection_passed=True,
        credential_protection_passed=True,
        sandbox_escape_passed=True,
        authority_escalation_passed=True,
        network_abuse_passed=False,
        security_boundary_passed=True,
        fail_closed_passed=True,
    )

    result = gate.evaluate(tests)

    assert result.decision == SecurityDecision.BLOCK
    assert "network_abuse_passed" in result.failed_tests


def test_security_boundary_failure_blocks():
    gate = ChildSelfImprovementSecurityGate()

    tests = SecurityTestState(
        prompt_injection_passed=True,
        credential_protection_passed=True,
        sandbox_escape_passed=True,
        authority_escalation_passed=True,
        network_abuse_passed=True,
        security_boundary_passed=False,
        fail_closed_passed=True,
    )

    result = gate.evaluate(tests)

    assert result.decision == SecurityDecision.BLOCK
    assert "security_boundary_passed" in result.failed_tests


def test_fail_closed_failure_blocks():
    gate = ChildSelfImprovementSecurityGate()

    tests = SecurityTestState(
        prompt_injection_passed=True,
        credential_protection_passed=True,
        sandbox_escape_passed=True,
        authority_escalation_passed=True,
        network_abuse_passed=True,
        security_boundary_passed=True,
        fail_closed_passed=False,
    )

    result = gate.evaluate(tests)

    assert result.decision == SecurityDecision.BLOCK
    assert "fail_closed_passed" in result.failed_tests


def test_multiple_security_failures_reported():
    gate = ChildSelfImprovementSecurityGate()

    tests = SecurityTestState(
        prompt_injection_passed=False,
        credential_protection_passed=False,
        sandbox_escape_passed=True,
        authority_escalation_passed=False,
        network_abuse_passed=True,
        security_boundary_passed=True,
        fail_closed_passed=False,
    )

    result = gate.evaluate(tests)

    assert result.decision == SecurityDecision.BLOCK
    assert "prompt_injection_passed" in result.failed_tests
    assert "credential_protection_passed" in result.failed_tests
    assert "authority_escalation_passed" in result.failed_tests
    assert "fail_closed_passed" in result.failed_tests


def test_security_invariants():
    gate = ChildSelfImprovementSecurityGate()

    assert gate.prompt_injection_protection_required() is True
    assert gate.credential_protection_required() is True
    assert gate.sandbox_escape_protection_required() is True
    assert gate.authority_escalation_protection_required() is True
    assert gate.network_abuse_protection_required() is True
    assert gate.security_boundary_protection_required() is True
    assert gate.fail_closed_required() is True

    assert gate.execution_allowed() is False
    assert gate.upgrade_execution_allowed() is False
    assert gate.grants_authority() is False
    assert gate.bypass_allowed() is False
    assert gate.modifies_soul() is False
    assert gate.modifies_constitution() is False
    assert gate.creates_real_child() is False
    assert gate.activates_real_child() is False


if __name__ == "__main__":
    test_all_security_tests_pass()
    test_prompt_injection_failure_blocks()
    test_credential_failure_blocks()
    test_sandbox_escape_failure_blocks()
    test_authority_escalation_failure_blocks()
    test_network_abuse_failure_blocks()
    test_security_boundary_failure_blocks()
    test_fail_closed_failure_blocks()
    test_multiple_security_failures_reported()
    test_security_invariants()

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT SECURITY GATE TEST: PASS"
    )
