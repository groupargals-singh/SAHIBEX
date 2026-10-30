from __future__ import annotations

from core.brain.mother_operational_integration import MotherOperationalIntegration
from core.research.memory_object import MemoryCandidate


def test_old_conversation_answers_are_not_context_for_ordinary_queries() -> None:
    conversation = MemoryCandidate(
        memory_id="old-conversation",
        content="User: Hello SAHIBEX.\nSAHIBEX: SAHIBEX is the personal AI Main Brain.",
        memory_type="conversation",
        source="master_brain",
        metadata={"verification_status": "STRUCTURALLY_VALID"},
    )
    project = MemoryCandidate(
        memory_id="project-memory",
        content="SAHIBEX is the personal AI Main Brain.",
        memory_type="project",
        source="user",
    )

    selected = MotherOperationalIntegration._context_memories_for_request(
        "Hello SAHIBEX, reply in one short sentence.",
        [conversation, project],
    )

    assert [item.memory_id for item in selected] == ["project-memory"]


def test_explicit_previous_conversation_recall_can_use_conversation_memory() -> None:
    conversation = MemoryCandidate(
        memory_id="old-conversation",
        content="User: What did I ask earlier?\nSAHIBEX: We discussed voice testing.",
        memory_type="conversation",
        source="master_brain",
    )

    selected = MotherOperationalIntegration._context_memories_for_request(
        "What did I ask earlier?",
        [conversation],
    )

    assert [item.memory_id for item in selected] == ["old-conversation"]


def test_live_operational_greeting_fast_path_matches_english_and_hindi() -> None:
    from core.brain.universal_language_brain import UniversalLanguageBrain
    from core.research.storage import ResearchStorage

    storage = ResearchStorage(":memory:")
    integration = MotherOperationalIntegration(storage=storage)
    english = integration.process_approved_request(
        objective="Hello SAHIBEX, reply in one short sentence.",
        intent="general_request",
        provider="mock",
    )
    hindi_question = "नमस्ते साहिबेक्स, एक वाक्य में जवाब दें।"
    hindi = integration.process_approved_request(
        objective=hindi_question,
        intent="general_request",
        provider="mock",
    )

    assert english.success is True
    assert english.response == "Hello! How can I help you?"
    assert english.provider == "deterministic_greeting"
    assert english.diagnostics["factual_verification"] is False

    assert UniversalLanguageBrain().detect(hindi_question).language_code == "hi"
    assert hindi.success is True
    assert hindi.response == "नमस्ते! मैं आपकी कैसे मदद कर सकती हूँ?"
    assert hindi.provider == "deterministic_greeting"
    assert hindi.diagnostics["language_match"] == "MATCH"
    storage.close()
