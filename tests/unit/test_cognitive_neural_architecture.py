from core.brain.cognitive_neural_architecture import CognitiveNeuralArchitecture


def assess(request, intent="general_request", action="respond", risk="low", verification="VERIFIED", confirmation=False):
    return CognitiveNeuralArchitecture().assess(
        request=request,
        intent=intent,
        action=action,
        risk=risk,
        verification_status=verification,
        confirmation_required=confirmation,
    )


def test_simple_request_routes_to_direct_reasoning():
    result = assess("What is 2 plus 2?")
    assert result.route == "direct_reasoning"
    assert result.inhibition_required is False
    assert result.stages[0] == "perception"
    assert result.stages[-1] == "response_and_learning_signal"
    assert 0 <= result.complexity <= 1
    assert 0 <= result.attention <= 1


def test_research_routes_through_evidence_and_verification():
    result = assess("Research current evidence about solar energy", intent="research")
    assert result.route == "research_and_evidence"
    assert any("evidence" in item.lower() for item in result.rationale)


def test_protected_action_is_inhibited_without_granting_authority():
    result = assess("delete file", action="delete_file", risk="high")
    assert result.route == "protected_action_review"
    assert result.inhibition_required is True
    assert any("cannot grant" in item.lower() for item in result.rationale)


def test_confirmation_requirement_always_activates_inhibition():
    result = assess("Please do this", confirmation=True)
    assert result.inhibition_required is True
    assert result.route == "protected_action_review"


def test_unverified_outcome_is_explicitly_conservative():
    result = assess("Find answer", intent="research", verification="UNVERIFIED")
    assert any("not marked fully verified" in item.lower() for item in result.rationale)
    assert result.to_dict()["version"] == CognitiveNeuralArchitecture.VERSION


def test_invalid_inputs_are_rejected():
    try:
        assess("hello", intent="")
    except ValueError:
        pass
    else:
        raise AssertionError("empty intent must be rejected")


def test_master_brain_records_cognitive_trace_on_fast_path():
    from core.brain.master_brain import MasterBrain

    result = MasterBrain().process("hello")
    trace = result.metadata.get("cognitive_neural_architecture")
    assert trace is not None
    assert trace["version"] == CognitiveNeuralArchitecture.VERSION
    assert trace["route"] in {
        "direct_reasoning", "deliberative_reasoning",
        "research_and_evidence", "specialist_and_plan",
        "protected_action_review",
    }
    assert trace["authority_changed"] is False if "authority_changed" in trace else True


def test_hindi_and_hinglish_multistep_requests_route_deliberatively():
    hindi = assess("Pehle research karo, uske baad compare karke batao")
    devanagari = assess("पहले शोध करो, उसके बाद तुलना करके बताओ")
    assert hindi.route == "deliberative_reasoning"
    assert devanagari.route == "deliberative_reasoning"
    assert hindi.complexity > assess("Namaste").complexity
    assert devanagari.complexity > assess("नमस्ते").complexity


def test_bilingual_routing_remains_advisory_for_protected_actions():
    result = assess(
        "पहले योजना बनाओ, फिर delete file",
        action="delete_file",
        risk="critical",
    )
    assert result.route == "protected_action_review"
    assert result.inhibition_required is True
    assert any("cannot grant" in item.lower() for item in result.rationale)
