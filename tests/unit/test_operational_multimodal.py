from __future__ import annotations

from core.brain.multimodal import (
    InputModality,
    MultimodalInput,
)
from core.brain.operational_model import OperationalModelIntegration
from core.brain.operational_multimodal import (
    OperationalMultimodalIntegration,
)
from core.brain.operational_reasoning import (
    OperationalReasoningEngine,
)
from core.model_gateway.base import ModelGateway
from core.model_gateway.mock_provider import MockModelProvider


def build_integration() -> OperationalMultimodalIntegration:
    gateway = ModelGateway()
    gateway.register_provider(MockModelProvider())

    model_integration = OperationalModelIntegration(gateway)

    reasoning_engine = OperationalReasoningEngine(
        model_integration=model_integration,
    )

    return OperationalMultimodalIntegration(
        reasoning_engine=reasoning_engine,
    )


def main() -> None:
    integration = build_integration()

    text_input = MultimodalInput(
        modality=InputModality.TEXT,
        content="Analyze this request.",
    )

    voice_input = MultimodalInput(
        modality=InputModality.VOICE,
        content="Please explain the result.",
    )

    image_input = MultimodalInput(
        modality=InputModality.IMAGE,
        content="Image observation: object detected.",
    )

    result = integration.process(
        objective="Understand the supplied multimodal information.",
        inputs=[
            text_input,
            voice_input,
            image_input,
        ],
        provider="mock",
    )

    assert result.success is True
    assert result.objective == (
        "Understand the supplied multimodal information."
    )

    assert result.modalities == [
        "text",
        "voice",
        "image",
    ]

    assert "[text] Analyze this request." in result.summary
    assert "[voice] Please explain the result." in result.summary
    assert (
        "[image] Image observation: object detected."
        in result.summary
    )

    assert result.reasoning is not None
    assert result.reasoning.success is True
    assert result.reasoning.model_provider == "mock"
    assert result.reasoning.model == "mock-v1"
    assert result.reasoning.model_response.startswith(
        "MOCK MODEL RESPONSE:"
    )

    # Duplicate modalities must remain normalized.
    duplicate_result = integration.process(
        objective="Process repeated multimodal input.",
        inputs=[
            MultimodalInput(
                modality=InputModality.TEXT,
                content="First text.",
            ),
            MultimodalInput(
                modality=InputModality.TEXT,
                content="Second text.",
            ),
            MultimodalInput(
                modality=InputModality.VOICE,
                content="Voice context.",
            ),
        ],
        provider="mock",
    )

    assert duplicate_result.success is True
    assert duplicate_result.modalities == [
        "text",
        "voice",
    ]

    # Invalid input list must be rejected.
    try:
        integration.process(
            objective="Invalid input test.",
            inputs=[],
            provider="mock",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty multimodal input list must be rejected."
        )

    # Invalid input object must be rejected.
    try:
        integration.process(
            objective="Invalid object test.",
            inputs=["not-a-multimodal-input"],
            provider="mock",
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Invalid multimodal input object must be rejected."
        )

    # Provider must be validated.
    try:
        integration.process(
            objective="Provider validation test.",
            inputs=[text_input],
            provider="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty provider must be rejected."
        )

    # No permission-granting or protected execution API.
    forbidden_methods = {
        "grant_permission",
        "execute_action",
        "execute_command",
        "run_command",
        "modify_constitution",
        "override_constitution",
    }

    for method_name in forbidden_methods:
        assert not hasattr(integration, method_name)

    print(
        "SAHIBEX 6O-8 MULTIMODAL RUNTIME "
        "INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
