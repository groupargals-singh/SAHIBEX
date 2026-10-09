from core.research.standing_research_consent import StandingResearchConsent


def test_public_search_and_learning_use_narrow_standing_consent():
    consent = StandingResearchConsent()
    assert consent.allows(intent="search", action="research", request="Search the internet for AI security research")
    assert consent.allows(intent="learn", action="respond", request="Learn about photosynthesis with evidence")


def test_consent_does_not_apply_to_protected_or_arbitrary_network_actions():
    consent = StandingResearchConsent()
    assert not consent.allows(intent="search", action="network_access", request="Search for AI security")
    assert not consent.allows(intent="code", action="research", request="Search for AI security")
    assert not consent.allows(intent="search", action="research", request="Download this file")
    assert not consent.allows(intent="search", action="research", request="Fetch https://example.com/private")
    assert not consent.allows(intent="learn", action="research", request="Upload my files to a website")
    assert not consent.allows(intent="search", action="research", request="Use my API key to search")
