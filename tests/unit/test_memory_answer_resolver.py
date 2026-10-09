from core.brain.memory_answer_resolver import resolve_memory_fact
from core.brain.mother_operational_integration import MotherOperationalIntegration
from core.research.memory_object import MemoryCandidate
from core.research.storage import ResearchStorage


def memory(memory_id: str, content: str, *, confidence: float = 0.99, importance: float = 0.9, memory_type: str = "user_context") -> MemoryCandidate:
    return MemoryCandidate(
        memory_id=memory_id,
        content=content,
        memory_type=memory_type,
        source="test",
        importance=importance,
        confidence=confidence,
        tags=["project", "codename"],
    )


def test_direct_codename_recall_requires_exact_question_and_trusted_memory_type():
    item = memory("m1", "User preference: the private project codename is ORBITAL_FALCON.")
    result = resolve_memory_fact("What is my project codename?", [item])
    assert result is not None
    assert "ORBITAL_FALCON" in result.answer
    assert result.memory_id == "m1"
    assert resolve_memory_fact("Delete the project files", [item]) is None
    assert resolve_memory_fact(
        "What is my project codename?",
        [memory("m2", item.content, memory_type="episodic")],
    ) is None


def test_ambiguous_or_low_confidence_memories_are_not_used():
    first = memory("m1", "Project codename is ORBITAL_FALCON.")
    second = memory("m2", "Project codename is BLUE_HAWK.")
    assert resolve_memory_fact("What is my project codename?", [first, second]) is None
    assert resolve_memory_fact(
        "What is my project codename?",
        [memory("m3", first.content, confidence=0.4)],
    ) is None


def test_operational_brain_answers_from_persistent_memory_without_model_echo(tmp_path):
    storage = ResearchStorage(tmp_path / "memory.db")
    storage.save_memory(
        memory("m1", "User preference: the private project codename is ORBITAL_FALCON.")
    )
    brain = MotherOperationalIntegration(storage=storage)

    result = brain.process_approved_request(
        objective="What is my project codename?",
        intent="general_request",
    )

    assert result.success is True
    assert "ORBITAL_FALCON" in result.response
    assert result.verification_status == "MEMORY_RECALLED"
    assert result.memory_ids == ("m1",)
    assert result.provider == "persistent_memory:project_codename"
    storage.close()
