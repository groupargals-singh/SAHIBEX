from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.brain.master_brain import MasterBrain
from core.brain.mother_research_integration import MotherResearchIntegration
from core.research.storage import ResearchStorage


def test_custom_research_storage_is_wired_through_nested_operational_retrieval(tmp_path):
    research_storage = ResearchStorage(tmp_path / "research.sqlite3")
    research = MotherResearchIntegration(storage=research_storage)

    brain = MasterBrain(mother_research=research)

    assert brain.mother_research.storage is research_storage
    assert brain.mother_operational.storage is research_storage
    assert brain.mother_operational.memory_knowledge.storage is research_storage
    assert brain.mother_operational.memory_knowledge.memory_brain.storage is research_storage
    assert brain.mother_operational.memory_knowledge.knowledge_brain.storage is research_storage
    assert brain.memory_brain.storage is research_storage
    assert brain.knowledge_brain.storage is research_storage
    assert brain.research_learning_brain.research is brain.mother_research
    assert brain.research_learning_brain.learning.research is brain.mother_research


def test_main_brain_wires_every_declared_internal_role_to_a_handler():
    brain = MasterBrain()
    roles = {role.role_id: role.handler_registered for role in brain.internal_brain_team.roles()}

    assert set(roles) == set(brain.internal_brain_team.ROLE_PURPOSES)
    assert all(roles.values())


def test_safe_fast_path_keeps_cognitive_and_context_integration_available():
    brain = MasterBrain()
    result = brain.process("What is 2 + 2?")

    assert result.success is True
    assert result.message.strip() in {"4", "Answer: 4", "उत्तर: 4"}
    assert result.metadata["response_source"] == "safe_arithmetic_resolver"
    assert any("cannot grant" in item for item in result.metadata["cognitive_neural_architecture"]["rationale"])
    assert any("cannot grant permissions" in item for item in result.metadata["three_brain_council"]["limitations"])
    assert brain.context.history
