"""P1 live smoke through MasterBrain with the configured local provider."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["SAHIBEX_MODEL_PROVIDER"] = "local"

from core.brain.master_brain import MasterBrain
from core.brain.mother_operational_integration import MotherOperationalIntegration
from core.research.models import KnowledgeCandidate
from core.research.storage import ResearchStorage


def seed(storage: ResearchStorage, key: str, statement: str) -> None:
    storage.save_knowledge(
        KnowledgeCandidate(
            knowledge_id=key,
            statement=statement,
            findings=[statement],
            evidence=[f"reviewed evidence record for {key}"],
            confidence=0.95,
            verified=True,
            last_verified_at=datetime.now(timezone.utc),
            metadata={"source": "p1-live-smoke-reviewed-fixture"},
        )
    )
    storage.record_knowledge_verification(
        knowledge_id=key,
        status="VERIFIED",
        reason="P1 live smoke fixture includes explicit evidence and verification lifecycle.",
        verified_at=datetime.now(timezone.utc),
    )


with TemporaryDirectory(prefix="sahibex-p1-live-") as temp:
    storage = ResearchStorage(Path(temp) / "sahibex_p1.db")
    integration = MotherOperationalIntegration(storage=storage)
    assert integration.default_provider == "local", integration.default_provider
    brain = MasterBrain(mother_operational=integration)

    hindi_unknown = brain.process("पौधों को सूर्य के प्रकाश की आवश्यकता क्यों होती है?")
    assert hindi_unknown.verification_status == "INSUFFICIENT_EVIDENCE"
    assert "पर्याप्त सत्यापित प्रमाण" in hindi_unknown.message
    print("PASS real MainBrain Hindi insufficient-evidence: INSUFFICIENT_EVIDENCE")

    english_unknown = brain.process("Why do plants need sunlight?")
    assert english_unknown.verification_status == "INSUFFICIENT_EVIDENCE"
    assert "verified evidence" in english_unknown.message.lower()
    print("PASS real MainBrain English insufficient-evidence: INSUFFICIENT_EVIDENCE")

    english_claim = "Plants use sunlight to power photosynthesis and make sugars."
    seed(storage, "p1-live-plants-en", english_claim)
    english_grounded = brain.process("Why do plants need sunlight?")
    assert english_grounded.verification_status == "VERIFIED_KNOWLEDGE"
    assert english_grounded.message == english_claim
    assert english_grounded.metadata["mother_operational_integration"]["factual_verification"] is True
    print("PASS real MainBrain English evidence-grounded answer: VERIFIED_KNOWLEDGE")

    hindi_claim = "पौधे प्रकाश संश्लेषण के लिए सूर्य के प्रकाश का उपयोग करते हैं।"
    seed(storage, "p1-live-plants-hi", hindi_claim)
    hindi_grounded = brain.process("पौधों को सूर्य के प्रकाश की आवश्यकता क्यों होती है?")
    assert hindi_grounded.verification_status == "VERIFIED_KNOWLEDGE"
    assert "प्रकाश संश्लेषण" in hindi_grounded.message
    print("PASS real MainBrain Hindi evidence-grounded answer: VERIFIED_KNOWLEDGE")

    seed(storage, "p1-live-plants-en-conflict", "Plants do not need sunlight for photosynthesis.")
    conflict = brain.process("Why do plants need sunlight?")
    assert conflict.verification_status == "CONFLICTING_EVIDENCE"
    assert "evidence conflicts" in conflict.message.lower()
    print("PASS real MainBrain conflicting evidence: CONFLICTING_EVIDENCE")

    # Exercise the real configured local model on a non-factual creative request.
    creative = brain.process("Write a short two-line poem about rain.")
    assert creative.verification_status in {"STRUCTURALLY_VALID", "QUALITY_REJECTED", "INSUFFICIENT_EVIDENCE"}
    if creative.verification_status == "STRUCTURALLY_VALID":
        op = creative.metadata.get("mother_operational_integration", {})
        assert op.get("factual_verification") is False
    print(f"LOCAL MODEL CREATIVE SMOKE: {creative.verification_status}")
    print(f"LOCAL MODEL PROVIDER: {integration.default_provider}")
    print("P1 LIVE ANSWER RELIABILITY SMOKE: PASS")

    storage.close()
