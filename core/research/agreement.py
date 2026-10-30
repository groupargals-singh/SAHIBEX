
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlsplit

from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)


AGREEMENT_VERSION = "6G-5"

AGGREGATOR_HOSTS = {
    "news.google.com",
    "news.yahoo.com",
    "consent.yahoo.com",
    "www.msn.com",
    "msn.com",
    "flipboard.com",
}


@dataclass(frozen=True)
class MultiSourceAgreementAssessment:
    """
    Measures agreement across identifiable source groups.

    Agreement is only a source-independence signal. It does NOT
    establish truth, reliability, evidence strength, or verification.
    """

    knowledge_id: str
    total_source_count: int
    supporting_source_count: int
    contradicting_source_count: int
    agreement_score: float
    version: str = AGREEMENT_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.agreement_score <= 1.0:
            raise ValueError(
                "agreement score must be between 0 and 1"
            )

        if self.total_source_count < 0:
            raise ValueError(
                "total_source_count cannot be negative"
            )

        if self.supporting_source_count < 0:
            raise ValueError(
                "supporting_source_count cannot be negative"
            )

        if self.contradicting_source_count < 0:
            raise ValueError(
                "contradicting_source_count cannot be negative"
            )


def _linked_evidence(
    knowledge: KnowledgeCandidate,
    evidence_items: Iterable[Evidence],
) -> list[Evidence]:
    """Return evidence explicitly linked to the candidate."""

    linked: list[Evidence] = []

    for evidence in evidence_items:
        metadata = evidence.metadata or {}

        if metadata.get("knowledge_id") != knowledge.knowledge_id:
            continue

        linked.append(evidence)

    return linked


def _normalise_publisher(source: ResearchSource) -> str:
    """Return a normalized publisher label, if available."""

    publisher = getattr(source, "publisher", None)

    if not isinstance(publisher, str):
        return ""

    return " ".join(publisher.casefold().split())


def _hostname_from_url(locator: object) -> str:
    """Return a canonical public HTTP(S) hostname, or empty for unsafe input."""

    if not isinstance(locator, str) or not locator.strip():
        return ""

    try:
        parsed = urlsplit(locator.strip())
        if parsed.scheme.casefold() not in {"http", "https"}:
            return ""
        if not parsed.netloc or parsed.username is not None or parsed.password is not None:
            return ""
        # Accessing .port validates malformed port values.
        _ = parsed.port
        hostname = (parsed.hostname or "").rstrip(".").casefold()
        if not hostname:
            return ""
        hostname = hostname.encode("idna").decode("ascii")
    except (UnicodeError, TypeError, ValueError):
        return ""

    if hostname == "localhost" or "." not in hostname:
        return ""

    return hostname.removeprefix("www.")


def _is_aggregator_hostname(hostname: str) -> bool:
    """Match aggregator domains and their subdomains, not just exact hosts."""

    return any(
        hostname == aggregator or hostname.endswith("." + aggregator)
        for aggregator in AGGREGATOR_HOSTS
    )


def _normalise_hostname(source: ResearchSource) -> str:
    """
    Resolve the article host, never treating a search/news aggregator as
    the original publisher unless an explicit original publisher URL exists.
    """

    locator = getattr(source, "locator", "")
    hostname = _hostname_from_url(locator)
    if not hostname:
        return ""

    if not _is_aggregator_hostname(hostname):
        return hostname

    metadata = getattr(source, "metadata", None)
    if not isinstance(metadata, dict):
        return ""

    # These fields must identify the original article, not the feed/search page.
    original_url = (
        metadata.get("original_publisher_url")
        or metadata.get("canonical_article_url")
    )
    original_hostname = _hostname_from_url(original_url)
    if not original_hostname or _is_aggregator_hostname(original_hostname):
        return ""

    return original_hostname


def _source_groups(
    sources: Iterable[ResearchSource],
) -> dict[str, str]:
    """
    Group source IDs that share a publisher or ordinary hostname.

    A source is eligible only if it has an identifiable publisher
    or an identifiable non-aggregator hostname.

    Aggregator hostnames alone are not treated as publishers.
    This function groups provenance; it does not prove that two
    publishers independently reported the underlying facts.
    """

    parent: dict[str, str] = {}
    identity_owners: dict[str, str] = {}

    def find(source_id: str) -> str:
        parent.setdefault(source_id, source_id)

        while parent[source_id] != source_id:
            parent[source_id] = parent[parent[source_id]]
            source_id = parent[source_id]

        return source_id

    def union(first: str, second: str) -> None:
        root_first = find(first)
        root_second = find(second)

        if root_first != root_second:
            # Deterministic root selection.
            if root_first < root_second:
                parent[root_second] = root_first
            else:
                parent[root_first] = root_second

    for source in sources:
        if not isinstance(source, ResearchSource):
            continue

        source_id = source.source_id.strip()

        if not source_id:
            continue

        publisher = _normalise_publisher(source)
        hostname = _normalise_hostname(source)

        # A publisher label alone is untrusted metadata: without a valid
        # article hostname it must not create an eligible independent source.
        # Aggregator links are eligible only when an explicit original article
        # URL was supplied and validated by _normalise_hostname.
        if not hostname:
            continue

        identity_keys: list[str] = [f"domain:{hostname}"]

        if publisher:
            identity_keys.append(f"publisher:{publisher}")

        find(source_id)

        for identity_key in identity_keys:
            previous_source_id = identity_owners.get(identity_key)

            if previous_source_id is None:
                identity_owners[identity_key] = source_id
            else:
                union(source_id, previous_source_id)

    return {
        source_id: find(source_id)
        for source_id in parent
    }


def _agreement_score(
    supporting_source_count: int,
    total_source_count: int,
) -> float:
    """
    Calculate source agreement.

    One source cannot establish multi-source agreement.

    Examples:
        0 sources -> 0.0
        1 source  -> 0.0
        2 of 2    -> 1.0
        2 of 3    -> 0.5
        3 of 3    -> 1.0
    """

    if total_source_count < 2:
        return 0.0

    score = (
        (supporting_source_count - 1)
        / (total_source_count - 1)
    )

    return max(0.0, min(1.0, score))


def assess_multi_source_agreement(
    *,
    knowledge: KnowledgeCandidate,
    evidence_items: Iterable[Evidence],
    sources: Iterable[ResearchSource] = (),
) -> MultiSourceAgreementAssessment:
    """
    Assess agreement for one knowledge candidate.

    Evidence must explicitly reference the candidate through
    metadata["knowledge_id"] and a source present in `sources`.

    Only identifiable publisher/domain groups count toward
    independent-source agreement. Source reliability and quality
    are intentionally not used in this calculation.
    """

    if not isinstance(knowledge, KnowledgeCandidate):
        raise TypeError(
            "knowledge must be a KnowledgeCandidate"
        )

    evidence_list = _linked_evidence(
        knowledge,
        evidence_items,
    )

    source_list = list(sources)
    source_groups = _source_groups(source_list)

    # Unknown, unregistered, or unidentifiable sources do not
    # count as independent corroboration.
    filtered_evidence = [
        evidence
        for evidence in evidence_list
        if (
            isinstance(evidence.source_id, str)
            and evidence.source_id in source_groups
        )
    ]

    all_source_groups = {
        source_groups[evidence.source_id]
        for evidence in filtered_evidence
    }

    supporting_source_groups = {
        source_groups[evidence.source_id]
        for evidence in filtered_evidence
        if evidence.supports
    }

    contradicting_source_groups = {
        source_groups[evidence.source_id]
        for evidence in filtered_evidence
        if not evidence.supports
    }

    total_source_count = len(all_source_groups)
    supporting_source_count = len(supporting_source_groups)
    contradicting_source_count = len(
        contradicting_source_groups
    )

    agreement_score = _agreement_score(
        supporting_source_count,
        total_source_count,
    )

    return MultiSourceAgreementAssessment(
        knowledge_id=knowledge.knowledge_id,
        total_source_count=total_source_count,
        supporting_source_count=supporting_source_count,
        contradicting_source_count=contradicting_source_count,
        agreement_score=round(agreement_score, 4),
    )
