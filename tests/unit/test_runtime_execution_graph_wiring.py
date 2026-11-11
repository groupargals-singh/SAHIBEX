from pathlib import Path

from app.main import build_runtime_components
from core.brain.master_brain import MasterBrain
from core.brain.mother_operational_integration import MotherOperationalIntegration
from core.brain.mother_research_integration import MotherResearchIntegration
from core.research.knowledge_registry import Concept
from core.research.persistent_memory_knowledge_graph import PersistentMemoryKnowledgeGraph
from core.research.storage import ResearchStorage


def _brain(database_path: Path, project_root: Path) -> MasterBrain:
    storage = ResearchStorage(database_path)
    operational = MotherOperationalIntegration(storage=storage)
    research = MotherResearchIntegration(storage=storage)
    return MasterBrain(
        mother_operational=operational,
        mother_research=research,
        tool_project_root=project_root,
    )


def test_cli_runtime_factory_wires_execution_loop_and_graph_to_shared_database(tmp_path):
    database_path = tmp_path / "runtime" / "sahibex.db"
    brain = _brain(database_path, tmp_path)

    active_brain, execution_loop, graph = build_runtime_components(
        project_root=tmp_path,
        brain=brain,
    )
    try:
        assert active_brain is brain
        assert execution_loop.brain is brain
        assert Path(graph._knowledge_storage.database_path).resolve() == database_path.resolve()
        assert Path(graph._association_storage.database_path).resolve() == database_path.resolve()
        assert Path(brain.mother_operational.storage.database_path).resolve() == database_path.resolve()
        assert Path(brain.mother_research.storage.database_path).resolve() == database_path.resolve()
        summary = graph.summary()
        assert summary["persistent"] is True
        assert summary["shared_sqlite_database"] is True
        assert summary["knowledge_graph_connected"] is True
        assert summary["grants_permission"] is False
        assert summary["executes_actions"] is False
    finally:
        graph.close()
        brain.mother_operational.storage.close()


def test_cli_runtime_execution_uses_loop_and_does_not_duplicate_read_turn(tmp_path, monkeypatch):
    database_path = tmp_path / "runtime" / "sahibex.db"
    target = tmp_path / "sample.txt"
    target.write_text("runtime execution loop accepted", encoding="utf-8")
    brain = _brain(database_path, tmp_path)

    active_brain, execution_loop, graph = build_runtime_components(
        project_root=tmp_path,
        brain=brain,
    )
    execute_calls = []
    original_execute = brain.tool_brain.execute

    def counted_execute(*args, **kwargs):
        execute_calls.append(1)
        return original_execute(*args, **kwargs)

    monkeypatch.setattr(brain.tool_brain, "execute", counted_execute)
    try:
        result = execution_loop.process("Read file sample.txt")
        assert result.success is True
        assert result.status == "COMPLETED"
        assert result.metadata["execution_kind"] == "read_only_tool"
        assert result.metadata["verified"] is True
        assert result.metadata["audit_recorded"] is True
        assert execute_calls == [1]
        assert "sample.txt" in result.response
        assert "runtime execution loop accepted" in result.response
        turns = active_brain.context.recent(5)
        assert len(turns) == 1
        assert turns[0].user == "Read file sample.txt"
        assert turns[0].assistant == result.response
        assert active_brain.persistent_memory_knowledge_graph is graph

        second_result = execution_loop.process("Read file sample.txt")
        assert second_result.success is True
        recent_memories = brain.memory_brain.storage.list_recent_memories(
            memory_type="conversation", source="master_brain", limit=2
        )
        assert len(recent_memories) == 2
        links = graph.links_for_memory(recent_memories[0].memory_id)
        assert len(links) == 1
        assert links[0].target_id == recent_memories[1].memory_id
        assert second_result.brain.metadata["persistent_memory_graph_link"]["status"] == "LINKED"
        assert graph.association_count() == 1
    finally:
        graph.close()
        brain.mother_operational.storage.close()


def test_runtime_graph_associations_survive_reopen_on_mother_database(tmp_path):
    database_path = tmp_path / "runtime" / "sahibex.db"
    brain = _brain(database_path, tmp_path)
    _, _, graph = build_runtime_components(project_root=tmp_path, brain=brain)
    graph._knowledge_storage.save_concept(
        Concept(concept_id="runtime-concept", name="Runtime Graph", concept_type="runtime_test")
    )
    linked = graph.link(
        memory_id="runtime-memory-1",
        target_id="runtime-concept",
        target_type="concept",
        confidence=0.9,
    )
    assert linked.created is True
    assert linked.target_exists is True
    graph.close()
    brain.mother_operational.storage.close()

    reopened = PersistentMemoryKnowledgeGraph(str(database_path))
    try:
        assert reopened.memories_for_target("runtime-concept", "concept") == (
            "runtime-memory-1",
        )
        assert reopened.summary()["association_count"] == 1
    finally:
        reopened.close()


def test_runtime_factory_rejects_in_memory_database_for_persistent_graph():
    storage = ResearchStorage(":memory:")
    operational = MotherOperationalIntegration(storage=storage)
    research = MotherResearchIntegration(storage=storage)
    brain = MasterBrain(mother_operational=operational, mother_research=research)
    try:
        try:
            build_runtime_components(brain=brain)
        except RuntimeError as exc:
            assert "file-backed" in str(exc)
        else:
            raise AssertionError("in-memory database must not masquerade as persistent graph")
    finally:
        storage.close()


def test_memory_graph_checks_real_memory_targets_in_shared_store(tmp_path):
    database_path = tmp_path / "runtime" / "sahibex.db"
    brain = _brain(database_path, tmp_path)
    _, _, graph = build_runtime_components(project_root=tmp_path, brain=brain)
    try:
        saved = brain.memory_brain.remember(
            content="Persisted conversation memory node",
            memory_type="conversation",
            source="master_brain",
        )
        assert saved.persisted is True
        existing = graph.link(
            memory_id="new-memory-node",
            target_id=saved.memory_id,
            target_type="memory",
        )
        missing = graph.link(
            memory_id="new-memory-node",
            target_id="missing-memory-node",
            target_type="memory",
        )
        assert existing.target_exists is True
        assert missing.target_exists is False
    finally:
        graph.close()
        brain.mother_operational.storage.close()


def test_runtime_graph_resumes_conversation_linking_after_restart(tmp_path):
    database_path = tmp_path / "runtime" / "sahibex.db"
    first_brain = _brain(database_path, tmp_path)
    _, first_loop, first_graph = build_runtime_components(
        project_root=tmp_path, brain=first_brain
    )
    first_result = first_loop.process("Namaste")
    assert first_result.success is True
    first_memories = first_brain.memory_brain.storage.list_recent_memories(
        memory_type="conversation", source="master_brain", limit=1
    )
    assert len(first_memories) == 1
    first_memory_id = first_memories[0].memory_id
    first_graph.close()
    first_brain.mother_operational.storage.close()

    second_brain = _brain(database_path, tmp_path)
    _, second_loop, second_graph = build_runtime_components(
        project_root=tmp_path, brain=second_brain
    )
    try:
        second_result = second_loop.process("Namaste")
        assert second_result.success is True
        recent = second_brain.memory_brain.storage.list_recent_memories(
            memory_type="conversation", source="master_brain", limit=2
        )
        assert len(recent) == 2
        links = second_graph.links_for_memory(recent[0].memory_id)
        assert len(links) == 1
        assert links[0].target_id == first_memory_id
        assert second_result.brain.metadata["persistent_memory_graph_link"]["status"] == "LINKED"
    finally:
        second_graph.close()
        second_brain.mother_operational.storage.close()
