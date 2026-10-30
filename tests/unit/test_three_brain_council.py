from core.brain.three_brain_council import ThreeBrainCouncil

def run(request="How can I improve this?", answer="Measure the current result, then test one improvement.", intent="general_request", risk="low", status="VERIFIED"):
    return ThreeBrainCouncil().deliberate(request=request, answer=answer, intent=intent, risk=risk, verification_status=status)

def test_three_distinct_perspectives_and_suggestions():
    result = run()
    assert [p.brain for p in result.perspectives] == ["brain_1_solver", "brain_2_challenger", "brain_3_strategist"]
    assert len(result.suggestions) >= 2
    assert result.mode == "parallel_advisory"

def test_research_without_verification_is_flagged():
    result = run("Find latest solar research", "Solar energy is useful.", "research", "low", "UNVERIFIED")
    assert result.consensus == "EVIDENCE_REQUIRED"
    assert any("primary sources" in p.recommendation for p in result.perspectives)

def test_protected_action_gets_safety_review():
    result = run("Transfer money to this account", "Done", "general_request", "high", "VERIFIED")
    assert result.consensus == "SAFETY_REVIEW_REQUIRED"
    assert any("explicit permission" in p.recommendation for p in result.perspectives)

def test_council_never_claims_truth_or_authority():
    result = run()
    assert any("cannot grant permissions" in item for item in result.limitations)
    assert any("does not prove factual truth" in item for item in result.limitations)

def test_empty_request_is_rejected():
    try: run(request=" ")
    except ValueError: pass
    else: raise AssertionError("empty request must be rejected")
