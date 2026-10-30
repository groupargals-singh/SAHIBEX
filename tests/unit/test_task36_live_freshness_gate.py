from datetime import datetime, timedelta, timezone

from core.research.freshness import STATUS_FRESH, STATUS_AGING, STATUS_INVALID, STATUS_UNKNOWN
from core.research.models import ResearchSource
from scripts.task36_live_research_acceptance import assess_acceptance_freshness


UTC = timezone.utc
REFERENCE = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)


def _source(source_id, published_at):
    return ResearchSource(
        source_id=source_id,
        title=f"Source {source_id}",
        source_type="web",
        locator=f"https://{source_id}.example/news",
        publisher=f"Publisher {source_id}",
        published_at=published_at,
        accessed_at=REFERENCE,
        reliability=0.8,
    )


def test_current_news_acceptance_passes_only_fresh_dated_sources():
    sources = [
        _source("fresh-one", REFERENCE - timedelta(days=1)),
        _source("fresh-two", REFERENCE - timedelta(days=6)),
    ]
    assessments, checks = assess_acceptance_freshness(
        sources,
        requires_publication_dates=True,
        reference_time=REFERENCE,
    )
    assert [item["status"] for item in assessments] == [STATUS_FRESH, STATUS_FRESH]
    assert checks == {
        "source_freshness_assessed": True,
        "current_query_sources_fresh": True,
    }


def test_current_news_acceptance_rejects_aging_source():
    assessments, checks = assess_acceptance_freshness(
        [_source("aging", REFERENCE - timedelta(days=10))],
        requires_publication_dates=True,
        reference_time=REFERENCE,
    )
    assert assessments[0]["status"] == STATUS_AGING
    assert checks["source_freshness_assessed"] is True
    assert checks["current_query_sources_fresh"] is False


def test_current_news_acceptance_rejects_unknown_publication_date():
    assessments, checks = assess_acceptance_freshness(
        [_source("unknown", None)],
        requires_publication_dates=True,
        reference_time=REFERENCE,
    )
    assert assessments[0]["status"] == STATUS_UNKNOWN
    assert checks["current_query_sources_fresh"] is False


def test_current_news_acceptance_rejects_future_publication():
    assessments, checks = assess_acceptance_freshness(
        [_source("future", REFERENCE + timedelta(hours=1))],
        requires_publication_dates=True,
        reference_time=REFERENCE,
    )
    assert assessments[0]["status"] == STATUS_INVALID
    assert checks["current_query_sources_fresh"] is False


def test_stable_fact_can_use_old_source_but_still_records_freshness():
    assessments, checks = assess_acceptance_freshness(
        [_source("stable-old", REFERENCE - timedelta(days=365))],
        requires_publication_dates=False,
        reference_time=REFERENCE,
    )
    assert assessments[0]["status"] != STATUS_FRESH
    assert checks["source_freshness_assessed"] is True
    assert checks["current_query_sources_fresh"] is True


def test_empty_source_set_fails_closed_for_current_news():
    assessments, checks = assess_acceptance_freshness(
        [],
        requires_publication_dates=True,
        reference_time=REFERENCE,
    )
    assert assessments == []
    assert checks["source_freshness_assessed"] is False
    assert checks["current_query_sources_fresh"] is False

def test_today_query_rejects_multi_day_source_even_if_generic_status_is_fresh():
    assessments, checks = assess_acceptance_freshness(
        [_source("several-days-old", REFERENCE - timedelta(days=2))],
        requires_publication_dates=True,
        max_age_seconds=24 * 60 * 60,
        reference_time=REFERENCE,
    )
    assert assessments[0]["status"] == STATUS_FRESH
    assert assessments[0]["age_seconds"] > 24 * 60 * 60
    assert checks["current_query_sources_fresh"] is False
