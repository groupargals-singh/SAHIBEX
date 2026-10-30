from datetime import datetime, timezone

from core.research.models import ResearchSource
from core.research.source_reliability_assessment import assess_source_reliability


def source(locator, reliability=0.5, metadata=None):
    return ResearchSource(
        source_id="source-test",
        title="Test source",
        source_type="web",
        locator=locator,
        publisher="Test Publisher",
        published_at=datetime(2026, 10, 16, tzinfo=timezone.utc),
        reliability=reliability,
        metadata=metadata or {},
    )


def test_official_domain_prior_is_explainable_and_bounded():
    result = assess_source_reliability(source("https://www.cisa.gov/news", 0.5))
    assert result.host == "cisa.gov"
    assert result.domain_class == "official_or_intergovernmental"
    assert result.domain_prior == 0.86
    assert 0.0 <= result.assessed_reliability <= 1.0
    assert "declared_score_blended_with_domain_prior" in result.flags


def test_known_publisher_ranks_above_unknown_host_with_same_declared_score():
    known = assess_source_reliability(source("https://www.reuters.com/world/story", 0.5))
    unknown = assess_source_reliability(source("https://unknown-example.invalid/story", 0.5))
    assert known.domain_class == "recognized_publisher"
    assert known.assessed_reliability > unknown.assessed_reliability


def test_aggregator_wrapper_and_discovery_only_are_capped():
    wrapper = assess_source_reliability(source(
        "https://news.google.com/rss/articles/example", 0.9,
        {"is_aggregator_wrapper": True, "discovery_only": True},
    ))
    assert wrapper.assessed_reliability <= 0.25
    assert "discovery_only_capped" in wrapper.flags
    assert "aggregator_wrapper_capped" in wrapper.flags


def test_unverified_publisher_identity_is_capped():
    result = assess_source_reliability(source(
        "https://reuters.com.example.invalid/story", 0.95,
        {"publisher_identity_verified": False},
    ))
    assert result.domain_class == "unclassified_domain"
    assert result.assessed_reliability <= 0.30


def test_explicit_human_review_score_is_preserved():
    result = assess_source_reliability(source(
        "https://www.reuters.com/world/story", 0.63,
        {"reliability_method": "human_review"},
    ))
    assert result.assessed_reliability == 0.63
    assert "explicit_human_review_preserved" in result.flags


def test_missing_or_invalid_locator_gets_conservative_prior():
    result = assess_source_reliability(source("not a valid URL", 0.5))
    assert result.host == ""
    assert result.domain_class == "missing_host"
    assert "missing_or_invalid_host" in result.flags
