from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.master_brain import MasterBrain
from core.brain.mother_operational_integration import MotherOperationalIntegration
from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


def _seed_verified(storage, knowledge_id: str, statement: str) -> None:
    storage.save_knowledge(
        KnowledgeCandidate(
            knowledge_id=knowledge_id,
            statement=statement,
            findings=[statement],
            evidence=[f"reviewed source record for {knowledge_id}"],
            confidence=0.95,
            verified=True,
            last_verified_at=datetime.now(timezone.utc),
            metadata={"source": "test-reviewed-source"},
        )
    )
    storage.record_knowledge_verification(
        knowledge_id=knowledge_id,
        status="VERIFIED",
        reason="Fixed acceptance fixture with explicit evidence.",
        verified_at=datetime.now(timezone.utc),
    )


def _brain(storage):
    integration = MotherOperationalIntegration(storage=storage)
    return MasterBrain(mother_operational=integration)


def test_real_main_brain_hindi_factual_question_discloses_insufficient_evidence():
    with TemporaryDirectory() as temp:
        storage = ResearchStorage(Path(temp) / "main.db")
        brain = _brain(storage)
        result = brain.process("पौधों को सूर्य के प्रकाश की आवश्यकता क्यों होती है?")
        assert result.success is True
        assert result.verification_status == "INSUFFICIENT_EVIDENCE"
        assert "पर्याप्त सत्यापित प्रमाण" in result.message
        operational = result.metadata["mother_operational_integration"]
        assert operational["factual_verification"] is False
        assert operational["diagnostics"]["uncertainty_disclosed"] is True


def test_real_main_brain_english_factual_answer_uses_verified_knowledge():
    with TemporaryDirectory() as temp:
        storage = ResearchStorage(Path(temp) / "main.db")
        statement = "Plants use sunlight to power photosynthesis and make sugars."
        _seed_verified(storage, "plants-sunlight-verified", statement)
        brain = _brain(storage)
        result = brain.process("Why do plants need sunlight?")
        assert result.success is True
        assert result.verification_status == "VERIFIED_KNOWLEDGE"
        assert result.message == statement
        operational = result.metadata["mother_operational_integration"]
        assert operational["factual_verification"] is True
        assert operational["diagnostics"]["evidence_backed"] is True
        assert "plants-sunlight-verified" in operational["knowledge_ids"]


def test_real_main_brain_conflicting_knowledge_discloses_conflict():
    with TemporaryDirectory() as temp:
        storage = ResearchStorage(Path(temp) / "main.db")
        _seed_verified(storage, "plants-sunlight-yes", "Plants use sunlight to power photosynthesis and make sugars.")
        _seed_verified(storage, "plants-sunlight-no", "Plants do not need sunlight for photosynthesis.")
        brain = _brain(storage)
        result = brain.process("Why do plants need sunlight?")
        assert result.success is True
        assert result.verification_status == "CONFLICTING_EVIDENCE"
        assert "evidence conflicts" in result.message.lower()
        operational = result.metadata["mother_operational_integration"]
        assert operational["factual_verification"] is False
        assert operational["diagnostics"]["uncertainty_disclosed"] is True


def test_real_main_brain_surfaces_rejected_answer_reason():
    with TemporaryDirectory() as temp:
        storage = ResearchStorage(Path(temp) / "main.db")
        brain = _brain(storage)
        result = brain.process("SAHIBEX")
        assert result.success is False
        assert result.verification_status == "QUALITY_REJECTED"
        operational = result.metadata["mother_operational_integration"]
        assert operational["quality_reasons"]
        assert operational["diagnostics"]["failure_stage"] == "answer_quality"


def test_real_main_brain_hindi_factual_answer_uses_verified_knowledge():
    with TemporaryDirectory() as temp:
        storage = ResearchStorage(Path(temp) / "main.db")
        statement = "पौधे प्रकाश संश्लेषण के लिए सूर्य के प्रकाश का उपयोग करते हैं।"
        _seed_verified(storage, "paudhe-surya-prakash-verified", statement)
        brain = _brain(storage)
        result = brain.process("पौधों को सूर्य के प्रकाश की आवश्यकता क्यों होती है?")
        assert result.success is True
        assert result.verification_status == "VERIFIED_KNOWLEDGE"
        assert "प्रकाश संश्लेषण" in result.message
        operational = result.metadata["mother_operational_integration"]
        assert operational["factual_verification"] is True
        assert operational["diagnostics"]["evidence_backed"] is True
