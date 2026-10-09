from core.brain.mother_operational_integration import MotherOperationalIntegration


def test_cognitive_context_is_bounded_for_small_local_models():
    value = "x" * 10000
    bounded = MotherOperationalIntegration._bounded_context(value, 3500)

    assert len(bounded) <= 3500 + len("\n[CONTEXT_TRUNCATED]")
    assert bounded.endswith("[CONTEXT_TRUNCATED]")


def test_cognitive_context_is_not_changed_when_within_bound():
    value = "useful memory"
    assert MotherOperationalIntegration._bounded_context(value, 3500) == value


def test_phone_local_model_prompt_context_budgets_stay_small():
    assert MotherOperationalIntegration.MAX_MEMORY_CONTEXT_CHARS <= 1000
    assert MotherOperationalIntegration.MAX_KNOWLEDGE_CONTEXT_CHARS <= 500
