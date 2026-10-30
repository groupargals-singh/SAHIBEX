from __future__ import annotations

import json

from core.brain.contextual_input_understanding import ContextualInputUnderstandingBrain
from core.model_gateway.base import ModelGateway, ModelProvider, ModelRequest, ModelResponse


class FixtureProvider(ModelProvider):
    name = "contextual-fixture"

    def __init__(self, payload, success=True):
        self.payload = payload
        self.success = success

    def generate(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            text=json.dumps(self.payload, ensure_ascii=False),
            provider=self.name,
            model="fixture-v1",
            success=self.success,
        )


def build(payload):
    gateway = ModelGateway()
    provider = FixtureProvider(payload)
    gateway.register_provider(provider)
    return ContextualInputUnderstandingBrain(gateway, provider=provider.name)


def result_payload(corrected, confidence=0.96, **overrides):
    value = {
        "corrected_text": corrected,
        "confidence": confidence,
        "language_code": "hi-Latn",
        "intent_summary": "User wants the assistant to understand mistyped language.",
        "needs_clarification": False,
    }
    value.update(overrides)
    return value


def test_contextual_typo_repair_accepts_high_confidence_meaning_preserving_text():
    brain = build(result_payload(
        "Pehle ise sahi karo, kya GPT jaise baat samajhni chahiye?",
        confidence=0.96,
    ))
    result = brain.understand("Pahle ise sahi kro kya gpt jese bat samjhni chahiye")
    assert result.changed
    assert result.status == "CONTEXTUAL_REPAIR_ACCEPTED"
    assert result.corrected_text.startswith("Pehle ise sahi karo")


def test_contextual_repair_rejects_number_changes():
    brain = build(result_payload("delete file 99", confidence=0.99))
    result = brain.understand("delete file 42")
    assert not result.changed
    assert result.corrected_text == "delete file 42"
    assert result.status == "REJECTED_NUMERIC_MISMATCH"


def test_contextual_repair_rejects_negation_changes():
    brain = build(result_payload("file delete kar do", confidence=0.99))
    result = brain.understand("file delete mat karna")
    assert not result.changed
    assert result.corrected_text == "file delete mat karna"
    assert result.status == "REJECTED_NEGATION_MISMATCH"


def test_contextual_repair_requires_high_confidence_and_preserves_original():
    brain = build(result_payload(
        "weather tomorrow", confidence=0.55, needs_clarification=True,
    ))
    result = brain.understand("wether tomorow")
    assert not result.changed
    assert result.corrected_text == "wether tomorow"
    assert result.status == "CLARIFICATION_OR_LOW_CONFIDENCE"


def test_contextual_repair_provider_failure_fails_closed():
    gateway = ModelGateway()
    provider = FixtureProvider(result_payload("changed words"), success=False)
    gateway.register_provider(provider)
    brain = ContextualInputUnderstandingBrain(gateway, provider=provider.name)
    result = brain.understand("original words")
    assert not result.changed
    assert result.corrected_text == "original words"
    assert result.status == "UNCHANGED_NO_MODEL_RESULT"
