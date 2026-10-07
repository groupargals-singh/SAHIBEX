from __future__ import annotations

from core.brain.mother_reasoning_integration import (
    MotherReasoningIntegration,
)


def main() -> None:
    integration = MotherReasoningIntegration()

    result = integration.analyze_approved_request(
        user_input="Explain what artificial intelligence is.",
        intent="explain",
        action="approved_cognitive_response",
    )

    assert result.success is True
    assert result.user_input == (
        "Explain what artificial intelligence is."
    )
    assert result.intent == "explain"
    assert result.action == "approved_cognitive_response"
    assert result.reasoning_response
    assert result.reasoning_status == "COMPLETED"

    print(
        "SAHIBEX MOTHER REASONING INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
