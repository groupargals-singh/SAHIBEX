from core.brain.mother_brain_specialist_router import MotherBrainSpecialistRouter
from core.brain.master_brain import MasterBrain


def test_router_selects_math_for_hinglish_arithmetic():
    route = MotherBrainSpecialistRouter().select("2 + 2 kitna hota hai?", "general_request")
    assert route is not None
    assert route.role_id == "math"
    assert route.context["expression"] == "2 + 2 kitna hota hai?"


def test_router_selects_teaching_for_explicit_learning_intent():
    route = MotherBrainSpecialistRouter().select("Mujhe Python sikhao", "learn")
    assert route is not None
    assert route.role_id == "teaching"
    assert route.context["topic"] == "Mujhe Python sikhao"


def test_router_selects_language_only_for_explicit_language_detection_request():
    route = MotherBrainSpecialistRouter().select("Detect language of hello", "general_request")
    assert route is not None
    assert route.role_id == "language"
    assert route.context["text"] == "Detect language of hello"


def test_router_does_not_claim_translation_capability():
    assert MotherBrainSpecialistRouter().select("Translate hello to Hindi", "general_request") is None


def test_router_does_not_misroute_numeric_dates_as_arithmetic():
    assert MotherBrainSpecialistRouter().select("My appointment is on 12/11/2026", "general_request") is None


def test_router_does_not_fan_out_or_guess_on_generic_chat():
    router = MotherBrainSpecialistRouter()
    assert router.select("Namaste Sahibex", "general_request") is None
    assert router.select("Please help me", "general_request") is None


def test_router_rejects_empty_or_invalid_input():
    router = MotherBrainSpecialistRouter()
    assert router.select("", "general_request") is None
    assert router.select("hello", None) is None


def test_selected_language_role_dispatches_through_mother_brain():
    brain = MasterBrain()
    route = brain.specialist_router.select("Detect language of hello", "general_request")
    assert route is not None and route.role_id == "language"
    dispatched = brain.dispatch_internal_brain(
        route.role_id, "Detect language of hello", route.context,
        authorization_passed=True, verification_passed=True,
    )
    assert dispatched.accepted is True
    assert dispatched.result["success"] is True
    assert dispatched.result["translation_performed"] is False


def test_selected_teaching_role_dispatches_through_mother_brain():
    brain = MasterBrain()
    route = brain.specialist_router.select("Mujhe Python sikhao", "learn")
    assert route is not None and route.role_id == "teaching"
    dispatched = brain.dispatch_internal_brain(
        route.role_id, "Mujhe Python sikhao", route.context,
        authorization_passed=True, verification_passed=True,
    )
    assert dispatched.accepted is True
    assert dispatched.result["success"] is True
    assert dispatched.result["external_research_performed"] is False


def test_router_selects_debugging_for_explicit_bug_fix_request():
    route = MotherBrainSpecialistRouter().select("Please fix this Python bug", "code")
    assert route is not None and route.role_id == "debugging"
    failure = route.context["failures"][0]
    assert failure["symptom"] == "Please fix this Python bug"
    assert failure["reproduction_steps"] == []
    assert failure["expected"] is None
    assert failure["observed"] is None
    assert failure["error_excerpt"] == ""


def test_router_selects_debugging_for_hinglish_bug_repair_request():
    route = MotherBrainSpecialistRouter().select("Is bug ko thik karo", "code")
    assert route is not None and route.role_id == "debugging"


def test_router_selects_debugging_for_hindi_error_repair_request():
    route = MotherBrainSpecialistRouter().select("इस एरर को ठीक करो", "code")
    assert route is not None and route.role_id == "debugging"


def test_router_does_not_route_error_explanation_as_debugging():
    assert MotherBrainSpecialistRouter().select("Explain what HTTP error 404 means", "explain") is None


def test_router_does_not_route_generic_code_creation_as_debugging():
    assert MotherBrainSpecialistRouter().select("Write Python code to add two numbers", "code") is None


def test_selected_debugging_role_dispatches_as_evidence_incomplete_without_side_effects():
    brain = MasterBrain()
    route = brain.specialist_router.select("Please fix this Python bug", "code")
    assert route is not None and route.role_id == "debugging"
    dispatched = brain.dispatch_internal_brain(
        route.role_id, "Please fix this Python bug", route.context,
        authorization_passed=True, verification_passed=True,
    )
    assert dispatched.accepted is True
    assert dispatched.result["status"] == "SUPPLIED_FAILURE_REPORTS_TRIAGED_NOT_EXECUTED"
    assert dispatched.result["triage"][0]["status"] == "EVIDENCE_INCOMPLETE"
    assert "REPRODUCTION_STEPS_MISSING" in dispatched.result["triage"][0]["diagnostic_gaps"]
    assert dispatched.result["executes_code"] is False
    assert dispatched.result["writes_filesystem"] is False
    assert dispatched.result["root_cause_confirmed"] is False


def test_router_selects_reading_for_explicit_supplied_text():
    route = MotherBrainSpecialistRouter().select(
        "Read this text: Alpha\nBeta", "general_request"
    )
    assert route is not None and route.role_id == "reading"
    assert route.context["source_text"] == "Alpha\nBeta"


def test_router_selects_document_brain_for_supplied_document_text():
    route = MotherBrainSpecialistRouter().select(
        "Summarize this document: Title\nPoint one\nPoint two", "general_request"
    )
    assert route is not None and route.role_id == "document_file"
    assert route.context["document_text"] == "Title\nPoint one\nPoint two"


def test_router_keeps_document_path_unread_and_reports_missing_text():
    route = MotherBrainSpecialistRouter().select(
        "Summarize this document", "general_request"
    )
    assert route is not None and route.role_id == "document_file"
    assert route.context["document_text"] == ""


def test_router_does_not_treat_generic_read_as_file_access():
    assert MotherBrainSpecialistRouter().select("Read my mind", "general_request") is None


def test_selected_reading_role_dispatches_supplied_text_only():
    brain = MasterBrain()
    request = "Read this text: Alpha\nBeta"
    route = brain.specialist_router.select(request, "general_request")
    assert route is not None and route.role_id == "reading"
    dispatched = brain.dispatch_internal_brain(
        route.role_id, request, route.context,
        authorization_passed=True, verification_passed=True,
    )
    assert dispatched.accepted is True
    assert dispatched.result["status"] == "EXTRACTED_NOT_FACT_VERIFIED"
    assert dispatched.result["excerpt"] == "Alpha\nBeta"


def test_selected_document_role_dispatches_supplied_text_without_filesystem_access():
    brain = MasterBrain()
    request = "Summarize this document: Title\nPoint one\nPoint two"
    route = brain.specialist_router.select(request, "general_request")
    assert route is not None and route.role_id == "document_file"
    dispatched = brain.dispatch_internal_brain(
        route.role_id, request, route.context,
        authorization_passed=True, verification_passed=True,
    )
    assert dispatched.accepted is True
    assert dispatched.result["status"] == "SOURCE_GROUNDED_EXTRACTION_NOT_FACT_VERIFIED"
    assert dispatched.result["extracted_points"] == ["Title", "Point one", "Point two"]
    assert dispatched.result["reads_files"] is False
    assert dispatched.result["writes_files"] is False


def test_selected_document_role_requires_explicit_source_text():
    brain = MasterBrain()
    request = "Summarize this document"
    route = brain.specialist_router.select(request, "general_request")
    assert route is not None
    dispatched = brain.dispatch_internal_brain(
        route.role_id, request, route.context,
        authorization_passed=True, verification_passed=True,
    )
    assert dispatched.accepted is True
    assert dispatched.result["status"] == "DOCUMENT_TEXT_REQUIRED"
    assert dispatched.result["reads_files"] is False


def test_router_extracts_document_payload_from_polite_request():
    route = MotherBrainSpecialistRouter().select(
        "Could you summarize this document: Important text", "general_request"
    )
    assert route is not None and route.role_id == "document_file"
    assert route.context["document_text"] == "Important text"


def test_router_extracts_hinglish_document_payload():
    route = MotherBrainSpecialistRouter().select(
        "Is document ka summary: Pehla point\nDusra point", "general_request"
    )
    assert route is not None and route.role_id == "document_file"
    assert route.context["document_text"] == "Pehla point\nDusra point"


def test_router_extracts_hinglish_reading_payload():
    route = MotherBrainSpecialistRouter().select(
        "Is text ko padho: Namaste\nDuniya", "general_request"
    )
    assert route is not None and route.role_id == "reading"
    assert route.context["source_text"] == "Namaste\nDuniya"


def test_router_selects_memory_for_explicit_recall_request():
    route = MotherBrainSpecialistRouter().select(
        "What do you remember about the SAHIBEX roadmap?", "general_request"
    )
    assert route is not None and route.role_id == "memory"
    assert route.context["query"] == "the SAHIBEX roadmap"


def test_router_selects_memory_for_hinglish_recall_request():
    route = MotherBrainSpecialistRouter().select(
        "Tumhe SAHIBEX ke roadmap ke bare me kya yaad hai?", "general_request"
    )
    assert route is not None and route.role_id == "memory"
    assert route.context["query"] == "SAHIBEX ke roadmap"


def test_router_does_not_route_generic_memory_wording():
    assert MotherBrainSpecialistRouter().select("I have a good memory", "general_request") is None


def test_memory_route_dispatches_with_bounded_sanitized_read_only_result(monkeypatch):
    from datetime import datetime, timezone
    from types import SimpleNamespace

    brain = MasterBrain()
    sample = SimpleNamespace(
        memory_id="m-1", content="SAHIBEX roadmap note", memory_type="project_fact",
        source="user-confirmed", importance=0.9, confidence=0.95,
        tags=["SAHIBEX", "roadmap"], created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        metadata={"private_internal_field": "must not leak"},
    )
    monkeypatch.setattr(brain.memory_brain, "retrieve", lambda query: [sample])
    request = "What do you remember about the SAHIBEX roadmap?"
    route = brain.specialist_router.select(request, "general_request")
    assert route is not None and route.role_id == "memory"
    dispatched = brain.dispatch_internal_brain(
        route.role_id, request, route.context,
        authorization_passed=True, verification_passed=True,
    )
    assert dispatched.accepted is True
    result = dispatched.result
    assert result["status"] == "MEMORY_RETRIEVAL_ONLY"
    assert result["trust_filter_applied"] is True
    assert result["query"] == "the SAHIBEX roadmap"
    assert result["matches"][0]["content"] == "SAHIBEX roadmap note"
    assert "metadata" not in result["matches"][0]
    assert result["writes_memory"] is False
    assert result["deletes_memory"] is False
    assert result["permission_granted"] is False


def test_router_extracts_hindi_document_payload():
    route = MotherBrainSpecialistRouter().select(
        "इस दस्तावेज़ का सार: पहला बिंदु\nदूसरा बिंदु", "general_request"
    )
    assert route is not None and route.role_id == "document_file"
    assert route.context["document_text"] == "पहला बिंदु\nदूसरा बिंदु"


def test_router_extracts_hindi_reading_payload():
    route = MotherBrainSpecialistRouter().select(
        "इस टेक्स्ट को पढ़: नमस्ते\nदुनिया", "general_request"
    )
    assert route is not None and route.role_id == "reading"
    assert route.context["source_text"] == "नमस्ते\nदुनिया"
