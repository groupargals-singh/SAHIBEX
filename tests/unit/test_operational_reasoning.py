from __future__ import annotations

from core.brain.operational_model import OperationalModelIntegration
from core.brain.operational_reasoning import (
    OperationalReasoningEngine,
    OperationalReasoningResult,
)
from core.model_gateway.base import ModelGateway
from core.model_gateway.mock_provider import MockModelProvider


def build_engine() -> OperationalReasoningEngine:
    gateway = ModelGateway()
    gateway.register_provider(MockModelProvider())

    model_integration = OperationalModelIntegration(
        gateway
    )

    return OperationalReasoningEngine(
        model_integration=model_integration
    )


def test_operational_reasoning_result_contract() -> None:
    result = OperationalReasoningResult(
        success=True,
        user_input="Explain Python.",
        intent="explain",
        action="respond",
        reasoning_response="Explanation request detected.",
        model_response="Python is a programming language.",
        model_provider="mock",
        model="mock-v1",
        requires_confirmation=False,
        verification_status="VERIFIED",
    )

    assert result.success is True
    assert result.user_input == "Explain Python."
    assert result.intent == "explain"
    assert result.action == "respond"
    assert result.model_provider == "mock"
    assert result.model == "mock-v1"
    assert result.requires_confirmation is False
    assert result.verification_status == "VERIFIED"
    assert result.reasoning_id.strip()


def test_operational_reasoning_calls_model_gateway() -> None:
    engine = build_engine()

    result = engine.process(
        user_input="Explain Python.",
        provider="mock",
    )

    assert result.success is True
    assert result.user_input == "Explain Python."
    assert result.intent == "code"
    assert result.action == "create"
    assert result.model_provider == "mock"
    assert result.model == "mock-v1"
    assert result.model_response.startswith(
        "MOCK MODEL RESPONSE:"
    )
    assert result.verification_status == "VERIFIED"
    assert result.requires_confirmation is False


def test_empty_input_is_rejected() -> None:
    engine = build_engine()

    try:
        engine.process(
            user_input="   ",
            provider="mock",
        )
        raise AssertionError(
            "Expected ValueError for empty input"
        )
    except ValueError:
        pass


def test_empty_provider_is_rejected() -> None:
    engine = build_engine()

    try:
        engine.process(
            user_input="Explain Python.",
            provider="   ",
        )
        raise AssertionError(
            "Expected ValueError for empty provider"
        )
    except ValueError:
        pass


def test_unknown_provider_is_rejected() -> None:
    engine = build_engine()

    try:
        engine.process(
            user_input="Explain Python.",
            provider="unknown-provider",
        )
        raise AssertionError(
            "Expected KeyError for unknown provider"
        )
    except KeyError:
        pass


def test_protected_delete_requires_confirmation() -> None:
    engine = build_engine()

    result = engine.process(
        user_input="Delete the project files.",
        provider="mock",
    )

    assert result.success is False
    assert result.intent == "general_request"
    assert result.action == "delete_file"
    assert result.requires_confirmation is True
    assert result.verification_status == "VERIFIED"
    assert result.model_response == ""


def test_protected_command_requires_confirmation() -> None:
    engine = build_engine()

    result = engine.process(
        user_input=(
            "Run a shell command to delete "
            "the project files."
        ),
        provider="mock",
    )

    assert result.success is False
    assert result.intent == "general_request"
    assert result.action == "run_command"
    assert result.requires_confirmation is True
    assert result.verification_status == "VERIFIED"
    assert result.model_response == ""


def test_protected_write_requires_confirmation() -> None:
    engine = build_engine()

    result = engine.process(
        user_input="Write a file to the project.",
        provider="mock",
    )

    assert result.success is False
    assert result.intent == "file_operation"
    assert result.action == "write_file"
    assert result.requires_confirmation is True
    assert result.verification_status == "VERIFIED"
    assert result.model_response == ""


def test_forbidden_execution_methods_are_absent() -> None:
    engine = build_engine()

    forbidden_methods = {
        "execute_tool",
        "run_command",
        "grant_permission",
        "override_constitution",
        "delete_file",
        "write_file",
        "network_request",
    }

    for method_name in forbidden_methods:
        assert not hasattr(engine, method_name)


if __name__ == "__main__":
    test_operational_reasoning_result_contract()
    test_operational_reasoning_calls_model_gateway()
    test_empty_input_is_rejected()
    test_empty_provider_is_rejected()
    test_unknown_provider_is_rejected()
    test_protected_delete_requires_confirmation()
    test_protected_command_requires_confirmation()
    test_protected_write_requires_confirmation()
    test_forbidden_execution_methods_are_absent()

    print(
        "SAHIBEX 6O-3 MASTER BRAIN REASONING ENGINE TEST: PASS"
    )
