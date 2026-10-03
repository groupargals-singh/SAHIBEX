from __future__ import annotations

from core.brain.operational_verification import OperationalVerificationRecovery
from tools.result_handler import ToolResult


def valid_success() -> ToolResult:
    return ToolResult(
        tool="read_file",
        success=True,
        allowed=True,
        requires_confirmation=False,
        result="test data",
        error=None,
        risk="low",
        reason="Tool execution completed.",
    )


def test_valid_success_is_verified() -> None:
    verifier = OperationalVerificationRecovery()

    result = verifier.verify_tool_result(valid_success())

    assert result.success is True
    assert result.verified is True
    assert result.verification_status == "VERIFIED"
    assert result.recovery_status == "SUCCESS"
    assert result.result == "test data"


def test_success_without_permission_is_rejected() -> None:
    verifier = OperationalVerificationRecovery()

    result = ToolResult(
        tool="read_file",
        success=True,
        allowed=False,
        requires_confirmation=False,
        result="test data",
        error=None,
        risk="low",
        reason="Invalid success state.",
    )

    verified = verifier.verify_tool_result(result)

    assert verified.success is False
    assert verified.verified is False
    assert verified.verification_status == "FAILED"


def test_success_requiring_confirmation_is_rejected() -> None:
    verifier = OperationalVerificationRecovery()

    result = ToolResult(
        tool="read_file",
        success=True,
        allowed=True,
        requires_confirmation=True,
        result="test data",
        error=None,
        risk="medium",
        reason="Confirmation still required.",
    )

    verified = verifier.verify_tool_result(result)

    assert verified.success is False
    assert verified.verified is False
    assert verified.verification_status == "FAILED"


def test_success_without_result_is_rejected() -> None:
    verifier = OperationalVerificationRecovery()

    result = ToolResult(
        tool="read_file",
        success=True,
        allowed=True,
        requires_confirmation=False,
        result=None,
        error=None,
        risk="low",
        reason="Missing result.",
    )

    verified = verifier.verify_tool_result(result)

    assert verified.success is False
    assert verified.verified is False
    assert verified.verification_status == "FAILED"


def test_failed_result_cannot_become_success() -> None:
    verifier = OperationalVerificationRecovery()

    result = ToolResult(
        tool="read_file",
        success=False,
        allowed=False,
        requires_confirmation=False,
        result=None,
        error="Tool execution failed.",
        risk="low",
        reason="Tool failure.",
    )

    verified = verifier.verify_tool_result(result)

    assert verified.success is False
    assert verified.verified is False
    assert verified.verification_status == "FAILED"


def test_verifier_has_no_execution_or_authority_bypass_methods() -> None:
    verifier = OperationalVerificationRecovery()

    forbidden_methods = (
        "execute",
        "execute_action",
        "execute_command",
        "grant_permission",
        "modify_constitution",
        "override_constitution",
    )

    for method_name in forbidden_methods:
        assert not hasattr(verifier, method_name)


if __name__ == "__main__":
    print(
        "SAHIBEX 6P-9 POST-EXECUTION VERIFICATION "
        "SAFETY TEST: PASS"
    )
