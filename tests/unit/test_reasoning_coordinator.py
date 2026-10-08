from core.brain.reasoning_coordinator import ReasoningAssessment, ReasoningCoordinator


def test_reasoning_coordinator_covers_phase_two_capabilities() -> None:
    engine = ReasoningCoordinator()
    result = engine.assess(
        goal="Determine the safest next step.",
        intent="decision",
        confidence=0.9,
        quality_score=0.95,
        assumptions=["Input is current."],
        evidence=[True, True, True],
        constraints=[True, True],
        prior_context={"previous_goal": "inspect"},
    )

    assert isinstance(result, ReasoningAssessment)
    assert result.selected_strategy == "constraint"
    assert "understand_goal" in result.steps
    assert "select_reasoning_strategy" in result.steps
    assert "assess_uncertainty" in result.steps
    assert "verify_conclusion" in result.steps
    assert result.assumptions == ("Input is current.",)
    assert result.confidence >= 0.5
    assert result.uncertainty < 0.6
    assert result.verified is True
    assert result.corrected is False
    assert result.reusable_context["previous_goal"] == "inspect"


def test_reasoning_coordinator_detects_uncertainty_and_corrects() -> None:
    engine = ReasoningCoordinator()
    result = engine.assess(
        goal="Resolve an ambiguous request.",
        confidence=0.2,
        quality_score=0.2,
        conflict_score=0.8,
        missing_information=True,
        ambiguous=True,
        evidence=[True, False],
        constraints=[True, False],
    )

    assert result.needs_verification is True
    assert result.corrected is True
    assert result.correction_count == 1
    assert result.conflicts
    assert result.verified is False
    assert result.confidence < 0.5


def test_reasoning_coordinator_resume_and_reverify() -> None:
    engine = ReasoningCoordinator()
    result = engine.assess(
        goal="Resume this reasoning task.",
        confidence=0.8,
        quality_score=0.9,
    )
    resumed = engine.resume(result.reasoning_id)
    assert resumed.reasoning_id == result.reasoning_id

    verified = engine.verify(resumed)
    assert verified.reasoning_id == result.reasoning_id


def test_reasoning_capability_security_contract() -> None:
    contract = ReasoningCoordinator.capability_contract()
    for key in (
        "understand",
        "decompose",
        "strategy_selection",
        "assumption_tracking",
        "uncertainty",
        "evidence_check",
        "constraint_check",
        "conflict_detection",
        "verification",
        "correction",
        "long_running_resume",
        "context_reuse",
    ):
        assert contract[key] is True

    assert contract["protected_execution"] is False
    assert contract["permission_grant"] is False
    assert contract["constitution_override"] is False


def test_operational_reasoning_uses_structured_reasoning() -> None:
    from core.brain.operational_model import OperationalModelIntegration
    from core.brain.operational_reasoning import OperationalReasoningEngine
    from core.model_gateway.base import ModelGateway
    from core.model_gateway.mock_provider import MockModelProvider

    gateway = ModelGateway()
    gateway.register_provider(MockModelProvider())
    engine = OperationalReasoningEngine(
        model_integration=OperationalModelIntegration(gateway)
    )

    result = engine.process(
        user_input="Explain how Python works.",
        provider="mock",
    )

    assert result.success is True
    assert result.model_response.startswith("MOCK MODEL RESPONSE:")
    assert result.verification_status == "VERIFIED"
    assert "Structured reasoning control signals" in result.model_response
