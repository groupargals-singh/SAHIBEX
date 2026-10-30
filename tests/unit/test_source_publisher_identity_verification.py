from datetime import datetime, timezone

from core.research.agreement import assess_multi_source_agreement
from core.research.models import Evidence, KnowledgeCandidate, ResearchSource


def _knowledge() -> KnowledgeCandidate:
    now = datetime.now(timezone.utc)
    return KnowledgeCandidate(
        knowledge_id="claim-1",
        statement="A supported test claim.",
        findings=["finding-1"],
        evidence=[],
        confidence=0.8,
        verified=True,
        created_at=now,
        last_verified_at=now,
        metadata={},
    )


def _source(
    source_id: str,
    locator: str,
    *,
    publisher: str | None = None,
    metadata: dict | None = None,
) -> ResearchSource:
    return ResearchSource(
        source_id=source_id,
        title=f"Story {source_id}",
        source_type="web",
        locator=locator,
        publisher=publisher,
        reliability=0.8,
        metadata=metadata or {},
    )


def _evidence(source_id: str, *, supports: bool = True) -> Evidence:
    return Evidence(
        evidence_id=f"evidence-{source_id}",
        finding_id="finding-1",
        source_id=source_id,
        evidence_text="A supported test claim.",
        supports=supports,
        strength=0.8,
        metadata={"knowledge_id": "claim-1"},
    )


def _assess(sources: list[ResearchSource]):
    return assess_multi_source_agreement(
        knowledge=_knowledge(),
        evidence_items=[_evidence(item.source_id) for item in sources],
        sources=sources,
    )


def test_aggregator_link_does_not_count_even_with_publisher_label():
    source = _source(
        "google-result",
        "https://news.google.com/rss/articles/abc",
        publisher="Independent Publisher",
    )
    result = _assess([source])
    assert result.total_source_count == 0
    assert result.supporting_source_count == 0
    assert result.agreement_score == 0.0


def test_aggregator_subdomain_is_not_mistaken_for_publisher():
    source = _source(
        "google-subdomain",
        "https://edition.news.google.com/articles/abc",
        publisher="Publisher Name",
    )
    result = _assess([source])
    assert result.total_source_count == 0


def test_aggregator_can_use_explicit_validated_original_article_url():
    source = _source(
        "google-result-with-original",
        "https://news.google.com/rss/articles/abc",
        publisher="Independent Publisher",
        metadata={"original_publisher_url": "https://publisher.example.org/story"},
    )
    result = _assess([source])
    assert result.total_source_count == 1
    assert result.supporting_source_count == 1
    assert result.agreement_score == 0.0


def test_publisher_label_cannot_rescue_malformed_locator():
    source = _source(
        "bad-url",
        "not-a-valid-url",
        publisher="Publisher Name",
    )
    result = _assess([source])
    assert result.total_source_count == 0


def test_credentials_in_source_url_are_rejected_for_identity():
    source = _source(
        "credential-url",
        "https://user:secret@example.org/story",
        publisher="Publisher Name",
    )
    result = _assess([source])
    assert result.total_source_count == 0


def test_same_publisher_across_different_domains_counts_once():
    sources = [
        _source("publisher-a", "https://publisher-a.example.org/story", publisher="Same Publisher"),
        _source("publisher-b", "https://publisher-b.example.net/story", publisher="  SAME   PUBLISHER "),
    ]
    result = _assess(sources)
    assert result.total_source_count == 1
    assert result.supporting_source_count == 1
    assert result.agreement_score == 0.0


def test_same_domain_with_different_labels_counts_once():
    sources = [
        _source("domain-a", "https://www.example.org/story-a", publisher="Publisher One"),
        _source("domain-b", "https://example.org./story-b", publisher="Publisher Two"),
    ]
    result = _assess(sources)
    assert result.total_source_count == 1
    assert result.supporting_source_count == 1


def test_non_http_scheme_cannot_establish_source_identity():
    source = _source(
        "file-url",
        "file://publisher.example.org/article",
        publisher="Publisher Name",
    )
    result = _assess([source])
    assert result.total_source_count == 0


def test_two_distinct_valid_hosts_count_as_independent_sources():
    sources = [
        _source("source-a", "https://source-a.org/article", publisher="Publisher A"),
        _source("source-b", "https://source-b.net/article", publisher="Publisher B"),
    ]
    result = _assess(sources)
    assert result.total_source_count == 2
    assert result.supporting_source_count == 2
    assert result.agreement_score == 1.0
