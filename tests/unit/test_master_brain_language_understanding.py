from __future__ import annotations

from types import SimpleNamespace

from core.brain.master_brain import MasterBrain
from core.brain.mother_operational_integration import MotherOperationalIntegration
from core.research.storage import ResearchStorage
from security.audit.audit_logger import AuditLogger


def _brain(tmp_path) -> MasterBrain:
    storage = ResearchStorage(tmp_path / "language-understanding.db")
    operational = MotherOperationalIntegration(storage=storage)
    return MasterBrain(
        mother_operational=operational,
        audit_logger=AuditLogger(tmp_path / "audit"),
    )


def test_master_brain_repairs_safe_hinglish_typo_before_curated_answer(tmp_path):
    brain = _brain(tmp_path)
    result = brain.process("sahibaks kya hai?")

    assert result.success is True
    assert result.verification_status == "CURATED_KNOWLEDGE"
    assert "SAHIBEX" in result.message
    trace = result.metadata["input_understanding"]
    assert trace["original_text"] == "sahibaks kya hai?"
    assert trace["normalized_text"] == "SAHIBEX kya hai?"
    assert trace["language_code"] == "hi-Latn"
    assert trace["corrections"][0]["original"] == "sahibaks"
    assert trace["raw_input_preserved"] is True
    assert trace["permission_granted"] is False


def test_master_brain_keeps_uncertain_dictionary_suggestions_unapplied(tmp_path):
    brain = _brain(tmp_path)
    normalized, trace = brain._prepare_user_input("please add dictioary")

    assert normalized == "please add dictioary"
    assert trace["corrections"] == []
    assert any(
        item["original"] == "dictioary" and item["suggested"] == "dictionary"
        for item in trace["suggestions_not_applied"]
    )


def test_master_brain_never_changes_numbers_or_negation_during_normalization(tmp_path):
    brain = _brain(tmp_path)
    original = "SAHIBEX delete mat karna 42 xqz"
    normalized, trace = brain._prepare_user_input(original)

    assert normalized == original
    assert trace["status"] == "NO_SAFE_CORRECTION_NEEDED"
    assert trace["permission_granted"] is False
    assert trace["action_executed"] is False


def test_oversized_input_falls_back_without_breaking_master_pipeline(tmp_path):
    brain = _brain(tmp_path)
    original = "x" * 8193

    normalized, trace = brain._prepare_user_input(original)

    assert normalized == original
    assert trace["status"] == "PERCEPTION_SKIPPED_INPUT_LIMIT_OR_INVALID"
    assert trace["raw_input_preserved"] is True
    assert trace["permission_granted"] is False


def test_raw_protected_action_survives_contextual_rewrite(tmp_path):
    brain = _brain(tmp_path)

    class ContextualFixture:
        def understand(self, _text):
            return SimpleNamespace(
                changed=True,
                corrected_text="delight the file tomorrow please",
                status="CONTEXTUAL_REPAIR_ACCEPTED",
                confidence=0.96,
                language_code="en",
            )

    brain.contextual_input_understanding_brain = ContextualFixture()
    result = brain.process("delete the file tomorow plese")

    assert result.action == "delete_file"
    assert result.permission_allowed is False
    assert result.confirmation_required is True
    assert result.verification_status == "NOT_EXECUTED"
    assert result.metadata["input_understanding"]["normalized_text"] == "delight the file tomorrow please"


def test_contextual_hinglish_fix_request_uses_recent_software_context(tmp_path):
    brain = _brain(tmp_path)
    brain.context.add_turn(
        user="The bug is in core/brain/intent.py.",
        assistant="I found a bug in the Python intent matcher.",
        intent="code",
    )

    result = brain.process("isko thik kro")

    assert result.intent == "code"
    assert result.action == "create"
    assert result.plan_created is True
    assert result.metadata.get("action_executed") is not True
    assert result.permission_allowed is True


def test_hinglish_fix_request_without_context_asks_what_to_fix(tmp_path):
    brain = _brain(tmp_path)
    result = brain.process("isko thik kro")

    assert result.verification_status == "CLARIFICATION_REQUIRED"
    assert result.plan_created is False
    assert result.permission_allowed is False
    assert result.metadata.get("action_executed") is False


def test_explicit_hinglish_bug_fix_is_classified_as_code(tmp_path):
    brain = _brain(tmp_path)
    result = brain.process("is bug ko fix karo")

    assert result.intent == "code"
    assert result.plan_created is True
    assert result.metadata.get("action_executed") is not True


def test_contextual_fix_intent_recovers_from_persistent_memory_after_restart(tmp_path, monkeypatch):
    monkeypatch.setenv("SAHIBEX_SEMANTIC_INTENT_ENABLED", "0")
    monkeypatch.setenv("SAHIBEX_CONTEXTUAL_INPUT_ENABLED", "0")
    database = tmp_path / "persistent-context.db"
    first_storage = ResearchStorage(database)
    first = MasterBrain(
        mother_operational=MotherOperationalIntegration(storage=first_storage),
        audit_logger=AuditLogger(tmp_path / "audit-first"),
    )
    first.memory_brain.remember_interaction(
        user_text="The bug is in a Python script.",
        assistant_text="I found the bug in the script.",
        intent="code", action="create", verification_status="INSUFFICIENT_EVIDENCE",
    )

    restarted_storage = ResearchStorage(database)
    restarted = MasterBrain(
        mother_operational=MotherOperationalIntegration(storage=restarted_storage),
        audit_logger=AuditLogger(tmp_path / "audit-restarted"),
    )
    assert restarted.context.recent(1) == []

    result = restarted.process("isko thik kro")

    assert result.intent == "code"
    assert result.plan_created is True
    assert result.metadata.get("action_executed") is not True
    first_storage.close()
    restarted_storage.close()


def test_master_brain_asks_before_routing_ambiguous_word(tmp_path):
    brain = _brain(tmp_path)
    result = brain.process("Explain bank")

    assert result.success is False
    assert result.verification_status == "CLARIFICATION_REQUIRED"
    assert "financial bank" in result.message
    assert result.plan_created is False
    assert result.metadata["confidence_verification"]["decision"] == "CLARIFICATION_REQUIRED"
    assert result.metadata["action_executed"] is False
    assert result.permission_allowed is False


def test_master_brain_does_not_treat_its_own_clarification_as_context(tmp_path):
    brain = _brain(tmp_path)
    first = brain.process("Explain bank")
    second = brain.process("bank")

    assert first.verification_status == "CLARIFICATION_REQUIRED"
    assert second.verification_status == "CLARIFICATION_REQUIRED"


def test_master_brain_asks_for_missing_action_target(tmp_path):
    brain = _brain(tmp_path)
    result = brain.process("delete it")

    assert result.verification_status == "CLARIFICATION_REQUIRED"
    assert "Which file" in result.message
    assert result.permission_allowed is False
    assert result.plan_created is False


def test_master_brain_uses_existing_context_for_demonstrative(tmp_path):
    brain = _brain(tmp_path)
    brain.context.add_turn(
        user="We are discussing Python programming.",
        assistant="Python is a programming language.",
        intent="explain",
    )
    result = brain.process("What is this?")

    assert result.verification_status != "CLARIFICATION_REQUIRED"
    assert result.metadata["confidence_verification"]["clarification_required"] is False


def test_master_brain_reports_factual_status_separately_from_routing(tmp_path):
    brain = _brain(tmp_path)
    result = brain.process("sahibaks kya hai?")

    assert result.verification_status == "CURATED_KNOWLEDGE"
    confidence = result.metadata["confidence_verification"]
    assert confidence["decision"] == "PROCEED"
    assert confidence["factual_claim_status"] == "CURATED_NOT_INDEPENDENTLY_VERIFIED"
    assert result.metadata["factual_verification_assessment"]["verified"] is False
    assert result.metadata["factual_verification"] == "CURATED_NOT_INDEPENDENTLY_VERIFIED"


def test_master_brain_does_not_use_unrelated_context_as_action_target(tmp_path):
    brain = _brain(tmp_path)
    brain.context.add_turn(
        user="We are discussing Python programming.",
        assistant="Python is a programming language.",
        intent="explain",
    )
    result = brain.process("delete it")

    assert result.verification_status == "CLARIFICATION_REQUIRED"
    assert result.permission_allowed is False
    assert result.plan_created is False


def test_master_brain_uses_contextual_file_reference_but_keeps_permission_gate(tmp_path):
    brain = _brain(tmp_path)
    brain.context.add_turn(
        user="The report.docx file is the selected target.",
        assistant="I understand that report.docx is the file under discussion.",
        intent="file_operation",
    )
    result = brain.process("delete it")

    assert result.verification_status != "CLARIFICATION_REQUIRED"
    assert result.action == "delete_file"
    assert result.permission_allowed is False
    assert result.confirmation_required is True
