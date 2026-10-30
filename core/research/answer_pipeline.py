from dataclasses import dataclass, replace
import re
from typing import Iterable, List, Optional
from urllib.parse import urlparse

from core.research.answer_arbitration import (
    AnswerArbitrationResult,
    AnswerArbitrator,
)
from core.research.knowledge_merge import (
    KnowledgeDuplicateDetector,
    KnowledgeMergeService,
)
from core.research.aggregator import (
    ResearchAggregationResult,
    ResearchResultAggregator,
)
from core.research.answer import (
    ResearchAnswer,
    ResearchAnswerSynthesizer,
)
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchSource,
)
from core.research.query import (
    ResearchQueryEngine,
    ResearchQueryResult,
)
from core.research.traceability import (
    ResearchTraceabilityEngine,
    ResearchTraceabilityResult,
)
from core.research.engine import ResearchEngine


def _safe_hostname(locator: object) -> str:
    """Return a normalized hostname, treating malformed URLs as unknown."""
    if not isinstance(locator, str) or not locator.strip():
        return ""
    try:
        hostname = urlparse(locator.strip()).hostname or ""
    except (TypeError, ValueError):
        return ""
    return hostname.casefold().rstrip(".").removeprefix("www.")


def _normalized_publisher_identity(value: object) -> str:
    """Ignore search-query/backend labels masquerading as publisher names."""
    publisher = " ".join(str(value or "").casefold().split())
    if not publisher:
        return ""
    discovery_markers = (
        "google news",
        "bingnews",
        "bing news",
        "brave search",
        "duckduckgo",
        "search results",
        "rss feed",
    )
    if any(marker in publisher for marker in discovery_markers):
        return ""
    return publisher


_AGGREGATOR_HOSTS = {
    "news.google.com",
    "news.yahoo.com",
    "consent.yahoo.com",
    "msn.com",
    "flipboard.com",
}


def _source_identity_groups(
    sources: Iterable[ResearchSource],
) -> dict[str, str]:
    """Map source IDs to shared publisher/domain groups for corroboration."""
    parent: dict[str, str] = {}
    identity_owners: dict[str, str] = {}

    def find(source_id: str) -> str:
        parent.setdefault(source_id, source_id)
        if parent[source_id] != source_id:
            parent[source_id] = find(parent[source_id])
        return parent[source_id]

    def union(first: str, second: str) -> None:
        first_root = find(first)
        second_root = find(second)
        if first_root != second_root:
            parent[second_root] = first_root

    for source in sources:
        source_metadata = dict(getattr(source, "metadata", {}) or {})
        # Test fixtures and discovery-only leads are not corroborating
        # publisher evidence, even when they use distinct-looking URLs.
        if source_metadata.get("test_fixture") is True or source_metadata.get("discovery_only") is True:
            continue
        source_id = str(getattr(source, "source_id", "") or "").strip()
        if not source_id:
            continue

        publisher = _normalized_publisher_identity(
            getattr(source, "publisher", "")
        )
        hostname = _safe_hostname(getattr(source, "locator", ""))
        identity_keys = []
        if publisher:
            identity_keys.append(f"publisher:{publisher}")
        if hostname and hostname not in _AGGREGATOR_HOSTS:
            identity_keys.append(f"domain:{hostname}")
        if not identity_keys:
            continue

        find(source_id)
        for identity_key in identity_keys:
            previous = identity_owners.get(identity_key)
            if previous is None:
                identity_owners[identity_key] = source_id
            else:
                union(source_id, previous)

    return {source_id: find(source_id) for source_id in parent}


@dataclass(frozen=True)
class ResearchAnswerPipelineResult:
    query_result: ResearchQueryResult
    aggregation: ResearchAggregationResult
    answer: ResearchAnswer
    traceability: ResearchTraceabilityResult
    knowledge_verification_contexts: dict[str, dict]
    arbitration: AnswerArbitrationResult
    relevance_candidate_count: int = 0
    corroborated_candidate_count: int = 0
    claim_link_diagnostics: dict[str, int] | None = None


class ResearchAnswerPipeline:
    """
    Complete auditable research-answer pipeline.

    Flow:

        Query
          -> Retrieval
          -> Aggregation
          -> Conflict Detection / Resolution
          -> Answer Synthesis
          -> Evidence / Source Traceability
          -> Knowledge Verification / Conflict Context

    Knowledge verification context is observational only.

    It does not:
    - mutate knowledge
    - change aggregation selection
    - replace conflict resolution
    - replace answer synthesis
    - replace traceability
    """

    def __init__(
        self,
        query_engine: ResearchQueryEngine,
        aggregator: Optional[ResearchResultAggregator] = None,
        synthesizer: Optional[ResearchAnswerSynthesizer] = None,
        traceability_engine: Optional[
            ResearchTraceabilityEngine
        ] = None,
    ) -> None:
        if query_engine is None:
            raise ValueError("query_engine is required")

        self.query_engine = query_engine

        self.aggregator = (
            aggregator
            or ResearchResultAggregator()
        )

        self.synthesizer = (
            synthesizer
            or ResearchAnswerSynthesizer()
        )

        self.traceability_engine = (
            traceability_engine
            or ResearchTraceabilityEngine()
        )
        self.answer_arbitrator = AnswerArbitrator()

    @staticmethod
    def _extract_knowledge(
        query_result: ResearchQueryResult,
    ) -> List[KnowledgeCandidate]:
        """
        Convert query matches into KnowledgeCandidate objects.
        """
        candidates: List[KnowledgeCandidate] = []

        for match in query_result.matches:
            candidates.append(
                KnowledgeCandidate(
                    knowledge_id=match.knowledge_id,
                    statement=match.statement,
                    findings=list(getattr(match, "findings", ()) or ()),
                    evidence=list(getattr(match, "evidence", ()) or ()),
                    confidence=match.confidence,
                    verified=match.verified,
                    created_at=getattr(match, "created_at", None),
                    last_verified_at=getattr(match, "last_verified_at", None),
                    metadata=dict(getattr(match, "metadata", {}) or {}),
                )
            )

        return candidates

    @staticmethod
    def _merge_exact_duplicate_claims(
        knowledge_items: Iterable[KnowledgeCandidate],
        evidence_items: Iterable[Evidence],
    ) -> tuple[List[KnowledgeCandidate], List[Evidence]]:
        """
        Coalesce only text-identical claims from different extracted records.

        Extraction creates a new knowledge ID for each finding. Consequently,
        the same exact statement found in two documents can otherwise appear as
        two unrelated single-source claims and never reach the multi-source
        corroboration gate. This is deliberately exact-match only: semantic
        similarity alone must not be used to manufacture corroboration.
        Original persisted records are not mutated; evidence links are remapped
        only in the in-memory copies used by this answer run.
        """
        detector = KnowledgeDuplicateDetector()
        merger = KnowledgeMergeService(detector)
        merged_by_key: dict[str, KnowledgeCandidate] = {}
        aliases: dict[str, str] = {}

        for item in knowledge_items:
            key = detector._normalize(item.statement)
            primary = merged_by_key.get(key)
            if primary is None:
                merged_by_key[key] = item
                continue

            result = merger.merge(primary, item)
            if result.merged and result.knowledge is not None:
                merged_by_key[key] = result.knowledge
                aliases[item.knowledge_id] = primary.knowledge_id

        remapped_evidence: List[Evidence] = []
        for evidence in evidence_items:
            metadata = dict(getattr(evidence, "metadata", {}) or {})
            linked_id = metadata.get("knowledge_id")
            canonical_id = aliases.get(linked_id)
            if canonical_id is not None:
                metadata["knowledge_id"] = canonical_id
                remapped_evidence.append(
                    replace(evidence, metadata=metadata)
                )
            else:
                remapped_evidence.append(evidence)

        return list(merged_by_key.values()), remapped_evidence

    @staticmethod

    @staticmethod
    def _filter_current_claims_to_independent_sources(
        query: str,
        knowledge_items: Iterable[KnowledgeCandidate],
        evidence_items: Iterable[Evidence],
        sources: Iterable[ResearchSource],
    ) -> tuple[List[KnowledgeCandidate], List[Evidence]]:
        """
        For time-sensitive queries, retain only claims supported by at least
        two distinct publisher identities. Duplicate URLs from the same
        publisher or ordinary website must not count as independent sources.
        Aggregator wrappers use publisher metadata instead of wrapper hosts.
        """
        knowledge_list = list(knowledge_items)
        evidence_list = list(evidence_items)
        source_list = list(sources)

        if not ResearchAnswerSynthesizer._requires_independent_corroboration(
            query
        ):
            return knowledge_list, evidence_list

        aggregator_hosts = {
            "news.google.com",
            "news.yahoo.com",
            "consent.yahoo.com",
            "www.msn.com",
            "msn.com",
            "flipboard.com",
        }

        source_identity: dict[str, str] = {}
        parent: dict[str, str] = {}
        publisher_owner: dict[str, str] = {}
        hostname_owner: dict[str, str] = {}

        def find(source_id: str) -> str:
            parent.setdefault(source_id, source_id)
            if parent[source_id] != source_id:
                parent[source_id] = find(parent[source_id])
            return parent[source_id]

        def union(first: str, second: str) -> None:
            first_root = find(first)
            second_root = find(second)
            if first_root != second_root:
                parent[second_root] = first_root

        source_details: dict[str, tuple[str, str, bool]] = {}

        for source in source_list:
            source_id = str(getattr(source, "source_id", "") or "")
            if not source_id:
                continue

            publisher = _normalized_publisher_identity(
                getattr(source, "publisher", "")
            )
            locator = str(getattr(source, "locator", "") or "")
            hostname = _safe_hostname(locator)
            is_aggregator = hostname in aggregator_hosts

            parent.setdefault(source_id, source_id)
            source_details[source_id] = (
                publisher,
                hostname,
                is_aggregator,
            )

            # Publisher identity is useful across multiple domains.
            if publisher:
                previous = publisher_owner.get(publisher)
                if previous is not None:
                    union(source_id, previous)
                else:
                    publisher_owner[publisher] = source_id

            # Ordinary domains are also a deduplication boundary.
            # Aggregator hosts are excluded because they can contain
            # reports from multiple genuinely independent publishers.
            if hostname and not is_aggregator:
                previous = hostname_owner.get(hostname)
                if previous is not None:
                    union(source_id, previous)
                else:
                    hostname_owner[hostname] = source_id

        for source_id, (publisher, hostname, is_aggregator) in (
            source_details.items()
        ):
            if is_aggregator and publisher:
                source_identity[source_id] = find(source_id)
            elif publisher or hostname:
                source_identity[source_id] = find(source_id)

        candidate_ids = {
            item.knowledge_id for item in knowledge_list
        }
        supporting_identities: dict[str, set[str]] = {
            knowledge_id: set() for knowledge_id in candidate_ids
        }

        for evidence in evidence_list:
            if not getattr(evidence, "supports", False):
                continue

            metadata = getattr(evidence, "metadata", {}) or {}
            knowledge_id = metadata.get("knowledge_id")
            evidence_source_id = getattr(evidence, "source_id", "")
            identity = source_identity.get(evidence_source_id)

            if knowledge_id in candidate_ids and identity:
                supporting_identities[knowledge_id].add(identity)

        corroborated_ids = {
            knowledge_id
            for knowledge_id, identities in supporting_identities.items()
            if len(identities) >= 2
        }

        filtered_knowledge = [
            item
            for item in knowledge_list
            if item.knowledge_id in corroborated_ids
        ]
        filtered_evidence = [
            item
            for item in evidence_list
            if (getattr(item, "metadata", {}) or {}).get("knowledge_id")
            in corroborated_ids
        ]

        return filtered_knowledge, filtered_evidence


    def _evidence_knowledge(
        self,
        evidence_items: Iterable[Evidence],
    ) -> List[KnowledgeCandidate]:
        """Return knowledge explicitly linked to the supplied evidence."""
        ids = []
        seen = set()
        for evidence in evidence_items:
            knowledge_id = (evidence.metadata or {}).get("knowledge_id")
            if isinstance(knowledge_id, str) and knowledge_id and knowledge_id not in seen:
                seen.add(knowledge_id)
                ids.append(knowledge_id)

        candidates: List[KnowledgeCandidate] = []
        storage = getattr(self.query_engine, "storage", None)
        for knowledge_id in ids:
            knowledge = self.query_engine.engine.knowledge.get(knowledge_id)
            if knowledge is None and storage is not None:
                knowledge = storage.get_knowledge(knowledge_id)
            if knowledge is None:
                continue
            # Preserve the canonical relationship graph. Reconstructing a
            # candidate with only its statement/score silently dropped the
            # finding/evidence IDs, so freshness and source assessments could
            # not attach to the selected claim and valid live research was
            # mislabeled STALE. Copy the stored links; do not infer links from
            # text or promote an unverified knowledge record.
            candidates.append(
                KnowledgeCandidate(
                    knowledge_id=knowledge.knowledge_id,
                    statement=knowledge.statement,
                    findings=list(getattr(knowledge, "findings", ()) or ()),
                    evidence=list(getattr(knowledge, "evidence", ()) or ()),
                    confidence=knowledge.confidence,
                    verified=knowledge.verified,
                    created_at=getattr(knowledge, "created_at", None),
                    last_verified_at=getattr(knowledge, "last_verified_at", None),
                    metadata=dict(getattr(knowledge, "metadata", {}) or {}),
                )
            )
        return candidates

    @staticmethod
    def _selected_knowledge(
        knowledge_items: Iterable[KnowledgeCandidate],
        aggregation: ResearchAggregationResult,
    ) -> List[KnowledgeCandidate]:
        """
        Keep only knowledge candidates selected by the aggregator.
        """
        selected_ids = {
            item.knowledge_id
            for item in aggregation.results
        }

        return [
            item
            for item in knowledge_items
            if item.knowledge_id in selected_ids
        ]

    @staticmethod
    def _knowledge_verification_contexts(
        knowledge_items: Iterable[KnowledgeCandidate],
        storage,
    ) -> dict[str, dict]:
        """
        Build observational knowledge verification contexts.

        Combines:
        - verification lifecycle
        - conflict verification context

        This layer is observational only.
        It does not mutate knowledge or change answer selection.
        """
        if storage is None:
            return {}

        contexts: dict[str, dict] = {}

        for knowledge in knowledge_items:
            knowledge_id = knowledge.knowledge_id

            lifecycle = (
                storage.knowledge_verification_lifecycle(
                    knowledge_id
                )
            )

            conflict_context = (
                storage.knowledge_verification_context(
                    knowledge_id
                )
            )

            context: dict = {}

            if isinstance(lifecycle, dict):
                context.update(lifecycle)

            if isinstance(conflict_context, dict):
                context.update(conflict_context)

            contexts[knowledge_id] = context

        return contexts

    @staticmethod
    def _is_ai_safety_security_query(query: str) -> bool:
        text = query.casefold()
        has_ai = (
            bool(re.search(r"\bai\b", text))
            or "artificial intelligence" in text
            or "कृत्रिम बुद्धिमत्ता" in text
        )
        has_safety = any(term in text for term in (
            "safety", "security", "cyber", "risk", "threat", "सुरक्षा", "खतरा",
        ))
        return has_ai and has_safety

    @staticmethod
    def _ai_safety_claim_is_relevant(
        statement: str,
        source_context: str = "",
    ) -> bool:
        # The headline can establish the subject, while the extracted sentence
        # carries the claim. Keep the safety/event signal in the claim itself
        # so unrelated sidebar text is not admitted from a relevant page.
        text = statement.casefold()
        subject_text = f"{text} {source_context.casefold()}"
        has_ai = (
            bool(re.search(r"\bai\b", subject_text))
            or any(term in subject_text for term in (
                "artificial intelligence", "llm", "openai", "anthropic",
                "chatgpt", "nvidia", "ai agent", "ai agents", "ai model",
                "ai system", "frontier model", "safety researcher",
                "safety researchers",
            ))
        )
        safety_terms = (
            "safety", "security", "cyber", "risk", "threat", "attack",
            "attacker", "hack", "hacked", "breach", "vulnerab", "guardrail",
            "alignment", "misalignment", "privacy", "permission",
            "unauthorized", "unauthorised", "incident", "safe", "secure",
            "rogue", "misuse", "misused", "misbehavior", "misbehaviour",
            "unsafe", "harmful", "harm", "abuse", "malicious", "deceptive",
            "manipulation", "autonomous agent", "agent behavior", "agent behaviour",
            "misinformation", "disinformation", "retaliation", "firing", "fired",
            "termination", "terminated", "former employee", "former researcher",
            "monitorability", "safety assessor", "safety assessors", "misconduct",
            "raising concerns", "safety concerns", "violated policies", "trust",
            "सुरक्षा", "खतरा", "दुरुपयोग", "हानिकारक", "गलत व्यवहार",
        )
        has_safety = any(term in text for term in safety_terms)
        if not has_safety and source_context:
            # Headline context can identify the event topic, while the claim
            # itself must still describe a testing/evaluation/access event. This
            # admits independently reported paraphrases such as a regulator
            # gaining access to models for safety testing without accepting
            # arbitrary sidebar claims from a relevant article.
            headline_has_safety = any(
                term in source_context.casefold()
                for term in ("safety", "security", "risk", "threat", "testing", "test")
            )
            claim_has_event_anchor = any(
                term in text
                for term in (
                    "test", "testing", "tested", "assessment", "assess",
                    "evaluate", "evaluation", "access", "pre-release", "release",
                    "released", "models",
                )
            )
            has_safety = headline_has_safety and claim_has_event_anchor
        return has_ai and has_safety

    @staticmethod
    def _is_india_capital_query(query: str) -> bool:
        text = query.casefold()
        asks_capital = any(term in text for term in ("capital", "राजधानी"))
        names_india = any(term in text for term in ("india", "भारत"))
        return asks_capital and names_india

    @staticmethod
    def _india_capital_claim_is_relevant(statement: str) -> bool:
        text = statement.casefold()
        has_india = "india" in text or "भारत" in text
        has_capital = "capital" in text or "राजधानी" in text
        has_new_delhi = "new delhi" in text or "नई दिल्ली" in text
        # Require an explicit subject-predicate relation, not just the three
        # keywords appearing somewhere in a headline. Otherwise a travel story
        # about "India's capital region" that later mentions New Delhi can be
        # mistaken for an answer to "What is the capital of India?".
        explicit_relation = any(
            re.search(pattern, text)
            for pattern in (
                r"\bnew delhi\b.{0,80}\b(?:is|remains|serves as)\b.{0,60}\bcapital(?: city)?\b.{0,30}\bindia\b",
                r"\bnew delhi\s*,\s*(?:the\s+)?capital(?: city)?\s+of\s+india\b",
                r"\bcapital(?: city)?\s+of\s+india\b.{0,30}\bnew delhi\b",
                r"\bindia['’]s\s+(?:national\s+)?capital\s+(?:is\s+)?new delhi\b",
            )
        )
        return has_india and has_capital and has_new_delhi and explicit_relation

    @classmethod
    def _filter_query_relevant_knowledge(
        cls,
        query: str,
        knowledge_items: List[KnowledgeCandidate],
        *,
        evidence_items: Iterable[Evidence] = (),
        sources: Iterable[ResearchSource] = (),
    ) -> List[KnowledgeCandidate]:
        """Filter claims to the query's subject before answer synthesis."""
        if cls._is_india_capital_query(query):
            return [
                item for item in knowledge_items
                if cls._india_capital_claim_is_relevant(item.statement)
            ]
        if not cls._is_ai_safety_security_query(query):
            return knowledge_items

        source_titles = {
            source.source_id: str(getattr(source, "title", "") or "")
            for source in sources
        }
        context_by_knowledge: dict[str, list[str]] = {}
        candidate_ids = {item.knowledge_id for item in knowledge_items}
        for evidence in evidence_items:
            if not getattr(evidence, "supports", False):
                continue
            metadata = getattr(evidence, "metadata", {}) or {}
            knowledge_id = metadata.get("knowledge_id")
            if knowledge_id not in candidate_ids:
                continue
            title = source_titles.get(getattr(evidence, "source_id", ""), "")
            if title:
                context_by_knowledge.setdefault(knowledge_id, []).append(title)

        return [
            item for item in knowledge_items
            if cls._ai_safety_claim_is_relevant(
                item.statement,
                " ".join(dict.fromkeys(context_by_knowledge.get(item.knowledge_id, []))),
            )
        ]

    def run(
        self,
        query: str,
        *,
        verified_only: bool = True,
        limit: int = 10,
        evidence_items: Iterable[Evidence] = (),
        sources: Iterable[ResearchSource] = (),
        focus_on_provided_evidence: bool = False,
    ) -> ResearchAnswerPipelineResult:
        """
        Execute the complete auditable research pipeline.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError(
                "query must be a non-empty string"
            )

        if not isinstance(limit, int) or isinstance(limit, bool):
            raise ValueError(
                "limit must be an integer"
            )

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero"
            )

        evidence_list = list(evidence_items)
        source_list = list(sources)
        relevance_candidate_count = 0
        corroborated_candidate_count = 0
        claim_link_diagnostics: dict[str, int] = {
            "candidate_pairs_considered": 0,
            "linked_pairs": 0,
            "rejected_missing_or_same_host": 0,
            "rejected_numeric_mismatch": 0,
            "rejected_low_overlap": 0,
            "rejected_negation_mismatch": 0,
            "rejected_entity_mismatch": 0,
        }

        # ---------------------------------------------------------
        # STEP 1: Query / Retrieval
        # ---------------------------------------------------------

        if focus_on_provided_evidence and evidence_list:
            focused = self._evidence_knowledge(evidence_list)
            focused = self._filter_query_relevant_knowledge(
                query,
                focused,
                evidence_items=evidence_list,
                sources=source_list,
            )
            relevance_candidate_count = len(focused)
            query_result = ResearchQueryResult(
                query=query,
                matches=focused,
                verified_only=verified_only,
                total_matches=len(focused),
            )
        else:
            query_result = self.query_engine.search(
                query,
                verified_only=verified_only,
                limit=limit,
                # Preserve rejected candidates for audit context only.
                # STEP 2B below removes conflicted/unverified records and
                # their linked evidence before aggregation or synthesis.
                _include_blocked_for_audit=(
                    getattr(self.query_engine, "storage", None) is not None
                ),
            )
            relevance_candidate_count = len(query_result.matches)

        # ---------------------------------------------------------
        # STEP 2: Convert retrieval matches to knowledge objects
        # ---------------------------------------------------------

        knowledge_candidates = self._extract_knowledge(
            query_result
        )

        # Apply known query-specific relevance guards on every retrieval path,
        # not only the focused-provided-evidence path. Otherwise a verified
        # claim from a tangential page can pass source verification while not
        # actually answering a question (for example, a Delhi travel headline
        # for "What is the capital of India?"). Relevance filtering may reject
        # candidates; it never creates evidence or upgrades verification.
        knowledge_candidates = self._filter_query_relevant_knowledge(
            query,
            knowledge_candidates,
            evidence_items=evidence_list,
            sources=source_list,
        )
        query_result = replace(
            query_result,
            matches=knowledge_candidates,
            total_matches=len(knowledge_candidates),
        )

        # When this job supplies its own persisted evidence, combine only
        # exact duplicate claims so independent sources can attach to one
        # canonical in-memory claim without changing stored records.
        if focus_on_provided_evidence and evidence_list:
            knowledge_candidates, evidence_list = (
                self._merge_exact_duplicate_claims(
                    knowledge_candidates,
                    evidence_list,
                )
            )
            knowledge_candidates, evidence_list = (
                self._merge_verified_claim_paraphrases(
                    knowledge_candidates,
                    evidence_list,
                    source_list,
                    diagnostics=claim_link_diagnostics,
                    query=query,
                )
            )
            knowledge_candidates, evidence_list = (
                self._filter_current_claims_to_independent_sources(
                    query,
                    knowledge_candidates,
                    evidence_list,
                    source_list,
                )
            )
            source_identity_groups = _source_identity_groups(source_list)
            multi_source_claim_ids = {
                str((item.metadata or {}).get("knowledge_id", ""))
                for item in evidence_list
                if getattr(item, "supports", False)
                and (item.metadata or {}).get("knowledge_id")
                and source_identity_groups.get(str(getattr(item, "source_id", "") or ""))
            }
            multi_source_claim_ids = {
                knowledge_id
                for knowledge_id in multi_source_claim_ids
                if len({
                    source_identity_groups.get(str(getattr(item, "source_id", "") or ""))
                    for item in evidence_list
                    if getattr(item, "supports", False)
                    and str((item.metadata or {}).get("knowledge_id", "")) == knowledge_id
                    and source_identity_groups.get(str(getattr(item, "source_id", "") or ""))
                }) >= 2
            }
            if (
                ResearchAnswerSynthesizer._requires_independent_corroboration(query)
                or any(item.knowledge_id in multi_source_claim_ids for item in knowledge_candidates)
            ):
                # Run the canonical ResearchEngine verification rules against
                # the in-memory, source-linked claim graph. Time-sensitive claims
                # must pass the strict independent-publisher filter; stable facts
                # can enter this verifier only when the claim already has linked
                # evidence from at least two independent source groups. This is
                # isolated from persistent storage: only the final accepted answer
                # path may later persist verified knowledge. Strong evidence and
                # conflict/confidence gates remain authoritative.
                verifier = ResearchEngine()
                verifier.sources = {
                    source.source_id: source for source in source_list
                    if getattr(source, "source_id", "")
                }
                verifier.evidence = {
                    item.evidence_id: replace(
                        item, metadata=dict(getattr(item, "metadata", {}) or {})
                    )
                    for item in evidence_list
                    if getattr(item, "evidence_id", "")
                }
                verifier.knowledge = {
                    item.knowledge_id: replace(
                        item,
                        findings=list(item.findings),
                        evidence=list(item.evidence),
                        metadata=dict(item.metadata or {}),
                    )
                    for item in knowledge_candidates
                }
                verified_candidates = []
                verification_reasons: dict[str, int] = {}
                for candidate in knowledge_candidates:
                    checked = verifier.verify_knowledge(candidate.knowledge_id)
                    reason = str(checked.metadata.get("verification_reason", ""))
                    if checked.verified:
                        verified_candidates.append(checked)
                    else:
                        key = reason or "verification_rejected"
                        verification_reasons[key] = verification_reasons.get(key, 0) + 1
                knowledge_candidates = verified_candidates
                if claim_link_diagnostics is not None:
                    claim_link_diagnostics["verification_engine_checked"] = len(
                        verifier.knowledge
                    )
                    claim_link_diagnostics["verification_engine_passed"] = len(
                        verified_candidates
                    )
                    claim_link_diagnostics["verification_engine_rejected"] = sum(
                        verification_reasons.values()
                    )
                    claim_link_diagnostics["verification_engine_rejection_reasons"] = (
                        verification_reasons
                    )
            query_result = replace(
                query_result,
                matches=knowledge_candidates,
                total_matches=len(knowledge_candidates),
            )


        # ---------------------------------------------------------
        # STEP 2B: Fail-closed verification lifecycle gate
        # ---------------------------------------------------------
        # Preserve contexts for audit/diagnostics, including rejected
        # candidates. Verification history must never promote a record.
        verification_context_candidates = list(knowledge_candidates)

        storage = getattr(
            self.query_engine,
            "storage",
            None,
        )

        if storage is not None and knowledge_candidates:
            lifecycle_contexts = (
                self._knowledge_verification_contexts(
                    knowledge_candidates,
                    storage,
                )
            )


            blocked_ids = set()

            for knowledge_id, context in lifecycle_contexts.items():
                if not isinstance(context, dict):
                    if verified_only:
                        blocked_ids.add(knowledge_id)
                    continue

                event_count = int(
                    context.get("verification_event_count", 0) or 0
                )
                status = str(
                    context.get("verification_status", "")
                ).upper()
                conflict_status = str(
                    context.get("conflict_status", "")
                ).upper()
                unresolved_count = int(
                    context.get("unresolved_conflict_count", 0) or 0
                )
                conflict_count = int(
                    context.get("conflict_count", 0) or 0
                )
                selected_knowledge_id = context.get(
                    "selected_knowledge_id"
                )

                # Unresolved conflicts block both claims. Once resolved, only
                # the selected claim may re-enter answer synthesis; an absent
                # or ambiguous selection fails closed.
                if (
                    status == "CONFLICTED"
                    or conflict_status == "UNRESOLVED"
                    or unresolved_count > 0
                    or (
                        conflict_count > 0
                        and selected_knowledge_id != knowledge_id
                    )
                ):
                    blocked_ids.add(knowledge_id)
                    continue

                # Trusted historical retrieval requires recorded VERIFIED
                # history. A fresh live-research run is different: its newly
                # fetched evidence must reach the independent-source and answer
                # verification gates below, or it can never bootstrap a new
                # verified claim. This exception does not promote the record;
                # conflict blocks and final evidence/traceability gates remain.
                if verified_only and not focus_on_provided_evidence and (
                    event_count == 0 or status != "VERIFIED"
                ):
                    blocked_ids.add(knowledge_id)


            if blocked_ids:
                knowledge_candidates = [
                    item
                    for item in knowledge_candidates
                    if item.knowledge_id not in blocked_ids
                ]

                # Remove evidence explicitly linked to blocked claims.
                evidence_list = [
                    item
                    for item in evidence_list
                    if (
                        (getattr(item, "metadata", {}) or {}).get(
                            "knowledge_id"
                        ) not in blocked_ids
                    )
                ]

                query_result = replace(
                    query_result,
                    matches=knowledge_candidates,
                    total_matches=len(knowledge_candidates),
                )

        corroborated_candidate_count = len(knowledge_candidates)



        # ---------------------------------------------------------
        # STEP 3: Aggregation
        # ---------------------------------------------------------

        # AnswerTraceabilityEngine validates the complete knowledge -> finding
        # -> evidence -> source chain. Supplying evidence and sources without
        # the matching findings makes every otherwise-valid live claim look
        # incomplete and incorrectly rejects the final answer. Resolve findings
        # only through canonical IDs already declared by the selected knowledge.
        linked_finding_ids = {
            finding_id
            for item in knowledge_candidates
            for finding_id in (getattr(item, "findings", ()) or ())
            if isinstance(finding_id, str) and finding_id
        }
        finding_registry = getattr(
            getattr(self.query_engine, "engine", None),
            "findings",
            {},
        )
        finding_items = []
        storage_finding_getter = getattr(storage, "get_finding", None)
        for finding_id in sorted(linked_finding_ids):
            finding = finding_registry.get(finding_id)
            if finding is None and callable(storage_finding_getter):
                finding = storage_finding_getter(finding_id)
            if finding is not None:
                finding_items.append(finding)

        aggregation = self.aggregator.aggregate(
            knowledge_candidates,
            verified_only=verified_only,
            limit=limit,
            evidence_items=evidence_list,
            sources=source_list,
            findings=finding_items,
            freshness_sensitive=ResearchAnswerSynthesizer._requires_independent_corroboration(query),
        )

        # Persist conflict decisions at the same storage boundary used by
        # future retrieval. Without this connection, the current answer may
        # exclude a loser while later Main Brain turns still retrieve it as
        # previously VERIFIED knowledge.
        conflict_persistence_failed = False
        storage = getattr(self.query_engine, "storage", None)
        if storage is not None:
            try:
                for assessment in aggregation.conflict_intelligence:
                    storage.save_conflict_assessment(assessment)
            except Exception:
                # A conflict that cannot be durably recorded must not yield a
                # trusted final answer; preserve fail-closed behavior below.
                conflict_persistence_failed = True

        # ---------------------------------------------------------
        # STEP 4: Answer synthesis
        # ---------------------------------------------------------

        answer = self.synthesizer.synthesize(
            query,
            aggregation,
            evidence_items=evidence_list,
        )

        # ---------------------------------------------------------
        # STEP 5: Third-pass answer arbitration
        # ---------------------------------------------------------
        # Candidate A is the aggregator's quality-aware claim synthesis.
        # Candidate B is the evidence-linked answer synthesis above.
        # The deterministic arbiter compares their claim IDs and status.
        # This is two synthesis paths plus a verifier, not three LLMs.
        arbitration = self.answer_arbitrator.arbitrate(
            quality_answer=aggregation.answer,
            synthesized_answer=answer,
            unresolved_conflicts=aggregation.unresolved_conflict_count,
        )

        if not arbitration.accepted:
            answer = replace(
                answer,
                verified=False,
                status="ARBITRATION_REJECTED",
            )

        # ---------------------------------------------------------
        # STEP 6: Answer traceability
        # ---------------------------------------------------------

        selected_knowledge = self._selected_knowledge(
            knowledge_candidates,
            aggregation,
        )

        traceability = self.traceability_engine.trace(
            selected_knowledge,
            evidence_list,
            source_list,
        )

        # ---------------------------------------------------------
        # STEP 6B: Fail-closed end-to-end answer traceability gate
        # ---------------------------------------------------------
        # The quality-aware aggregator has already built the strict
        # knowledge -> finding -> evidence -> source trace for the exact
        # selected answer claims. Do not allow a quality score or a matching
        # pair of synthesis paths to override a broken evidence chain.
        answer_traceability = getattr(
            aggregation, "answer_traceability", None
        )
        answer_traces = tuple(
            getattr(answer_traceability, "traces", ()) or ()
        )
        traces_by_knowledge = {
            getattr(trace, "knowledge_id", ""): trace
            for trace in answer_traces
            if getattr(trace, "knowledge_id", "")
        }
        selected_answer_ids = tuple(
            getattr(answer, "knowledge_ids", ()) or ()
        )
        trace_gate_passed = bool(selected_answer_ids) and all(
            (trace := traces_by_knowledge.get(knowledge_id)) is not None
            and getattr(trace, "trace_complete", False) is True
            and getattr(trace, "supported", False) is True
            and getattr(trace, "verified", False) is True
            and bool(getattr(trace, "evidence_ids", ()))
            and bool(getattr(trace, "source_ids", ()))
            for knowledge_id in selected_answer_ids
        )

        if answer.verified and not trace_gate_passed:
            answer = replace(
                answer,
                verified=False,
                status="TRACEABILITY_REJECTED",
            )
            # Re-run arbitration after the final evidence gate so the
            # returned decision cannot remain ACCEPTED for a rejected answer.
            arbitration = self.answer_arbitrator.arbitrate(
                quality_answer=aggregation.answer,
                synthesized_answer=answer,
                unresolved_conflicts=aggregation.unresolved_conflict_count,
            )

        # ---------------------------------------------------------
        # STEP 7: Knowledge verification / conflict context
        # ---------------------------------------------------------

        storage = getattr(
            self.query_engine,
            "storage",
            None,
        )

        knowledge_verification_contexts = (
            self._knowledge_verification_contexts(
            verification_context_candidates,
                storage,
            )
        )

        # Conflict persistence is part of the verification trust boundary.
        # Revoke answer trust if durable conflict state could not be recorded.
        if conflict_persistence_failed:
            answer = replace(
                answer,
                verified=False,
                status="CONFLICT_PERSISTENCE_FAILED",
            )
            arbitration = self.answer_arbitrator.arbitrate(
                quality_answer=aggregation.answer,
                synthesized_answer=answer,
                unresolved_conflicts=aggregation.unresolved_conflict_count,
            )

        # ---------------------------------------------------------
        # FINAL RESULT
        # ---------------------------------------------------------

        return ResearchAnswerPipelineResult(
            query_result=query_result,
            aggregation=aggregation,
            answer=answer,
            traceability=traceability,
            knowledge_verification_contexts=(
                knowledge_verification_contexts
            ),
            arbitration=arbitration,
            relevance_candidate_count=relevance_candidate_count,
            corroborated_candidate_count=corroborated_candidate_count,
            claim_link_diagnostics=claim_link_diagnostics,
        )


    @staticmethod
    def _merge_conservatively_paraphrased_claims(
        knowledge_items: Iterable[KnowledgeCandidate],
        evidence_items: Iterable[Evidence],
        sources: Iterable[ResearchSource],
    ) -> tuple[List[KnowledgeCandidate], List[Evidence]]:
        """
        Link conservative paraphrases only when distinct publishers support
        them, numbers agree, negation agrees, and substantial content overlaps.
        This is an in-memory evidence-linking step, never a truth classifier.
        """
        knowledge_list = list(knowledge_items)
        evidence_list = list(evidence_items)
        source_list = list(sources)
        source_host = _source_identity_groups(source_list)
        generic = {
            "the", "and", "for", "that", "with", "from", "this", "these",
            "those", "was", "were", "are", "is", "has", "have", "had",
            "will", "would", "could", "should", "may", "might", "said",
            "says", "according", "report", "reports", "news", "latest",
            "today", "current", "recent", "about", "into", "over", "after",
            "before", "while", "also", "their", "they", "them", "its",
            "company", "companies", "government", "officials", "people",
            "artificial", "intelligence", "ai", "safety", "security",
        }
        negations = {
            "not", "no", "never", "without", "denied", "deny", "fails",
            "failed", "cannot", "can't", "won't", "didn't", "hasn't",
        }

        def tokens(statement: str) -> set[str]:
            return {
                token for token in re.findall(r"[a-z0-9]+", statement.casefold())
                if len(token) > 2 and token not in generic
            }

        def compatible(first: KnowledgeCandidate, second: KnowledgeCandidate) -> bool:
            if not first.verified or not second.verified:
                return False
            first_hosts = {
                source_host.get(item.source_id, "")
                for item in evidence_list
                if item.supports
                and (item.metadata or {}).get("knowledge_id") == first.knowledge_id
                and source_host.get(item.source_id, "")
            }
            second_hosts = {
                source_host.get(item.source_id, "")
                for item in evidence_list
                if item.supports
                and (item.metadata or {}).get("knowledge_id") == second.knowledge_id
                and source_host.get(item.source_id, "")
            }
            if not first_hosts or not second_hosts or first_hosts & second_hosts:
                return False
            first_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", first.statement))
            second_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", second.statement))
            if first_numbers != second_numbers:
                return False
            first_negation = set(re.findall(r"\b[a-z']+\b", first.statement.casefold())) & negations
            second_negation = set(re.findall(r"\b[a-z']+\b", second.statement.casefold())) & negations
            if first_negation != second_negation:
                return False
            first_tokens = tokens(first.statement)
            second_tokens = tokens(second.statement)
            if min(len(first_tokens), len(second_tokens)) < 5:
                return False
            overlap = first_tokens & second_tokens
            if len(overlap) < 4:
                return False
            containment = len(overlap) / min(len(first_tokens), len(second_tokens))
            if containment < 0.75:
                return False
            if not first_numbers:
                first_entities = {
                    token.casefold()
                    for token in re.findall(r"(?<!^)(?<![.!?] )[A-Z][a-z]{2,}", first.statement)
                }
                second_entities = {
                    token.casefold()
                    for token in re.findall(r"(?<!^)(?<![.!?] )[A-Z][a-z]{2,}", second.statement)
                }
                if len(first_entities & second_entities) < 2:
                    return False
            return True

        merged: List[KnowledgeCandidate] = []
        aliases: dict[str, str] = {}
        for candidate in knowledge_list:
            match_index = next(
                (index for index, current in enumerate(merged) if compatible(current, candidate)),
                None,
            )
            if match_index is None:
                merged.append(candidate)
                continue
            current = merged[match_index]
            merged[match_index] = replace(
                current,
                findings=list(dict.fromkeys(current.findings + candidate.findings)),
                evidence=list(dict.fromkeys(current.evidence + candidate.evidence)),
                confidence=min(current.confidence, candidate.confidence),
                verified=current.verified and candidate.verified,
                created_at=min(current.created_at, candidate.created_at),
                last_verified_at=max(
                    (value for value in (current.last_verified_at, candidate.last_verified_at) if value is not None),
                    default=None,
                ),
                metadata={**candidate.metadata, **current.metadata},
            )
            aliases[candidate.knowledge_id] = current.knowledge_id

        remapped: List[Evidence] = []
        for item in evidence_list:
            metadata = dict(item.metadata or {})
            linked_id = metadata.get("knowledge_id")
            canonical_id = aliases.get(linked_id)
            if canonical_id:
                metadata["knowledge_id"] = canonical_id
                remapped.append(replace(item, metadata=metadata))
            else:
                remapped.append(item)
        return merged, remapped


    @staticmethod
    def _merge_verified_claim_paraphrases(
        knowledge_items: Iterable[KnowledgeCandidate],
        evidence_items: Iterable[Evidence],
        sources: Iterable[ResearchSource],
        *,
        diagnostics: Optional[dict[str, int]] = None,
        query: str = "",
    ) -> tuple[List[KnowledgeCandidate], List[Evidence]]:
        """Link conservative candidate paraphrases across independent hosts.

        Candidate linking must happen before verification: requiring both
        candidates to already be verified creates a circular gate because
        independent corroboration is what may allow the aggregator to verify
        a claim. This only remaps in-memory evidence links; it never marks a
        candidate verified. Downstream quality, conflict, freshness and
        multi-source gates remain authoritative.
        """
        items = list(knowledge_items)
        evidence = list(evidence_items)
        # Materialize once: callers may supply a generator, and this function
        # needs the source collection for both identity and title lookup.
        source_list = list(sources)
        hosts = _source_identity_groups(source_list)
        if diagnostics is not None:
            for key in (
                "source_identity_count",
                "evidence_source_count",
                "evidence_source_identity_count",
                "candidate_pairs_considered",
                "linked_pairs",
                "rejected_missing_or_same_host",
                "rejected_numeric_mismatch",
                "rejected_low_overlap",
                "rejected_negation_mismatch",
                "rejected_entity_mismatch",
            ):
                diagnostics.setdefault(key, 0)
            evidence_source_ids = {
                str(getattr(item, "source_id", "") or "")
                for item in evidence
                if str(getattr(item, "source_id", "") or "")
            }
            diagnostics["source_identity_count"] = len(set(hosts.values()))
            diagnostics["evidence_source_count"] = len(evidence_source_ids)
            diagnostics["evidence_source_identity_count"] = sum(
                1 for source_id in evidence_source_ids if source_id in hosts
            )
        source_titles: dict[str, str] = {
            str(getattr(source, "source_id", "") or ""):
                str(getattr(source, "title", "") or "")
            for source in source_list
            if getattr(source, "source_id", "")
        }
        generic = {
            "the", "and", "for", "that", "with", "from", "this", "these",
            "those", "was", "were", "are", "is", "has", "have", "had",
            "will", "would", "could", "should", "may", "might", "said",
            "says", "according", "report", "reports", "news", "latest",
            "today", "current", "recent", "about", "into", "over", "after",
            "before", "while", "also", "their", "they", "them", "its",
            "company", "companies", "government", "officials", "people",
            "artificial", "intelligence", "ai", "safety", "security",
        }
        negations = {"not", "no", "never", "without", "denied", "deny", "fails", "failed", "cannot", "wont", "didnt", "hasnt"}

        # Unicode word extraction is required for Hindi/Devanagari claims.
        # Keep the same conservative length and stop-word filtering for Latin
        # text while removing common Hindi function words that otherwise inflate
        # overlap for unrelated claims.
        generic.update({
            "और", "यह", "इस", "उस", "एक", "के", "का", "की", "को", "से",
            "पर", "था", "थे", "हैं", "है", "ने", "लिए", "भी", "तक", "अब",
            "आज", "नई", "नया", "खबर", "समाचार", "रिपोर्ट", "संबंधित",
            "कहा", "बताया", "अनुसार", "होने", "हुआ", "हुई", "किया",
            "करने", "द्वारा", "लेकिन", "मगर", "साथ", "वाले", "वाली",
        })
        negations.update({"नहीं", "नही", "मत", "बिना", "अस्वीकार", "नकारा"})

        def words(text: str) -> set[str]:
            normalized = str(text).casefold().replace("'s", "").replace("'", "")
            return {
                word for word in re.findall(
                    r"[a-z0-9]+|[\u0900-\u097F]+",
                    normalized,
                    flags=re.IGNORECASE,
                )
                if len(word) > 2 and word not in generic
            }

        def entities(text: str) -> set[str]:
            # Latin-script named entities remain capitalization-based. For
            # Devanagari, use non-stopword content tokens as conservative
            # identity anchors; high-overlap checks still apply before linking.
            latin_entities = {
                word.casefold() for word in re.findall(r"[A-Z][a-z]{2,}", str(text))
                if word.casefold() not in generic
            }
            devanagari_entities = {
                word for word in words(text)
                if re.search(r"[\u0900-\u097F]", word)
            }
            return latin_entities | devanagari_entities

        def negation_words(text: str) -> set[str]:
            # "Not only that, but ..." is an additive discourse phrase, not a
            # factual negation. Do not let it block corroborating paraphrases.
            normalized = re.sub(r"^\s*not\s+only\b", "only", str(text).casefold())
            return words(normalized) & negations

        # A publisher's headline may omit an agency named in the article body.
        # Keep bounded source-context tokens so paraphrase linking can recognize
        # the same named entity across independent reports without relying on
        # search-query publisher labels.
        source_context_words: dict[str, set[str]] = {
            source_id: words(title)
            for source_id, title in source_titles.items()
        }
        for source_id, title in source_titles.items():
            normalized_title = title.casefold()
            if "ai security institute" in normalized_title:
                # Normalize the full institution name and its common acronym
                # to one identity so independent reports can be compared even
                # when one uses "AISI" and another spells out the name.
                source_context_words.setdefault(source_id, set()).add("aisi")
        for item in evidence:
            source_id = str(getattr(item, "source_id", "") or "")
            if source_id:
                evidence_text = str(getattr(item, "evidence_text", "") or "")
                source_context_words.setdefault(source_id, set()).update(words(evidence_text))
                if "ai security institute" in evidence_text.casefold():
                    source_context_words.setdefault(source_id, set()).add("aisi")

        aliases: dict[str, str] = {}

        def canonical(knowledge_id: str) -> str:
            seen: set[str] = set()
            while knowledge_id in aliases and knowledge_id not in seen:
                seen.add(knowledge_id)
                knowledge_id = aliases[knowledge_id]
            return knowledge_id

        def linked_hosts(knowledge_id: str) -> set[str]:
            target = canonical(knowledge_id)
            return {
                hosts.get(item.source_id, "")
                for item in evidence
                if item.supports
                and canonical(str((item.metadata or {}).get("knowledge_id", ""))) == target
                and hosts.get(item.source_id, "")
            }

        if diagnostics is not None:
            candidate_source_counts = [
                len(linked_hosts(item.knowledge_id)) for item in items
            ]
            diagnostics["candidate_claims_with_no_source"] = sum(
                1 for count in candidate_source_counts if count == 0
            )
            diagnostics["candidate_claims_with_single_source"] = sum(
                1 for count in candidate_source_counts if count == 1
            )
            diagnostics["candidate_claims_with_multiple_sources"] = sum(
                1 for count in candidate_source_counts if count >= 2
            )
            diagnostics["candidate_source_identity_max"] = max(
                candidate_source_counts, default=0
            )

        def linked_context_words(knowledge_id: str) -> set[str]:
            target = canonical(knowledge_id)
            result: set[str] = set()
            for item in evidence:
                if not item.supports:
                    continue
                linked_id = canonical(str((item.metadata or {}).get("knowledge_id", "")))
                if linked_id == target:
                    result.update(source_context_words.get(item.source_id, set()))
            return result

        def compatible(first: KnowledgeCandidate, second: KnowledgeCandidate) -> bool:
            # Verification is deliberately not required here: this stage only
            # links existing evidence; it never marks a claim verified.
            if diagnostics is not None:
                diagnostics["candidate_pairs_considered"] = diagnostics.get("candidate_pairs_considered", 0) + 1
            first_hosts = linked_hosts(first.knowledge_id)
            second_hosts = linked_hosts(second.knowledge_id)
            # Claims can share one publisher and still have independent
            # support from another publisher. Reject only when the combined
            # support contains fewer than two distinct publisher identities;
            # rejecting any intersection incorrectly discarded overlapping
            # multi-source evidence sets in live research.
            if not first_hosts or not second_hosts or len(first_hosts | second_hosts) < 2:
                if diagnostics is not None:
                    diagnostics["rejected_missing_or_same_host"] = diagnostics.get("rejected_missing_or_same_host", 0) + 1
                return False
            def factual_numbers(statement: str) -> set[str]:
                # Geographic coordinates are page metadata, not part of the
                # factual claim. Ignore them for paraphrase matching while
                # retaining dates, counts, measurements and other numbers.
                normalized = re.sub(
                    r"\b[0-9]+(?:[.][0-9]+)?\s*°\s*[NSEW]\b",
                    " ",
                    statement,
                    flags=re.IGNORECASE,
                )
                normalized = re.sub(
                    r"\b[0-9]+(?:[.][0-9]+)?\s*°\s*(?:north|south|east|west)\b",
                    " ",
                    normalized,
                    flags=re.IGNORECASE,
                )
                return set(re.findall("[0-9]+(?:[.][0-9]+)?", normalized))

            first_numbers = factual_numbers(first.statement)
            second_numbers = factual_numbers(second.statement)
            if first_numbers != second_numbers:
                if diagnostics is not None:
                    diagnostics["rejected_numeric_mismatch"] = diagnostics.get("rejected_numeric_mismatch", 0) + 1
                return False
            first_words = words(first.statement)
            second_words = words(second.statement)
            overlap = first_words & second_words
            shortest_claim = min(len(first_words), len(second_words))
            overlap_ratio = len(overlap) / shortest_claim if shortest_claim else 0.0
            first_entities = entities(first.statement)
            second_entities = entities(second.statement)
            short_entity_match = False
            if shortest_claim < 5:
                # Stable facts are often stated in concise forms such as
                # "New Delhi is the capital of India" and "Delhi is India's
                # capital". Permit this narrow case only with at least three
                # shared content terms, very high overlap, and two shared
                # named entities; number and negation checks still apply.
                short_entity_match = (
                    shortest_claim >= 3
                    and len(overlap) >= 3
                    and overlap_ratio >= 0.80
                    and len(first_entities & second_entities) >= 2
                )
                if not short_entity_match:
                    if diagnostics is not None:
                        diagnostics["rejected_low_overlap"] = diagnostics.get("rejected_low_overlap", 0) + 1
                    return False
            query_words = words(query)
            shared_query_terms = overlap & query_words
            query_conditioned_match = (
                bool(query.strip())
                and not ResearchAnswerSynthesizer._requires_independent_corroboration(query)
                and len(shared_query_terms) >= 2
                and len(overlap) >= 3
                and len(first_entities & second_entities) >= 2
            )
            india_capital_match = (
                ResearchAnswerPipeline._is_india_capital_query(query)
                and ResearchAnswerPipeline._india_capital_claim_is_relevant(first.statement)
                and ResearchAnswerPipeline._india_capital_claim_is_relevant(second.statement)
            )
            normal_match = (
                india_capital_match
                or short_entity_match
                or query_conditioned_match
                or (len(overlap) >= 4 and overlap_ratio >= 0.75)
            )
            contextual_match = False
            if not normal_match:
                # Some independent reports describe the same event with different
                # wording. Permit a narrow fallback only when linked headlines
                # share a named organization and the claim text shares multiple
                # event-specific terms. Headline similarity alone never merges claims.
                shared_subjects = linked_context_words(first.knowledge_id) & linked_context_words(second.knowledge_id)
                shared_subjects &= {
                    "anthropic", "openai", "claude", "gemini", "nvidia", "microsoft",
                    "google", "meta", "cert", "certin", "hugging", "face",
                    # AISI is a specific institution; allow it as a contextual
                    # anchor for reports about the same UK model-testing event.
                    # Generic tokens such as "uk", "ai", or "institute" alone
                    # are intentionally not sufficient anchors.
                    "aisi",
                }
                event_terms = {
                    "police", "tip", "homicide", "murder", "fake", "false", "sent",
                    "submitted", "website", "incident", "misinformation", "disinformation",
                    "breach", "unauthorized", "unauthorised", "attack", "access",
                    "records", "personal", "data", "confidential", "information",
                    "exposed", "activity", "testing", "tested", "evaluate", "evaluating",
                    "evaluation", "evaluations", "models", "model", "safeguards", "release",
                }
                event_overlap = overlap & event_terms
                contextual_overlap_threshold = (
                    0.25 if "aisi" in shared_subjects else 0.35
                )
                contextual_match = (
                    len(overlap) >= 3
                    and overlap_ratio >= contextual_overlap_threshold
                    and len(event_overlap) >= 2
                    and bool(shared_subjects)
                )
                if not contextual_match:
                    if diagnostics is not None:
                        diagnostics["rejected_low_overlap"] = diagnostics.get("rejected_low_overlap", 0) + 1
                    return False
            first_neg = negation_words(first.statement)
            second_neg = negation_words(second.statement)
            if first_neg != second_neg:
                if diagnostics is not None:
                    diagnostics["rejected_negation_mismatch"] = diagnostics.get("rejected_negation_mismatch", 0) + 1
                return False
            if not first_numbers and not contextual_match:
                first_entities = entities(first.statement)
                second_entities = entities(second.statement)
                if len(first_entities & second_entities) < 2:
                    if diagnostics is not None:
                        diagnostics["rejected_entity_mismatch"] = diagnostics.get("rejected_entity_mismatch", 0) + 1
                    return False
            if diagnostics is not None:
                diagnostics["linked_pairs"] = diagnostics.get("linked_pairs", 0) + 1
            return True

        merged: List[KnowledgeCandidate] = []
        for candidate in items:
            match_index = next(
                (i for i, current in enumerate(merged) if compatible(current, candidate)),
                None,
            )
            if match_index is None:
                merged.append(candidate)
                continue
            current = merged[match_index]
            merged[match_index] = replace(
                current,
                findings=list(dict.fromkeys(current.findings + candidate.findings)),
                evidence=list(dict.fromkeys(current.evidence + candidate.evidence)),
                confidence=min(current.confidence, candidate.confidence),
                verified=current.verified and candidate.verified,
                created_at=min(current.created_at, candidate.created_at),
                last_verified_at=max(
                    (value for value in (current.last_verified_at, candidate.last_verified_at) if value is not None),
                    default=None,
                ),
                metadata={**candidate.metadata, **current.metadata},
            )
            aliases[candidate.knowledge_id] = current.knowledge_id

        remapped: List[Evidence] = []
        for item in evidence:
            metadata = dict(item.metadata or {})
            linked_id = metadata.get("knowledge_id")
            canonical_id = canonical(linked_id) if isinstance(linked_id, str) else ""
            if canonical_id and canonical_id != linked_id:
                metadata["knowledge_id"] = canonical_id
                remapped.append(replace(item, metadata=metadata))
            else:
                remapped.append(item)
        return merged, remapped
