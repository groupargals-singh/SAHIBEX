from __future__ import annotations

from dataclasses import dataclass

from core.brain.operational_verification import OperationalVerificationResult
from tools.intelligence import ToolIntelligence
from tools.result_handler import ToolResult


@dataclass
class FakeInvocation:
    tool: str = "read_file"
    success: bool = True
    allowed: bool = True
    requires_confirmation: bool = False
    result: str | None = "test data"
    error: str | None = None
    risk: str = "low"
    reason: str = "Tool execution completed."


class FakeInvoker:
    def invoke(
        self,
        discovery_query: str,
        *,
        user_confirmation: bool = False,
        **kwargs,
    ) -> FakeInvocation:
        return FakeInvocation()


class FakeResultHandler:
    def handle(self, invocation: FakeInvocation) -> ToolResult:
        return ToolResult(
            tool=invocation.tool,
            success=True,
            allowed=True,
            requires_confirmation=False,
            result="test data",
            error=None,
            risk="low",
            reason="Tool execution completed.",
        )


class FakeRecovery:
    def recover(self, invocation, *, attempts: int):
        return type(
            "Recovery",
            (),
            {
                "status": "SUCCESS",
                "retryable": False,
                "reason": "Execution completed.",
            },
        )()


class RejectingVerification:
    def verify_tool_result(
        self,
        result: ToolResult,
    ) -> OperationalVerificationResult:
        return OperationalVerificationResult(
            success=False,
            verified=False,
            verification_status="FAILED",
            recovery_status="FAILED",
            attempts=1,
            retryable=False,
            reason="Post-execution verification rejected the result.",
            result=None,
        )


def test_verification_failure_cannot_be_reported_as_success() -> None:
    intelligence = ToolIntelligence(
        tool_invoker=FakeInvoker(),
        result_handler=FakeResultHandler(),
        recovery=FakeRecovery(),
        operational_verification=RejectingVerification(),
    )

    result = intelligence.execute("read file")

    assert result.success is False
    assert result.recovery_status == "FAILED"
    assert result.retryable is False
    assert result.result is None
    assert result.error == (
        "Post-execution verification rejected the result."
    )


def test_verified_success_is_returned_as_success() -> None:
    intelligence = ToolIntelligence(
        tool_invoker=FakeInvoker(),
        result_handler=FakeResultHandler(),
        recovery=FakeRecovery(),
    )

    result = intelligence.execute("read file")

    assert result.success is True
    assert result.recovery_status == "SUCCESS"
    assert result.retryable is False
    assert result.result == "test data"
    assert result.error is None


def test_confirmation_propagation_contract_remains_present() -> None:
    intelligence = ToolIntelligence(
        tool_invoker=FakeInvoker(),
        result_handler=FakeResultHandler(),
        recovery=FakeRecovery(),
    )

    result = intelligence.execute(
        "read file",
        user_confirmation=True,
    )

    assert result.success is True


if __name__ == "__main__":
    print(
        "SAHIBEX 6P-9 TOOL INTELLIGENCE "
        "POST-EXECUTION INTEGRATION TEST: PASS"
    )
