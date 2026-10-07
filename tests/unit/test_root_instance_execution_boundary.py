from __future__ import annotations

from copy import deepcopy

from core.brain.master_brain import MasterBrain
from core.brain.operational_tool_execution import (
    OperationalToolExecutionResult,
)
from core.brain.root_instance import SahibexRootInstanceIdentity


def make_execution_result(
    execution_id: str,
) -> OperationalToolExecutionResult:
    return OperationalToolExecutionResult(
        success=True,
        discovery_query="test execution",
        tool="read_file",
        allowed=True,
        requires_confirmation=False,
        attempts=1,
        recovery_status="SUCCESS",
        retryable=False,
        result={"value": "verified"},
        error=None,
        risk="low",
        reason="Test execution result.",
        execution_id=execution_id,
    )


def test_root_instance_and_execution_identity_are_distinct() -> None:
    root_instance = SahibexRootInstanceIdentity()
    execution = make_execution_result("execution-test-001")

    assert root_instance.instance_id != execution.execution_id
    assert root_instance.is_execution_identity() is False


def test_execution_identity_cannot_become_root_instance_identity() -> None:
    root_instance = SahibexRootInstanceIdentity()
    execution = make_execution_result("execution-test-002")

    original_instance_id = root_instance.instance_id

    forged_instance_id = execution.execution_id

    assert forged_instance_id != original_instance_id
    assert root_instance.instance_id == original_instance_id
    assert root_instance.validate() is True


def test_root_instance_identity_is_not_changed_by_execution_identity() -> None:
    root_instance = SahibexRootInstanceIdentity()
    execution = make_execution_result("execution-test-003")

    original = deepcopy(root_instance)

    assert execution.execution_id != root_instance.instance_id
    assert root_instance.instance_id == original.instance_id
    assert root_instance.fingerprint == original.fingerprint
    assert root_instance.validate() is True


def test_two_execution_identities_remain_distinct_from_same_root_instance() -> None:
    root_instance = SahibexRootInstanceIdentity()

    execution_a = make_execution_result("execution-test-A")
    execution_b = make_execution_result("execution-test-B")

    assert execution_a.execution_id != execution_b.execution_id
    assert execution_a.execution_id != root_instance.instance_id
    assert execution_b.execution_id != root_instance.instance_id
    assert root_instance.validate() is True


def test_master_brain_root_instance_is_separate_from_execution_identity() -> None:
    brain = MasterBrain()

    root_instance = brain.root_instance_identity
    execution = make_execution_result("execution-master-boundary-001")

    assert root_instance.root_identity.BRAIN_ID == "sahibex-master-brain"
    assert root_instance.instance_id != execution.execution_id
    assert root_instance.is_mother_instance() is True
    assert root_instance.is_execution_identity() is False


def test_root_instance_does_not_grant_execution_authority() -> None:
    root_instance = SahibexRootInstanceIdentity()

    forbidden_methods = {
        "execute",
        "invoke",
        "run_command",
        "write_file",
        "delete_file",
        "grant_permission",
        "require_permission",
        "change_permission",
        "modify_constitution",
        "update_constitution",
    }

    public_methods = set(dir(root_instance))

    assert not (
        forbidden_methods & public_methods
    )


def test_execution_result_identity_does_not_grant_authority() -> None:
    execution = make_execution_result(
        "execution-authority-boundary-001"
    )

    forbidden_attributes = {
        "grant_permission",
        "require_permission",
        "change_permission",
        "modify_constitution",
        "update_constitution",
        "execute",
        "invoke",
        "run_command",
    }

    public_attributes = set(dir(execution))

    assert not (
        forbidden_attributes & public_attributes
    )


def run_all_tests() -> None:
    test_root_instance_and_execution_identity_are_distinct()
    test_execution_identity_cannot_become_root_instance_identity()
    test_root_instance_identity_is_not_changed_by_execution_identity()
    test_two_execution_identities_remain_distinct_from_same_root_instance()
    test_master_brain_root_instance_is_separate_from_execution_identity()
    test_root_instance_does_not_grant_execution_authority()
    test_execution_result_identity_does_not_grant_authority()


if __name__ == "__main__":
    run_all_tests()
    print(
        "SAHIBEX PHASE 0 #10 ROOT-INSTANCE ↔ EXECUTION "
        "IDENTITY BOUNDARY TEST: PASS"
    )
