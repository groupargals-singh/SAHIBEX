from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.brain.semantic_intent_brain import SemanticIntentBrain
from core.model_gateway.base import ModelGateway, ModelProvider, ModelRequest, ModelResponse
from core.policies.approval import ActionType


class FixtureProvider(ModelProvider):
    name = "semantic-fixture"

    def __init__(self, payload: object, *, success: bool = True):
        self.payload = payload
        self.success = success
        self.last_request = None

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.last_request = request
        text = self.payload if isinstance(self.payload, str) else json.dumps(self.payload)
        return ModelResponse(
            text=text,
            provider=self.name,
            model="fixture-semantic-v1",
            success=self.success,
            metadata={"fixture": True},
        )


def payload(**overrides):
    data = {
        "intent": "file_operation",
        "action": "delete_file",
        "confidence": 0.96,
        "needs_clarification": False,
        "clarification_question": "",
        "language_code": "es",
        "rationale": "The user asks to delete a file.",
    }
    data.update(overrides)
    return data


def build_brain(data, *, allow_mock_for_tests=False):
    gateway = ModelGateway()
    provider = FixtureProvider(data)
    gateway.register_provider(provider)
    brain = SemanticIntentBrain(
        gateway,
        provider=provider.name,
        allow_mock_for_tests=allow_mock_for_tests,
    )
    return brain, provider


def test_semantic_classifier_accepts_valid_multilingual_action_and_never_authorizes():
    brain, provider = build_brain(payload())
    result = brain.classify("Borra este archivo")
    assert result is not None
    assert result.accepted
    assert result.intent == "file_operation"
    assert result.action is ActionType.DELETE_FILE
    assert result.language_code == "es"
    assert "meaning and context" in provider.last_request.prompt
    assert provider.last_request.metadata["untrusted_input"] is True
    assert not hasattr(result, "permission_allowed")
    assert not hasattr(result, "execute")


@pytest.mark.parametrize(
    "bad_payload",
    [
        "not json",
        [],
        {"intent": "delete_everything"},
        payload(intent=[]),
        payload(action={}),
        payload(action="grant_permission"),
        payload(confidence=True),
        payload(confidence=1.2),
        payload(needs_clarification="false"),
        payload(needs_clarification=True, clarification_question=""),
        payload(extra_field="not allowed"),
    ],
)
def test_semantic_classifier_rejects_invalid_or_unsafe_schema(bad_payload):
    brain, _ = build_brain(bad_payload)
    assert brain.classify("Supprime ce fichier") is None


def test_low_confidence_semantics_requires_clarification():
    brain, _ = build_brain(
        payload(confidence=0.41, needs_clarification=False, clarification_question="")
    )
    result = brain.classify("Do it")
    assert result is not None
    assert result.needs_clarification
    assert not result.accepted
    assert result.clarification_question


def test_explicit_clarification_is_preserved_in_users_language():
    brain, _ = build_brain(
        payload(
            action="respond",
            intent="general_request",
            confidence=0.90,
            needs_clarification=True,
            clarification_question="¿Qué archivo quieres borrar?",
        )
    )
    result = brain.classify("Borra eso")
    assert result is not None
    assert result.needs_clarification
    assert result.clarification_question == "¿Qué archivo quieres borrar?"


def test_mock_provider_is_not_accepted_as_real_semantic_understanding():
    gateway = ModelGateway()
    from core.model_gateway.mock_provider import MockModelProvider
    gateway.register_provider(MockModelProvider())
    with pytest.raises(ValueError, match="Mock provider"):
        SemanticIntentBrain(gateway, provider="mock")


def test_classifier_fails_closed_on_model_provider_error():
    brain, provider = build_brain(payload(), allow_mock_for_tests=False)
    provider.success = False
    assert brain.classify("Borra este archivo") is None


def test_master_brain_routes_semantic_foreign_language_delete_through_security_gate(tmp_path):
    from core.brain.master_brain import MasterBrain
    from core.brain.mother_operational_integration import MotherOperationalIntegration
    from core.research.storage import ResearchStorage
    from security.audit.audit_logger import AuditLogger

    gateway = ModelGateway()
    provider = FixtureProvider(payload())
    gateway.register_provider(provider)
    operational = MotherOperationalIntegration(
        storage=ResearchStorage(tmp_path / "semantic-security.db"),
        model_gateway=gateway,
    )
    semantic = SemanticIntentBrain(gateway, provider=provider.name)
    brain = MasterBrain(
        mother_operational=operational,
        semantic_intent_brain=semantic,
        audit_logger=AuditLogger(tmp_path / "audit"),
    )

    result = brain.process("Borra este archivo", user_confirmation=False)
    assert result.action == ActionType.DELETE_FILE.value
    assert result.success is False
    assert result.permission_allowed is False
    assert result.confirmation_required is True
    assert result.verification_status == "NOT_EXECUTED"
    assert result.metadata.get("tool_execution") is not True
