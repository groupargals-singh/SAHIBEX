from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RegressionDecision(str, Enum):
    PASS = "pass"
    BLOCK = "block"


class RegressionArea(str, Enum):
    CORE_FUNCTIONALITY = "core_functionality"
    MOTHER_CHILD_AUTHORITY = "mother_child_authority"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    VERIFICATION = "verification"
    SECURITY = "security"
    INTERNAL_ARMY = "internal_army"
    INTERNAL_LABOR = "internal_labor"
    AUDIT = "audit"


@dataclass(frozen=True)
class RegressionTestState:
    core_functionality_passed: bool
    mother_child_authority_passed: bool
    memory_passed: bool
    knowledge_passed: bool
    verification_passed: bool
    security_passed: bool
    internal_army_passed: bool
    internal_labor_passed: bool
    audit_passed: bool


@dataclass(frozen=True)
class RegressionGateResult:
    decision: RegressionDecision
    reason: str
    failed_tests: tuple[str, ...]
    requires_mother: bool
    requires_human: bool


class ChildSelfImprovementRegressionGate:
    """
    Regression validation gate for Child self-improvement.

    This layer verifies that a proposed improvement does not break
    existing Child capabilities, authority boundaries, memory,
    knowledge, verification, security, Army, Labor, or audit contracts.

    This layer NEVER:
    - executes upgrades
    - modifies live code
    - grants authority
    - modifies soul
    - modifies constitution
    - creates children
    - activates children
    """

    VERSION = "1.0"

    REQUIRED_TESTS = (
        "core_functionality_passed",
        "mother_child_authority_passed",
        "memory_passed",
        "knowledge_passed",
        "verification_passed",
        "security_passed",
        "internal_army_passed",
        "internal_labor_passed",
        "audit_passed",
    )

    def evaluate(
        self,
        tests: RegressionTestState,
    ) -> RegressionGateResult:

        failed: list[str] = []

        for test_name in self.REQUIRED_TESTS:
            if not getattr(tests, test_name):
                failed.append(test_name)

        if failed:
            return RegressionGateResult(
                decision=RegressionDecision.BLOCK,
                reason="one or more regression tests failed",
                failed_tests=tuple(failed),
                requires_mother=True,
                requires_human=True,
            )

        return RegressionGateResult(
            decision=RegressionDecision.PASS,
            reason="all required regression tests passed",
            failed_tests=(),
            requires_mother=True,
            requires_human=False,
        )

    def all_regression_tests_passed(
        self,
        tests: RegressionTestState,
    ) -> bool:
        return all(
            getattr(tests, test_name)
            for test_name in self.REQUIRED_TESTS
        )

    def core_functionality_required(self) -> bool:
        return True

    def mother_child_authority_required(self) -> bool:
        return True

    def memory_contract_required(self) -> bool:
        return True

    def knowledge_contract_required(self) -> bool:
        return True

    def verification_contract_required(self) -> bool:
        return True

    def security_contract_required(self) -> bool:
        return True

    def internal_army_contract_required(self) -> bool:
        return True

    def internal_labor_contract_required(self) -> bool:
        return True

    def audit_contract_required(self) -> bool:
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
        audit_passed=True,
    )

    result = gate.evaluate(tests)

    assert result.decision == RegressionDecision.PASS
    assert result.failed_tests == ()
    assert result.requires_mother is True
    assert result.requires_human is False

    assert gate.all_regression_tests_passed(tests) is True

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

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT REGRESSION GATE TEST: PASS"
    )
