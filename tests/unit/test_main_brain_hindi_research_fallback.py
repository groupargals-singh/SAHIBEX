from __future__ import annotations

from pathlib import Path
import tempfile
from types import SimpleNamespace

from core.brain.master_brain import MasterBrain
from core.brain.mother_operational_integration import MotherOperationalIntegration
from core.brain.mother_research_integration import MotherResearchIntegration, MotherResearchResult
from core.research.storage import ResearchStorage


def test_main_brain_preserves_localized_unverified_research_fallback(monkeypatch):
    with tempfile.TemporaryDirectory(prefix="sahibex_hindi_research_") as directory:
        storage = ResearchStorage(Path(directory) / "hindi.db")
        research = MotherResearchIntegration(storage=storage)
        brain = MasterBrain(
            mother_operational=MotherOperationalIntegration(storage=storage),
            mother_research=research,
        )
        localized = "इस सवाल का भरोसेमंद जवाब देने के लिए पर्याप्त प्रमाण सत्यापित नहीं हो सके।"
        blocked = MotherResearchResult(
            success=False,
            query="आज AI सुरक्षा में क्या नया है?",
            status="insufficient_evidence",
            answer=localized,
            job_id="hindi-fallback-job",
            execution_id="hindi-fallback-execution",
            verification_status="NOT_VERIFIED",
            diagnostics={
                "language_consistency": {"matches_query": True, "status": "MATCH"},
                "answer": {"verified": False, "claim_count": 0},
            },
        )
        monkeypatch.setattr(
            brain.research_learning_brain,
            "research_topic",
            lambda query, confirmation=False: SimpleNamespace(
                success=False,
                operation="research",
                verified=False,
                persisted=False,
                result=blocked,
                error="",
            ),
        )
        try:
            result = brain.process("आज AI सुरक्षा में क्या नया है?")
            assert result.success is False
            assert result.verification_status == "NOT_VERIFIED"
            assert "पर्याप्त प्रमाण" in result.message
            assert "couldn't verify this research answer" not in result.message.casefold()
            assert result.metadata["mother_research_integration"]["verification_status"] == "NOT_VERIFIED"
        finally:
            storage.close()
