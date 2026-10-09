from __future__ import annotations

from core.brain.operational_verification import (
    OperationalVerificationRecovery,
)
from core.brain.operational_reasoning import (
    OperationalReasoningResult,
)
from tools.failure_recovery import RecoveryResult


def build_reasoning(
    *,
    success: bool = True,
    verification_status: str = "VERIFIED",
    requires_confirmation: bool = False,
    model_response: str = "Verified response.",
) -> OperationalReasoningResult:
    return OperationalReasoningResult(
        success=success,
        user_input="Explain this request.",
        intent="explain",
        action="respond",
        reasoning_response="Reasoning completed.",
        model_response=model_response,
        model_provider="mock",
        model="mock-v1",
        requires_confirmation=requires_confirmation,
        verification_status=verification_status,
    )


def main() -> None:
    integration = OperationalVerificationRecovery()

    # Successful reasoning must verify.
    verified = integration.verify_reasoning(
        build_reasoning()
    )

    assert verified.success is True
    assert verified.verified is True
    assert verified.verification_status == "VERIFIED"
    assert verified.recovery_status == "SUCCESS"
    assert verified.attempts == 1
    assert verified.retryable is False
    assert verified.result == "Verified response."

    # Generated model text may pass structural checks, but must not be
    # falsely reported as factually verified.
    generated = integration.verify_reasoning(
        build_reasoning(verification_status="GENERATED")
    )
    assert generated.success is True
    assert generated.verified is False
    assert generated.verification_status == "STRUCTURALLY_VALID"
    assert generated.result == "Verified response."

    # Failed reasoning must never become successful.
    failed_reasoning = integration.verify_reasoning(
        build_reasoning(success=False)
    )

    assert failed_reasoning.success is False
    assert failed_reasoning.verified is False
    assert failed_reasoning.recovery_status == "FAILED"

    # Unverified reasoning must be blocked.
    unverified = integration.verify_reasoning(
        build_reasoning(
            verification_status="UNKNOWN"
        )
    )

    assert unverified.success is False
    assert unverified.verified is False
    assert unverified.recovery_status == "BLOCKED"

    # Confirmation requirement must remain blocked.
    confirmation = integration.verify_reasoning(
        build_reasoning(
            requires_confirmation=True
        )
    )

    assert confirmation.success is False
    assert confirmation.verified is False
    assert confirmation.recovery_status == "BLOCKED"

    # Empty model output must not be treated as success.
    empty_response = integration.verify_reasoning(
        build_reasoning(model_response="")
    )

    assert empty_response.success is False
    assert empty_response.verified is False
    assert empty_response.recovery_status == "FAILED"

    # Recovery SUCCESS.
    success_recovery = RecoveryResult(
        tool="search_local_files",
        status="SUCCESS",
        attempts=1,
        retryable=False,
        success=True,
        result={"count": 1},
        error=None,
        reason="Tool execution succeeded.",
    )

    normalized_success = integration.normalize_recovery(
        success_recovery
    )

    assert normalized_success.success is True
    assert normalized_success.verified is True
    assert normalized_success.recovery_status == "SUCCESS"
    assert normalized_success.result == {"count": 1}

    # Recovery RETRY.
    retry_recovery = RecoveryResult(
        tool="search_local_files",
        status="RETRY",
        attempts=1,
        retryable=True,
        success=False,
        result=None,
        error="TimeoutError: temporary failure",
        reason="Retry allowed.",
    )

    normalized_retry = integration.normalize_recovery(
        retry_recovery
    )

    assert normalized_retry.success is False
    assert normalized_retry.verified is False
    assert normalized_retry.recovery_status == "RETRY"
    assert normalized_retry.retryable is True

    # Recovery BLOCKED.
    blocked_recovery = RecoveryResult(
        tool="write_file",
        status="BLOCKED",
        attempts=1,
        retryable=False,
        success=False,
        result=None,
        error="Permission denied.",
        reason="Protected action blocked.",
    )

    normalized_blocked = integration.normalize_recovery(
        blocked_recovery
    )

    assert normalized_blocked.success is False
    assert normalized_blocked.verified is False
    assert normalized_blocked.verification_status == "BLOCKED"
    assert normalized_blocked.recovery_status == "BLOCKED"

    # Recovery FAILED.
    failed_recovery = RecoveryResult(
        tool="search_local_files",
        status="FAILED",
        attempts=3,
        retryable=False,
        success=False,
        result=None,
        error="Permanent failure.",
        reason="Retry limit reached.",
    )

    normalized_failed = integration.normalize_recovery(
        failed_recovery
    )

    assert normalized_failed.success is False
    assert normalized_failed.verified is False
    assert normalized_failed.recovery_status == "FAILED"
    assert normalized_failed.attempts == 3

    # No execution or permission-granting APIs.
    forbidden_methods = {
        "execute",
        "execute_action",
        "execute_command",
        "grant_permission",
        "modify_constitution",
        "override_constitution",
    }

    for method_name in forbidden_methods:
        assert not hasattr(integration, method_name)

    print(
        "SAHIBEX 6O-9 OPERATIONAL "
        "VERIFICATION & RECOVERY TEST: PASS"
    )


if __name__ == "__main__":
    main()
