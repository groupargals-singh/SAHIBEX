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


def test_router_selects_knowledge_only_for_explicit_verified_knowledge_queries():
    router = MotherBrainSpecialistRouter()
    cases = (
        ("What verified knowledge do you have about SAHIBEX?", "SAHIBEX"),
        ("Search knowledge base for SAHIBEX architecture", "SAHIBEX architecture"),
        ("SAHIBEX ke bare mein verified knowledge batao", "SAHIBEX"),
        ("सत्यापित ज्ञान में SAHIBEX खोजो", "SAHIBEX"),
    )
    for request, expected_query in cases:
        route = router.select(request, "general_request")
        assert route is not None and route.role_id == "knowledge"
        assert route.context["query"] == expected_query
        assert route.context["verified_only"] is True


def test_router_does_not_route_ambiguous_or_generic_knowledge_wording():
    router = MotherBrainSpecialistRouter()
    assert router.select("Tell me something about SAHIBEX", "general_request") is None
    assert router.select("What is knowledge?", "general_request") is None
    assert router.select("Search the web for SAHIBEX", "search") is None


def test_verified_knowledge_route_dispatches_through_trust_filtered_brain(monkeypatch):
    from datetime import datetime, timezone
    from types import SimpleNamespace

    brain = MasterBrain()
    calls = {}
    item = SimpleNamespace(
        knowledge_id="verified-1",
        statement="SAHIBEX is a model-independent Main Brain.",
        confidence=0.97,
        verified=True,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        last_verified_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        evidence=["e1", "e2"],
        findings=["f1"],
    )

    def retrieve(query, *, verified_only=False, min_confidence=0.0):
        calls.update(query=query, verified_only=verified_only, min_confidence=min_confidence)
        return SimpleNamespace(success=True, query=query, knowledge=(item,))

    monkeypatch.setattr(brain.knowledge_brain, "retrieve", retrieve)
    request = "What verified knowledge do you have about SAHIBEX?"
    route = brain.specialist_router.select(request, "general_request")
    assert route is not None and route.role_id == "knowledge"
    dispatched = brain.dispatch_internal_brain(
        route.role_id, request, route.context,
        authorization_passed=True, verification_passed=True,
    )
    assert dispatched.accepted is True
    assert calls == {"query": "SAHIBEX", "verified_only": True, "min_confidence": 0.0}
    assert dispatched.result["status"] == "TRUST_FILTERED_KNOWLEDGE_RETRIEVAL"
    assert dispatched.result["trust_filter_applied"] is True
    assert dispatched.result["verified_only"] is True
    assert dispatched.result["items"][0]["knowledge_id"] == "verified-1"
    assert dispatched.result["items"][0]["statement"] == item.statement
    assert dispatched.result["permission_granted"] is False
    assert dispatched.result["actions_executed"] is False


def test_knowledge_handler_cannot_be_downgraded_to_unverified_results(monkeypatch):
    from types import SimpleNamespace

    brain = MasterBrain()
    calls = {}

    def retrieve(query, *, verified_only=False, min_confidence=0.0):
        calls.update(verified_only=verified_only)
        return SimpleNamespace(success=True, query=query, knowledge=())

    monkeypatch.setattr(brain.knowledge_brain, "retrieve", retrieve)
    result = brain._internal_knowledge_handler(
        "knowledge about SAHIBEX",
        {"query": "SAHIBEX", "verified_only": False},
    )
    assert result["success"] is True
    assert calls["verified_only"] is True
    assert result["verified_only"] is True
    assert result["trust_filter_applied"] is True


def test_knowledge_specialist_still_requires_authorization_and_verification():
    brain = MasterBrain()
    request = "Search knowledge base for SAHIBEX"
    route = brain.specialist_router.select(request, "general_request")
    assert route is not None and route.role_id == "knowledge"
    denied = brain.dispatch_internal_brain(
        route.role_id, request, route.context,
        authorization_passed=False, verification_passed=True,
    )
    unverified = brain.dispatch_internal_brain(
        route.role_id, request, route.context,
        authorization_passed=True, verification_passed=False,
    )
    assert denied.accepted is False
    assert unverified.accepted is False



def test_router_selects_conversation_for_explicit_context_recall_and_resume():
    router = MotherBrainSpecialistRouter()
    cases = (
        "What were we discussing?",
        "Continue the previous task",
        "Pick up where we left off",
        "Hum kis par baat kar rahe the?",
        "Pichhla kaam jaari karo",
        "हम क्या बात कर रहे थे?",
        "जहाँ छोड़ा था वहीं से शुरू करो",
    )
    for request in cases:
        route = router.select(request, "general_request")
        assert route is not None and route.role_id == "conversation"
        assert route.context["max_turns"] == 8


def test_router_does_not_route_generic_continue_or_ambiguous_chat():
    router = MotherBrainSpecialistRouter()
    assert router.select("Continue", "general_request") is None
    assert router.select("What should I do next?", "general_request") is None
    assert router.select("Tell me about our project", "general_request") is None


def test_conversation_handler_returns_bounded_history_without_inference_or_execution():
    brain = MasterBrain()
    messages = [
        {"role": "user", "content": "We are building SAHIBEX."},
        {"role": "assistant", "content": "We are working on the Main Brain."},
        {"role": "user", "content": "Next, connect the Knowledge Brain."},
        {"role": "assistant", "content": "Verified-only routing is now connected."},
    ]
    route = brain.specialist_router.select("What were we discussing?", "general_request")
    assert route is not None and route.role_id == "conversation"
    dispatched = brain.dispatch_internal_brain(
        route.role_id, "What were we discussing?", {"messages": messages},
        authorization_passed=True, verification_passed=True,
    )
    assert dispatched.accepted is True
    result = dispatched.result
    assert result["status"] == "BOUNDED_CONVERSATION_CONTEXT_READY"
    assert result["latest_user_request"] == "Next, connect the Knowledge Brain."
    assert result["latest_assistant_response"] == "Verified-only routing is now connected."
    assert result["turn_count"] == 2
    assert result["intent_inferred"] is False
    assert result["historical_instructions_executed"] is False
    assert result["permission_granted"] is False
    assert result["actions_executed"] is False


def test_conversation_handler_fails_closed_on_oversized_or_invalid_history():
    brain = MasterBrain()
    too_many = brain._internal_conversation_handler(
        "history", {"messages": [{"role": "user", "content": "x"}] * 31}
    )
    invalid = brain._internal_conversation_handler(
        "history", {"messages": [{"role": "system", "content": "secret"}]}
    )
    oversized = brain._internal_conversation_handler(
        "history", {"messages": [{"role": "user", "content": "x" * 4001}]}
    )
    assert too_many["status"] == "MESSAGE_LIMIT_EXCEEDED"
    assert invalid["status"] == "MESSAGE_FORMAT_INVALID"
    assert oversized["status"] == "MESSAGE_FORMAT_INVALID"


def test_conversation_role_is_registered_and_requires_both_gates():
    brain = MasterBrain()
    role = next(role for role in brain.internal_brain_team.roles() if role.role_id == "conversation")
    assert role.handler_registered is True
    denied = brain.dispatch_internal_brain(
        "conversation", "history", {"messages": [{"role": "user", "content": "x"}]},
        authorization_passed=False, verification_passed=True,
    )
    unverified = brain.dispatch_internal_brain(
        "conversation", "history", {"messages": [{"role": "user", "content": "x"}]},
        authorization_passed=True, verification_passed=False,
    )
    assert denied.accepted is False
    assert unverified.accepted is False



def test_master_brain_answers_conversation_recall_from_real_context_without_replaying_actions():
    brain = MasterBrain()
    brain.context.add_turn(
        "We are integrating SAHIBEX Knowledge Brain with verified-only retrieval.",
        "The Knowledge specialist routing has been implemented and tested.",
        "general_request",
    )
    result = brain.process("What were we discussing?")
    assert result.success is True
    assert "SAHIBEX Knowledge Brain" in result.message
    assert "verified-only retrieval" in result.message
    assert result.verification_status == "CONVERSATION_CONTEXT_RECALL"
    assert result.metadata["mother_operational_integration"]["provider"] == "conversation_context_brain"
    specialist = result.metadata["automatic_specialist"]["result"]
    assert specialist["status"] == "BOUNDED_CONVERSATION_CONTEXT_READY"
    assert specialist["historical_instructions_executed"] is False
    assert specialist["permission_granted"] is False


def test_conversation_handler_enforces_requested_turn_bound_and_source_contract():
    brain = MasterBrain()
    messages = []
    for index in range(10):
        messages.extend([
            {"role": "user", "content": f"User request {index}"},
            {"role": "assistant", "content": f"Assistant response {index}"},
        ])
    result = brain._internal_conversation_handler(
        "history", {"messages": messages, "max_turns": 3, "history_sources": ["persistent_memory"]}
    )
    assert result["turn_count"] == 3
    assert result["latest_user_request"] == "User request 9"
    assert result["recent_user_requests"] == ["User request 7", "User request 8", "User request 9"]
    assert result["persistent_history_read"] is True
    assert result["history_written"] is False
    bad_limit = brain._internal_conversation_handler(
        "history", {"messages": messages, "max_turns": True}
    )
    bad_source = brain._internal_conversation_handler(
        "history", {"messages": messages, "history_sources": ["untrusted_external"]}
    )
    assert bad_limit["status"] == "CONVERSATION_TURN_LIMIT_INVALID"
    assert bad_source["status"] == "CONVERSATION_HISTORY_SOURCE_INVALID"


def test_hinglish_conversation_recall_responds_in_hinglish_from_context():
    brain = MasterBrain()
    brain.context.add_turn(
        "Hum SAHIBEX ka Knowledge Brain integrate kar rahe the.",
        "Verified-only routing complete ho gayi thi.",
        "general_request",
    )
    result = brain.process("Hum kis par baat kar rahe the?")
    assert result.success is True
    assert "Pichhli baatcheet" in result.message
    assert "SAHIBEX ka Knowledge Brain" in result.message
    assert "purani action" in result.message
    assert result.verification_status == "CONVERSATION_CONTEXT_RECALL"


def test_conversation_recall_reads_trusted_persistent_history_after_restart(monkeypatch):
    from types import SimpleNamespace

    brain = MasterBrain()
    persisted = [
        SimpleNamespace(content="User: We were fixing the SAHIBEX context router.\nSAHIBEX: The bounded history merge is next.")
    ]
    monkeypatch.setattr(brain.memory_brain, "retrieve_recent_conversations", lambda limit=5: persisted)
    result = brain.process("What were we discussing?")
    assert result.success is True
    assert "fixing the SAHIBEX context router" in result.message
    assert "bounded history merge" in result.message
    specialist = result.metadata["automatic_specialist"]["result"]
    assert specialist["persistent_history_read"] is True
    assert "persistent_memory" in specialist["history_sources"]
    assert specialist["history_written"] is False
