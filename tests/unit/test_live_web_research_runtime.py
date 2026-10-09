from core.brain.master_brain import MasterBrain


def test_live_web_research_fails_closed_without_search_credentials(monkeypatch):
    monkeypatch.delenv("SAHIBEX_SEARCH_BACKEND", raising=False)
    brain = MasterBrain()

    assert "search" not in brain.mother_research.research_provider_status.providers

    blocked = brain.process("Search the internet for AI security.")

    assert blocked.success is False
    assert blocked.permission_allowed is True
    assert blocked.confirmation_required is False
    assert blocked.verification_status in {"UNKNOWN", "NOT_EXECUTED"}
    assert blocked.message


def test_live_web_research_after_confirmation_is_controlled_without_provider(monkeypatch):
    monkeypatch.delenv("SAHIBEX_SEARCH_BACKEND", raising=False)
    brain = MasterBrain()

    allowed = brain.process(
        "Search the internet for AI security.",
        user_confirmation=True,
    )

    assert allowed.success is False
    assert allowed.verification_status in {"UNKNOWN", "NOT_EXECUTED"}
    assert allowed.message
