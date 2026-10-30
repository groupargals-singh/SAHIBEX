from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.brain.master_brain import MasterBrain
from core.brain.semantic_intent_brain import SemanticIntentBrain
from core.brain.universal_language_brain import UniversalLanguageBrain
from core.brain.mother_operational_integration import MotherOperationalIntegration
from core.model_gateway.base import ModelGateway, ModelProvider, ModelRequest, ModelResponse
from core.policies.approval import ActionType
from core.research.storage import ResearchStorage
from security.audit.audit_logger import AuditLogger


class MultilingualFixtureProvider(ModelProvider):
    name = "multilingual-regression-fixture"

    def __init__(self, routes):
        self.routes = routes

    def generate(self, request: ModelRequest) -> ModelResponse:
        encoded = request.prompt.split("REQUEST_JSON:\n", 1)[-1].split("\nReturn strict JSON", 1)[0]
        request_text = json.loads(encoded)
        result = self.routes.get(request_text)
        if result is None:
            return ModelResponse("", self.name, "fixture-v1", False, error="No fixture route")
        return ModelResponse(
            json.dumps(result, ensure_ascii=False),
            self.name,
            "fixture-v1",
            True,
            metadata={"fixture": True},
        )


def semantic_route(action: str, *, intent: str = "general_request", language: str = "und"):
    return {
        "intent": intent,
        "action": action,
        "confidence": 0.97,
        "needs_clarification": False,
        "clarification_question": "",
        "language_code": language,
        "rationale": "Fixture classification for a regression test.",
    }


def test_language_detection_regression_for_common_and_mixed_languages():
    language = UniversalLanguageBrain()
    cases = [
        ("Delete this file", "en"),
        ("Borra este archivo", "es"),
        ("Supprime ce fichier", "fr"),
        ("Lösche diese Datei", "de"),
        ("このファイルを削除して", "ja"),
        ("删除这个文件", "zh"),
        ("احذف هذا الملف", "ar"),
        ("इस फाइल को डिलीट करो", "hi"),
        ("Mujhe explain karo", "hi-Latn"),
    ]
    for text, expected in cases:
        result = language.detect(text)
        assert result.language_code == expected, (text, result)
        assert result.confidence > 0
    mixed = language.detect("Please mujhe explain karo")
    assert mixed.mixed is True


def test_multilingual_protected_actions_never_bypass_permission_or_audit(tmp_path):
    routes = {
        "Borra este archivo": semantic_route("delete_file", intent="file_operation", language="es"),
        "Exécute cette commande": semantic_route("run_command", language="fr"),
        "Zeige das Passwort": semantic_route("credential_use", language="de"),
        "转账给他钱": semantic_route("financial_action", language="zh"),
        "システム設定を変更して": semantic_route("system_change", language="ja"),
        "نزّل هذا الملف": semantic_route("network_access", language="ar"),
        "Edita este archivo": semantic_route("write_file", intent="file_operation", language="es"),
    }
    gateway = ModelGateway()
    provider = MultilingualFixtureProvider(routes)
    gateway.register_provider(provider)
    operational = MotherOperationalIntegration(
        storage=ResearchStorage(tmp_path / "multilingual-security.db"),
        model_gateway=gateway,
    )
    audit = AuditLogger(tmp_path / "audit")
    brain = MasterBrain(
        mother_operational=operational,
        semantic_intent_brain=SemanticIntentBrain(gateway, provider=provider.name),
        audit_logger=audit,
    )

    expected = {
        "Borra este archivo": ActionType.DELETE_FILE,
        "Exécute cette commande": ActionType.RUN_COMMAND,
        "Zeige das Passwort": ActionType.CREDENTIAL_USE,
        "转账给他钱": ActionType.FINANCIAL_ACTION,
        "システム設定を変更して": ActionType.SYSTEM_CHANGE,
        "نزّل هذا الملف": ActionType.NETWORK_ACCESS,
        "Edita este archivo": ActionType.WRITE_FILE,
    }
    for request, expected_action in expected.items():
        result = brain.process(request, user_confirmation=False)
        assert result.action == expected_action.value, (request, result)
        assert result.success is False, (request, result)
        assert result.permission_allowed is False, (request, result)
        assert result.confirmation_required is True, (request, result)
        assert result.verification_status == "NOT_EXECUTED", (request, result)

    audit_files = list((tmp_path / "audit").glob("*.jsonl"))
    assert audit_files, "blocked multilingual actions must be audited"
    audit_lines = sum(len(path.read_text(encoding="utf-8").splitlines()) for path in audit_files)
    assert audit_lines >= len(expected)


def test_semantic_classifier_disabled_by_default_without_a_real_model(monkeypatch):
    monkeypatch.delenv("SAHIBEX_SEMANTIC_INTENT_ENABLED", raising=False)
    brain = MasterBrain()
    assert brain.semantic_intent_brain is None
