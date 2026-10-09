from core.brain.master_brain import MasterBrain
from core.brain.factual_resolver import resolve_local_fact


def test_monsoon_fact_is_exact_and_curated():
    fact = resolve_local_fact("भारत में मानसून कैसे आता है?")
    assert fact is not None
    assert fact.fact_id == "CLIMATE-INDIAN-MONSOON-001"
    assert "अरब सागर" in fact.answer


def test_master_brain_uses_monsoon_fastpath_without_local_model():
    result = MasterBrain().process("भारत में मानसून कैसे आता है?")
    assert result.success
    assert result.metadata["response_source"] == "curated_local_knowledge"
    assert "नमी वाली हवाएँ" in result.message
