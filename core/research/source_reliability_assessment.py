from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse

SOURCE_RELIABILITY_ASSESSMENT_VERSION = "6G-9"
DECLARED_RELIABILITY_WEIGHT = 0.65
DOMAIN_PRIOR_WEIGHT = 0.35

# Conservative domain priors for ranking only; they do not prove truth.
_OFFICIAL_HOSTS = ("gov.uk", "gov.in", "gov.au", "govt.nz", "europa.eu", "who.int", "un.org", "cisa.gov", "nist.gov", "cdc.gov")
_ACADEMIC_SUFFIXES = (".edu", ".ac.uk", ".ac.in", ".edu.au")
_RECOGNIZED_PUBLISHERS = {"reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "ft.com", "nytimes.com", "theguardian.com", "bloomberg.com", "hindustantimes.com", "indianexpress.com", "thehindu.com", "thewire.in", "scroll.in", "firstpost.com", "lokmatimes.com"}
_AGGREGATOR_HOSTS = {"news.google.com", "news.yahoo.com", "yahoo.com", "msn.com", "note.com"}

@dataclass(frozen=True)
class SourceReliabilityAssessment:
    source_id: str
    declared_reliability: float
    domain_prior: float
    assessed_reliability: float
    host: str
    domain_class: str
    flags: tuple[str, ...]
    version: str = SOURCE_RELIABILITY_ASSESSMENT_VERSION

    def __post_init__(self) -> None:
        for score in (self.declared_reliability, self.domain_prior, self.assessed_reliability):
            if not 0.0 <= score <= 1.0:
                raise ValueError("reliability assessment scores must be between 0 and 1")

def _host_from_locator(locator: str) -> str:
    try:
        host = (urlparse(str(locator or "").strip()).hostname or "").lower().rstrip(".")
    except (TypeError, ValueError):
        return ""
    return host[4:] if host.startswith("www.") else host

def _is_host_or_subdomain(host: str, domain: str) -> bool:
    return host == domain or host.endswith("." + domain)

def _domain_prior(host: str) -> tuple[float, str]:
    if not host:
        return 0.35, "missing_host"
    if any(_is_host_or_subdomain(host, item) for item in _AGGREGATOR_HOSTS):
        return 0.42, "aggregator_or_platform"
    if host == "gov" or host.endswith(".gov") or any(_is_host_or_subdomain(host, item) for item in _OFFICIAL_HOSTS):
        return 0.86, "official_or_intergovernmental"
    if any(host.endswith(suffix) for suffix in _ACADEMIC_SUFFIXES):
        return 0.80, "academic_domain"
    if any(_is_host_or_subdomain(host, item) for item in _RECOGNIZED_PUBLISHERS):
        return 0.74, "recognized_publisher"
    return 0.50, "unclassified_domain"

def assess_source_reliability(source: Any) -> SourceReliabilityAssessment:
    """Explainable source-reliability prior for ranking; not a truth check."""
    def value(name: str, default: Any = None) -> Any:
        if isinstance(source, Mapping):
            return source.get(name, default)
        return getattr(source, name, default)

    source_id = str(value("source_id", "") or "")
    locator = str(value("locator", "") or "")
    metadata: Mapping[str, Any] = value("metadata", {}) or {}
    try:
        declared = float(value("reliability", 0.0))
    except (TypeError, ValueError):
        declared = 0.0
    declared = max(0.0, min(1.0, declared))
    host = _host_from_locator(locator)
    prior, domain_class = _domain_prior(host)
    flags: list[str] = []
    method = str(metadata.get("reliability_method", "") or "").casefold()
    if method in {"human_review", "manual_review", "expert_review"}:
        assessed = declared
        flags.append("explicit_human_review_preserved")
    else:
        assessed = declared * DECLARED_RELIABILITY_WEIGHT + prior * DOMAIN_PRIOR_WEIGHT
        flags.append("declared_score_blended_with_domain_prior")
    if metadata.get("discovery_only") is True:
        assessed = min(assessed, 0.25)
        flags.append("discovery_only_capped")
    if metadata.get("publisher_identity_verified") is False:
        assessed = min(assessed, 0.30)
        flags.append("publisher_identity_unverified_capped")
    if metadata.get("is_aggregator_wrapper") is True:
        assessed = min(assessed, 0.35)
        flags.append("aggregator_wrapper_capped")
    if not host:
        flags.append("missing_or_invalid_host")
    return SourceReliabilityAssessment(source_id, round(declared, 4), round(prior, 4), round(max(0.0, min(1.0, assessed)), 4), host, domain_class, tuple(flags))
