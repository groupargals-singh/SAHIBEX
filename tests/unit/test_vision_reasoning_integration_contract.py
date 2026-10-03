from __future__ import annotations

from core.brain.vision_reasoning import (
    VisionReasoningIntegration,
    VisionReasoningResult,
)


def main() -> None:
    integration = VisionReasoningIntegration()

    result = integration.analyze(
        vision_input_id="vision-123",
        observation="A red object is visible.",
    )

    assert isinstance(result, VisionReasoningResult)
    assert result.vision_input_id == "vision-123"
    assert result.observation == "A red object is visible."
    assert result.result_id

    second = integration.analyze(
        vision_input_id="vision-456",
        observation="A person is standing near a door.",
    )

    assert second.vision_input_id == "vision-456"
    assert second.observation == (
        "A person is standing near a door."
    )

    assert result.result_id != second.result_id

    try:
        integration.analyze(
            vision_input_id="",
            observation="Something is visible.",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty vision_input_id must be rejected."
        )

    try:
        integration.analyze(
            vision_input_id="vision-123",
            observation="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty observation must be rejected."
        )

    fields = VisionReasoningResult.__dataclass_fields__

    forbidden_fields = {
        "permission",
        "authorization",
        "api_key",
        "credential",
    }

    assert forbidden_fields.isdisjoint(fields.keys())

    print(
        "SAHIBEX 6M-7 VISION REASONING INTEGRATION CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
