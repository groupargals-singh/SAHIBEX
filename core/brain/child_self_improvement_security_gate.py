from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SecurityDecision(str, Enum):
    PASS = "pass"
    BLOCK = "block"


class SecurityTest(str, Enum):
    PROMPT_INJECTION = "prompt_injection"
    CREDENTIAL_PROTECTION = "credential_protection"
    SANDBOX_ESCAPE = "sandbox_escape"
    AUTHORITY_ESCALATION = "authority_escalation"
    NETWORK_ABUSE = "network_abuse"
    SECURITY_BOUNDARY = "security_boundary"
    FAIL_CLOSED = "fail_closed"


@dataclass(frozen=True)
class SecurityTestState:
    prompt_injection_passed: bool
    credential_protection_passed: bool
    sandbox_escape_passed: bool
    authority_escalation_passed: bool
    network_abuse_passed: bool
    security_boundary_passed: bool
    fail_closed_passed: bool


@dataclass(frozen=True)
class SecurityGateResult:
    decision: SecurityDecision
    reason: str
    failed_tests: tuple[str, ...]
    requires_mother: bool
    requires_human: bool


class ChildSelfImprovementSecurityGate:
    """
    Security validation gate for Child self-improvement.

    This layer:
    - validates security test results
    - blocks unsafe upgrades
    - fails closed when required security tests fail

    This layer NEVER:
    - executes upgrades
    - changes code
    - grants authority
    - modifies soul
    - modifies constitution
    - creates or activates children
    """

    VERSION = "1.0"

    REQUIRED_TESTS = (
        "prompt_injection_passed",
        "credential_protection_passed",
        "sandbox_escape_passed",
        "authority_escalation_passed",
        "network_abuse_passed",
        "security_boundary_passed",
        "fail_closed_passed",
    )

    def evaluate(
        self,
        tests: SecurityTestState,
    ) -> SecurityGateResult:

        failed: list[str] = []

        for test_name in self.REQUIRED_TESTS:
            if not getattr(tests, test_name):
                failed.append(test_name)

        if failed:
            return SecurityGateResult(
                decision=SecurityDecision.BLOCK,
                reason="one or more required security tests failed",
                failed_tests=tuple(failed),
                requires_mother=True,
                requires_human=True,
            )

        return SecurityGateResult(
            decision=SecurityDecision.PASS,
            reason="all required security tests passed",
            failed_tests=(),
            requires_mother=True,
            requires_human=False,
        )

    def all_security_tests_passed(
        self,
        tests: SecurityTestState,
    ) -> bool:
        return all(
            getattr(tests, test_name)
            for test_name in self.REQUIRED_TESTS
        )

    def prompt_injection_protection_required(self) -> bool:
        return True

    def credential_protection_required(self) -> bool:
        return True

    def sandbox_escape_protection_required(self) -> bool:
        return True

    def authority_escalation_protection_required(self) -> bool:
        return True

    def network_abuse_protection_required(self) -> bool:
        return True

    def security_boundary_protection_required(self) -> bool:
        return True

    def fail_closed_required(self) -> bool:
        return True

    def execution_allowed(self) -> bool:
        return False

    def upgrade_execution_allowed(self) -> bool:
        return False

    def grants_authority(self) -> bool:
        return False

    def bypass_allowed(self) -> bool:
        return False

    def modifies_soul(self) -> bool:
        return False

    def modifies_constitution(self) -> bool:
        return False

    def creates_real_child(self) -> bool:
        return False

    def activates_real_child(self) -> bool:
        return False


if __name__ == "__main__":
    gate = ChildSelfImprovementSecurityGate()

    tests = SecurityTestState(
        prompt_injection_passed=True,
        credential_protection_passed=True,
        sandbox_escape_passed=True,
        authority_escalation_passed=True,
        network_abuse_passed=True,
        security_boundary_passed=True,
        fail_closed_passed=True,
    )

    result = gate.evaluate(tests)

    assert result.decision == SecurityDecision.PASS
    assert result.failed_tests == ()
    assert result.requires_mother is True
    assert result.requires_human is False

    assert gate.all_security_tests_passed(tests) is True
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

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT SECURITY GATE TEST: PASS"
    )
