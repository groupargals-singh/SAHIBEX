from __future__ import annotations

from dataclasses import dataclass, field, replace
import re
import queue
import threading
import time
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional


from core.research.acquisition import AcquisitionRequest
from core.research.acquisition_pipeline import ResearchAcquisitionPipeline
from core.research.answer_pipeline import (
    ResearchAnswerPipeline,
    ResearchAnswerPipelineResult,
)
from core.research.answer import ResearchAnswerSynthesizer
from core.research.freshness import assess_query_source_freshness
from core.research.extraction_pipeline import (
    ExtractionPipelineResult,
    ResearchExtractionPipeline,
)
from core.research.models import ResearchDocument
from core.research.research_executor import ResearchExecutor
from core.research.job import ResearchJob
from core.research.research_plan import ResearchPlan, ResearchStep
from core.research.storage import ResearchStorage
from core.research.provider_router import ResearchProviderRouter


# A DNS/redirect request can stall beyond urllib's socket timeout. Keep the
# number of in-flight aggregator resolutions bounded across research jobs.
_ACTIVE_REDIRECT_RESOLUTION_SLOTS = threading.BoundedSemaphore(4)
_REDIRECT_RESOLUTION_DEADLINE_SECONDS = 12.0


@dataclass
class ResearchPipelineContext:
    """
    Runtime state shared by research execution step handlers.
    """

    query: str
    acquisition: Any = None
    ingestion: Any = None
    extraction: List[ExtractionPipelineResult] = field(
        default_factory=list
    )
    verification: Any = None
    answer: Optional[ResearchAnswerPipelineResult] = None
    outputs: Dict[str, Any] = field(default_factory=dict)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "acquisition": self.acquisition,
            "ingestion": self.ingestion,
            "extraction": list(self.extraction),
            "verification": self.verification,
            "answer": self.answer,
            "outputs": dict(self.outputs),
        }


class ResearchPipelineIntegration:
    """
    Adapter connecting the generic research executor to the
    existing acquisition, extraction, verification, storage,
    and answer pipeline components.
    """

    integration_name = "default_research_pipeline_integration"

    STEP_SCOPE = "research-scope"
    STEP_ACQUISITION = "source-acquisition"
    STEP_EXTRACTION = "evidence-extraction"
    STEP_VERIFICATION = "verification"
    STEP_ANSWER = "answer-synthesis"

    def __init__(
        self,
        acquisition_pipeline: ResearchAcquisitionPipeline,
        extraction_pipeline: ResearchExtractionPipeline,
        answer_pipeline: ResearchAnswerPipeline,
        storage: ResearchStorage,
    ) -> None:
        if not isinstance(
            acquisition_pipeline,
            ResearchAcquisitionPipeline,
        ):
            raise TypeError(
                "acquisition_pipeline must be "
                "ResearchAcquisitionPipeline"
            )

        if not isinstance(
            extraction_pipeline,
            ResearchExtractionPipeline,
        ):
            raise TypeError(
                "extraction_pipeline must be "
                "ResearchExtractionPipeline"
            )

        if not isinstance(
            answer_pipeline,
            ResearchAnswerPipeline,
        ):
            raise TypeError(
                "answer_pipeline must be ResearchAnswerPipeline"
            )

        if not isinstance(storage, ResearchStorage):
            raise TypeError("storage must be ResearchStorage")

        self.acquisition_pipeline = acquisition_pipeline
        self.extraction_pipeline = extraction_pipeline

        self.provider_router = ResearchProviderRouter(
            self.acquisition_pipeline.acquisition_engine
        )

        self.answer_pipeline = answer_pipeline
        self.storage = storage

        self._contexts: Dict[str, ResearchPipelineContext] = {}

    def context_for(
        self,
        job_id: str,
    ) -> ResearchPipelineContext:
        if not isinstance(job_id, str) or not job_id.strip():
            raise ValueError("job_id must be a non-empty string")

        context = self._contexts.get(job_id)

        if context is None:
            raise KeyError(
                f"research context not found: {job_id}"
            )

        return context

    def create_context(
        self,
        job: ResearchJob,
    ) -> ResearchPipelineContext:
        if not isinstance(job, ResearchJob):
            raise TypeError("job must be ResearchJob")

        if job.job_id in self._contexts:
            raise RuntimeError(
                f"research context already exists: {job.job_id}"
            )

        context = ResearchPipelineContext(
            query=job.query,
        )

        self._contexts[job.job_id] = context

        return context

    def register_handlers(
        self,
        executor: ResearchExecutor,
    ) -> None:
        if not isinstance(executor, ResearchExecutor):
            raise TypeError("executor must be ResearchExecutor")

        executor.register_step_handler(
            self.STEP_SCOPE,
            self.handle_scope,
        )

        executor.register_step_handler(
            self.STEP_ACQUISITION,
            self.handle_acquisition,
        )

        executor.register_step_handler(
            self.STEP_EXTRACTION,
            self.handle_extraction,
        )

        executor.register_step_handler(
            self.STEP_VERIFICATION,
            self.handle_verification,
        )

        executor.register_step_handler(
            self.STEP_ANSWER,
            self.handle_answer,
        )

    def handle_scope(
        self,
        step: ResearchStep,
        job: ResearchJob,
        plan: ResearchPlan,
    ) -> Dict[str, Any]:
        context = self._contexts.get(job.job_id)

        if context is None:
            context = self.create_context(job)

        output = {
            "step": step.step_id,
            "job_id": job.job_id,
            "query": job.query,
            "plan_id": plan.plan_id,
            "status": "scoped",
        }

        context.outputs[self.STEP_SCOPE] = output

        return output

    @staticmethod
    def _headline_corroboration_query(title: str) -> str:
        """Build a bounded follow-up search from a discovered article headline."""
        headline = " ".join(str(title or "").split()).strip()
        if " | " in headline:
            headline = headline.split(" | ", 1)[0].strip()
        if " - " in headline:
            left, suffix = headline.rsplit(" - ", 1)
            if len(suffix.split()) <= 5:
                headline = left.strip()
        headline = headline[:160].strip(" -|:;,.")
        tokens = re.findall(
            r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*|[\u0900-\u097F]+",
            headline,
        )
        stopwords = {
            "a", "an", "and", "are", "as", "at", "by", "for", "from",
            "in", "into", "is", "of", "on", "or", "the", "to", "was",
            "were", "with", "says", "said", "latest", "news", "report",
            "reports", "today", "क्या", "और", "में", "के", "को", "का",
            "की", "है", "से", "पर", "आज", "नया", "नई",
        }
        keywords: list[str] = []
        seen: set[str] = set()
        for token in tokens:
            normalized = token.casefold()
            if (len(normalized) < 2 and not normalized.isdigit()) or normalized in stopwords or normalized in seen:
                continue
            keywords.append(token)
            seen.add(normalized)
            if len(keywords) >= 7:
                break
        if len(keywords) < 4:
            return ""
        # Concise terms let search engines find independent reports that use
        # different wording for the same event without inventing source claims.
        return " ".join([*keywords, "latest"])

    @classmethod
    def _select_headline_corroboration_sources(
        cls,
        sources: List[ResearchSource],
        *,
        limit: int = 5,
        query: str = "",
    ) -> list[ResearchSource]:
        """Choose bounded, topic-relevant headlines for corroboration searches."""
        selected: list[ResearchSource] = []
        seen_queries: set[str] = set()
        query_text = str(query or "").casefold()
        safety_topic = bool(cls._discovery_query_expansions(query_text))
        ai_terms = (" ai ", "artificial intelligence", "anthropic", "openai", "claude", "gemini")
        safety_terms = ("safety", "safe", "security", "risk", "threat", "misinformation", "disinformation", "incident", "researcher", "evaluation")
        for source in sources:
            title = str(getattr(source, "title", "") or "").casefold()
            if safety_topic:
                padded_title = f" {title} "
                if not any(term in padded_title for term in ai_terms) or not any(term in title for term in safety_terms):
                    continue
            query_text_from_title = cls._headline_corroboration_query(title)
            normalized = query_text_from_title.casefold()
            if not query_text_from_title or normalized in seen_queries:
                continue
            seen_queries.add(normalized)
            selected.append(source)
            if len(selected) >= limit:
                break
        return selected

    @staticmethod
    def _interleave_url_batches(batches: List[List[str]]) -> list[str]:
        """Round-robin independent query result batches to preserve coverage."""
        ordered: list[str] = []
        max_depth = max((len(batch) for batch in batches), default=0)
        for index in range(max_depth):
            for batch in batches:
                if index < len(batch):
                    url = batch[index]
                    if url not in ordered:
                        ordered.append(url)
        return ordered

    @staticmethod
    def _select_best_corroboration_batch(batches: List[List[str]]) -> list[str]:
        """Choose one event-search batch with the strongest publisher diversity."""
        aggregator_hosts = {
            "news.google.com", "news.yahoo.com", "consent.yahoo.com",
            "msn.com", "flipboard.com",
        }

        def score(batch: List[str]) -> tuple[int, int]:
            unique_urls = list(dict.fromkeys(
                url.strip() for url in batch
                if isinstance(url, str) and url.strip()
                and urlparse(url.strip()).scheme in {"http", "https"}
                and urlparse(url.strip()).hostname
            ))
            publishers = {
                (urlparse(url).hostname or "").casefold().removeprefix("www.")
                for url in unique_urls
                if (urlparse(url).hostname or "").casefold().removeprefix("www.")
                not in aggregator_hosts
            }
            # Prefer batches with more independent direct publishers; break ties
            # by candidate count. If all candidates are wrappers/aggregators, the
            # longest batch is retained for the safe resolver to inspect.
            return len(publishers), len(unique_urls)

        non_empty = [batch for batch in batches if batch]
        return list(max(non_empty, key=score)) if non_empty else []

    @staticmethod
    def _order_current_research_urls(
        discovered_urls: List[str],
        expansion_urls: List[str],
        corroboration_urls: List[str],
    ) -> list[str]:
        """Prioritize headline-specific follow-up candidates for current research.

        Broad discovery often returns one publisher per unrelated story.
        Headline follow-ups are interleaved across separate event queries and
        prioritized first so the selected pages can corroborate the same event.
        Topic expansions follow, then broad leads. This changes candidate order
        only; search results remain leads, not evidence, and no verification gate
        is relaxed.
        """
        return list(dict.fromkeys([
            *corroboration_urls,
            *expansion_urls,
            *discovered_urls,
        ]))

    @staticmethod
    def _prioritize_diverse_public_urls(urls: List[str], *, limit: int = 10) -> list[str]:
        """Prefer one public URL per publisher host before adding a second URL."""
        unique_urls = list(dict.fromkeys(
            url.strip() for url in urls
            if isinstance(url, str)
            and urlparse(url.strip()).scheme in {"http", "https"}
            and urlparse(url.strip()).hostname
        ))
        selected: list[str] = []
        seen_hosts: set[str] = set()
        remaining: list[str] = []
        aggregator_hosts = {
            "news.google.com", "news.yahoo.com", "consent.yahoo.com",
            "msn.com", "flipboard.com",
        }
        aggregator_urls: list[str] = []
        for url in unique_urls:
            host = (urlparse(url).hostname or "").casefold().removeprefix("www.")
            if host in aggregator_hosts:
                aggregator_urls.append(url)
                continue
            if host not in seen_hosts:
                selected.append(url)
                seen_hosts.add(host)
            else:
                remaining.append(url)
            if len(selected) >= limit:
                return selected[:limit]
        # Prefer direct publisher pages. Aggregator/syndication pages are only
        # fallback candidates when fewer direct publisher hosts were found.
        for url in aggregator_urls:
            host = (urlparse(url).hostname or "").casefold().removeprefix("www.")
            if host not in seen_hosts:
                selected.append(url)
                seen_hosts.add(host)
            if len(selected) >= limit:
                return selected[:limit]
        selected.extend(remaining[:max(0, limit - len(selected))])
        return selected[:limit]

    @classmethod
    def _resolve_and_prioritize_public_urls(
        cls,
        urls: List[str],
        *,
        source_by_url: Dict[str, Any],
        resolver,
        limit: int = 10,
        max_candidates: int = 20,
    ) -> tuple[list[str], dict[str, Any]]:
        """Resolve bounded news wrappers before selecting diverse publisher hosts."""
        raw_urls = list(dict.fromkeys(
            url.strip()
            for url in urls
            if isinstance(url, str) and url.strip()
        ))[:max_candidates]
        has_google_wrapper = any(
            (urlparse(url).hostname or "").casefold() == "news.google.com"
            for url in raw_urls
        )
        if has_google_wrapper and not callable(resolver):
            raise RuntimeError(
                "safe publisher-link resolver is unavailable; discovery links remain unverified"
            )

        # A single stale/broken aggregator wrapper must not abort the entire
        # research job. Resolve a small bounded batch concurrently, but preserve
        # original candidate order when selecting publishers. Every hop remains
        # validated inside the direct-web provider's resolver.
        def resolve_one(url: str) -> tuple[str, str] | None:
            hostname = (urlparse(url).hostname or "").casefold()
            if hostname != "news.google.com":
                resolved_url = url
            else:
                # A stalled resolver must not consume an unbounded worker for
                # every new query. A slot stays held until the real call exits.
                if not _ACTIVE_REDIRECT_RESOLUTION_SLOTS.acquire(blocking=False):
                    return None
                try:
                    resolved_url = resolver(url, max_hops=3)
                except Exception:
                    return None
                finally:
                    _ACTIVE_REDIRECT_RESOLUTION_SLOTS.release()
            if not isinstance(resolved_url, str):
                return None
            resolved_url = resolved_url.strip()
            parsed = urlparse(resolved_url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                return None
            # An unresolved wrapper remains discovery-only and cannot be evidence.
            if hostname == "news.google.com" and parsed.hostname.casefold() == "news.google.com":
                return None
            return url, resolved_url

        # Resolve direct publisher URLs first; aggregator URLs may require DNS
        # and redirect chains. Daemon workers plus one deadline prevent a stuck
        # OS resolver from blocking the entire research request. Timed-out URLs
        # are discarded, never promoted to evidence.
        work_queue: queue.Queue[tuple[int, str]] = queue.Queue()
        result_queue: queue.Queue[tuple[int, tuple[str, str] | None]] = queue.Queue()
        indexed_urls = list(enumerate(raw_urls))
        indexed_urls.sort(
            key=lambda item: (
                (urlparse(item[1]).hostname or "").casefold() == "news.google.com",
                item[0],
            )
        )
        for item in indexed_urls:
            work_queue.put(item)

        def resolve_worker() -> None:
            while True:
                try:
                    index, url = work_queue.get_nowait()
                except queue.Empty:
                    return
                try:
                    pair = resolve_one(url)
                except Exception:
                    pair = None
                result_queue.put((index, pair))
                work_queue.task_done()

        worker_count = min(4, len(raw_urls))
        for worker_index in range(worker_count):
            threading.Thread(
                target=resolve_worker,
                name=f"sahibex-url-resolver-{worker_index}",
                daemon=True,
            ).start()

        deadline = time.monotonic() + _REDIRECT_RESOLUTION_DEADLINE_SECONDS
        resolved_by_index: dict[int, tuple[str, str] | None] = {}
        while len(resolved_by_index) < len(raw_urls):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                index, pair = result_queue.get(timeout=remaining)
            except queue.Empty:
                break
            resolved_by_index[index] = pair

        resolved_urls: list[str] = []
        resolved_source_by_url: dict[str, Any] = {}
        for index in range(len(raw_urls)):
            pair = resolved_by_index.get(index)
            if pair is None:
                continue
            original_url, resolved_url = pair
            resolved_urls.append(resolved_url)
            source = source_by_url.get(original_url)
            if source is not None:
                resolved_source_by_url[resolved_url] = source

        unique_resolved = list(dict.fromkeys(resolved_urls))
        selected = cls._prioritize_diverse_public_urls(
            unique_resolved,
            limit=limit,
        )
        return selected, resolved_source_by_url

    def handle_acquisition(
        self,
        step: ResearchStep,
        job: ResearchJob,
        plan: ResearchPlan,
    ) -> Any:
        context = self.context_for(job.job_id)

        if not step.source_types:
            raise RuntimeError(
                "source-acquisition step has no source types"
            )

        source_type = step.source_types[0]

        # A generic web research job has no URL yet; use search discovery
        # first only when a real search backend is configured. An explicit
        # fail-closed search backend must not hijack local/test providers.
        search_available = False
        engine = self.acquisition_pipeline.acquisition_engine
        if "search" in engine.providers():
            search_provider = engine.get_provider("search")
            backend = getattr(search_provider, "backend", None)
            search_available = (
                getattr(backend, "backend_name", "")
                != "unconfigured_search"
            )

        if (
            source_type == "web"
            and search_available
            and not job.metadata.get("url")
            and not job.metadata.get("urls")
        ):
            source_type = "search"

        request = AcquisitionRequest(
            query=job.query,
            source_type=source_type,
        )

        provider_name = self.provider_router.provider_name(
            request
        )

        confirmation = bool(job.metadata.get("network_confirmation", False))

        # Search is discovery-only. Once NETWORK_ACCESS is approved,
        # immediately fetch the discovered public sources through the
        # hardened direct-web provider so downstream extraction and
        # verification operate on source content rather than snippets.
        if provider_name == "search":
            search_result = self.acquisition_pipeline.acquire_and_ingest(
                request,
                provider_name="search",
                confirmation=confirmation,
            )
            # Search results are discovery leads, not publisher evidence.
            # Keep them separately for a safe failure response, and clear their
            # ingestion records so extraction can never treat snippets as source
            # documents if publisher fetching fails.
            context.outputs["search_discovery_acquisition"] = search_result.acquisition
            context.acquisition = search_result.acquisition
            context.ingestion = []
            context.extraction = []
            # Start with the broad discovery set, then perform bounded
            # headline-specific searches for current queries. Broad search
            # often returns several unrelated single-source stories; follow-up
            # discovery gives each lead a chance to find independent coverage.
            discovered_sources = list(search_result.acquisition.sources)
            candidate_sources = list(discovered_sources)
            discovered_urls = [
                source.locator for source in discovered_sources if source.locator
            ]
            expansion_candidate_urls: list[str] = []
            expansion_candidate_url_batches: list[list[str]] = []
            corroboration_candidate_urls: list[str] = []
            corroboration_candidate_url_batches: list[list[str]] = []
            expansion_attempts: list[str] = []
            expansion_failures: list[str] = []
            for expanded_query in self._discovery_query_expansions(job.query)[:2]:
                expansion_attempts.append(expanded_query)
                try:
                    expanded_result = self.acquisition_pipeline.acquire_and_ingest(
                        AcquisitionRequest(
                            query=expanded_query,
                            source_type="search",
                            max_sources=5,
                        ),
                        provider_name="search",
                        confirmation=confirmation,
                    )
                    candidate_sources.extend(expanded_result.acquisition.sources)
                    expansion_batch = [
                        item.locator
                        for item in expanded_result.acquisition.sources
                        if item.locator
                    ]
                    expansion_candidate_url_batches.append(expansion_batch)
                    expansion_candidate_urls.extend(expansion_batch)
                except Exception as exc:
                    expansion_failures.append(
                        f"{expanded_query[:100]}: {str(exc)[:160]}"
                    )

            expansion_candidate_urls = self._interleave_url_batches(
                expansion_candidate_url_batches
            )
            followup_attempts: list[str] = []
            followup_failures: list[str] = []
            if ResearchAnswerSynthesizer._requires_independent_corroboration(job.query):
                # Search a small set of headline candidates, then choose one
                # event batch by publisher diversity below. Never interleave
                # different events into a single evidence candidate set.
                for source in self._select_headline_corroboration_sources(
                    candidate_sources,
                    limit=3,
                    query=job.query,
                ):
                    followup_query = self._headline_corroboration_query(source.title)
                    if not followup_query:
                        continue
                    followup_attempts.append(followup_query)
                    try:
                        followup_result = self.acquisition_pipeline.acquire_and_ingest(
                            AcquisitionRequest(
                                query=followup_query,
                                source_type="search",
                                max_sources=10,
                            ),
                            provider_name="search",
                            confirmation=confirmation,
                        )
                        candidate_sources.extend(followup_result.acquisition.sources)
                        corroboration_batch = [
                            item.locator
                            for item in followup_result.acquisition.sources
                            if item.locator
                        ]
                        corroboration_candidate_url_batches.append(corroboration_batch)
                        corroboration_candidate_urls.extend(corroboration_batch)
                    except Exception as exc:
                        # A failed corroboration search must not discard the
                        # original leads or weaken the downstream evidence gate.
                        followup_failures.append(
                            f"{followup_query[:120]}: {str(exc)[:160]}"
                        )

            requires_corroboration = (
                ResearchAnswerSynthesizer._requires_independent_corroboration(
                    job.query
                )
            )
            corroboration_candidate_urls = self._interleave_url_batches(
                corroboration_candidate_url_batches
            )
            candidate_urls = [
                *discovered_urls,
                *expansion_candidate_urls,
                *corroboration_candidate_urls,
            ]
            # For stable factual queries, place explicitly mapped cross-language
            # discovery leads first. Otherwise the initial Hindi results can
            # consume the bounded URL budget before the English equivalents are
            # considered, defeating the expansion and leaving claims un-linkable.
            # These remain ordinary untrusted leads; every downstream evidence
            # and verification gate is unchanged.
            if not requires_corroboration and expansion_candidate_urls:
                candidate_urls = [*expansion_candidate_urls, *discovered_urls]
            selected_corroboration_batch: list[str] = []
            corroboration_batches_to_try: list[list[str]] = []
            if requires_corroboration:
                followup_batches = [
                    batch for batch in corroboration_candidate_url_batches if batch
                ]
                expansion_batches = [
                    batch for batch in expansion_candidate_url_batches if batch
                ]
                selected_batch_type = "headline_followup"
                if followup_batches:
                    selected_corroboration_batch = (
                        self._select_best_corroboration_batch(followup_batches)
                    )
                elif expansion_batches:
                    selected_batch_type = "topic_expansion"
                    selected_corroboration_batch = (
                        self._select_best_corroboration_batch(expansion_batches)
                    )
                else:
                    selected_batch_type = "broad_discovery_fallback"
                    selected_corroboration_batch = list(discovered_urls)
                alternate_batches = (
                    followup_batches if followup_batches else expansion_batches
                )
                corroboration_batches_to_try = [
                    selected_corroboration_batch,
                    *[
                        batch for batch in alternate_batches
                        if batch and batch != selected_corroboration_batch
                    ],
                ]
                if discovered_urls and selected_corroboration_batch != discovered_urls:
                    corroboration_batches_to_try.append(list(discovered_urls))
                # Current-event claims must be corroborated within one event
                # query. Mixing batches from unrelated headlines creates false
                # candidate pairs or leaves every claim single-source. Broad
                # leads remain discovery metadata and are not silently merged
                # into the evidence set for the selected event.
                candidate_urls = list(selected_corroboration_batch)
                context.outputs["corroboration_batch_selection"] = {
                    "type": selected_batch_type,
                    "candidate_count": len(candidate_urls),
                    "available_followup_batches": len(followup_batches),
                    "available_expansion_batches": len(expansion_batches),
                }
            # Preserve discovery metadata before resolving wrappers. Google News
            # links all share one host, so diversity must be selected only after
            # safe resolution to the actual publisher URLs.
            candidate_source_by_url = {
                source.locator: source
                for source in candidate_sources
                if getattr(source, "locator", None)
            }
            direct_provider = (
                engine.get_provider("direct_web")
                if "direct_web" in engine.providers()
                else None
            )
            resolver = getattr(direct_provider, "resolve_redirect_url", None)
            urls, resolved_source_by_url = self._resolve_and_prioritize_public_urls(
                candidate_urls,
                source_by_url=candidate_source_by_url,
                resolver=resolver,
                # Current-news requests inspect a wider but still bounded
                # candidate set so stale/short pages do not exhaust the whole
                # evidence budget. Stable queries keep the smaller phone-safe cap.
                # Evidence thresholds are unchanged; this never promotes snippets.
                limit=5 if requires_corroboration else 3,
                max_candidates=20 if requires_corroboration else 10,
            )
            if requires_corroboration and not urls:
                # A selected headline batch can consist entirely of unresolved
                # Google News wrappers. Try alternate event-query batches one
                # at a time; never combine unrelated headlines into one evidence
                # set, and never promote an unresolved wrapper to a publisher.
                for alternate_batch in corroboration_batches_to_try[1:]:
                    if not alternate_batch:
                        continue
                    alternate_urls, alternate_sources = (
                        self._resolve_and_prioritize_public_urls(
                            alternate_batch,
                            source_by_url=candidate_source_by_url,
                            resolver=resolver,
                            limit=5,
                            max_candidates=20,
                        )
                    )
                    if alternate_urls:
                        candidate_urls = list(alternate_batch)
                        urls = alternate_urls
                        resolved_source_by_url = alternate_sources
                        selection = context.outputs.get(
                            "corroboration_batch_selection", {}
                        )
                        selection["type"] = f"{selection.get('type', 'event')}_fallback"
                        selection["candidate_count"] = len(candidate_urls)
                        selection["fallback_used"] = True
                        break
            discovery_metadata_by_url: dict[str, dict[str, object]] = {}

            # RSS timestamps are discovery metadata only. Use them only for an
            # exact resolved URL and an allow-listed backend; publisher page
            # content is still fetched and required as the actual evidence.
            for url in urls:
                source = (
                    resolved_source_by_url.get(url)
                    or candidate_source_by_url.get(url)
                )
                if source is None or source.published_at is None:
                    continue
                source_metadata = dict(source.metadata or {})
                backend = str(source_metadata.get("backend", ""))
                if backend in {"google_news_rss", "bing_news_rss", "brave_search"}:
                    discovery_metadata_by_url[url] = {
                        "published_at": str(source.published_at),
                        "backend": backend,
                        "discovery_only": bool(source_metadata.get("discovery_only", True)),
                    }

            context.outputs["corroboration_discovery"] = {
                "attempted_queries": followup_attempts,
                "failed_queries": followup_failures,
                "expansion_queries": expansion_attempts,
                "expansion_failures": expansion_failures,
                "candidate_url_count": len(list(dict.fromkeys(candidate_urls))),
                "resolved_candidate_url_count": len(resolved_source_by_url),
                "selected_diverse_url_count": len(urls),
                "selected_publisher_hosts": sorted({
                    (urlparse(url).hostname or "").casefold().removeprefix("www.")
                    for url in urls
                })[:10],
            }
            if not urls:
                raise RuntimeError("search provider returned no source URLs")

            direct_request = AcquisitionRequest(
                query=job.query,
                source_type="web",
                max_sources=len(urls),
                metadata={
                    "urls": urls,
                    "discovery_metadata_by_url": discovery_metadata_by_url,
                },
            )
            context.outputs["discovery_timestamp_provenance"] = {
                "candidate_sources_with_timestamp": sum(
                    1 for source in candidate_sources if source.published_at is not None
                ),
                "selected_urls_with_timestamp": len(discovery_metadata_by_url),
                "selected_urls_with_trusted_backend": sum(
                    1 for value in discovery_metadata_by_url.values()
                    if value.get("backend") in {"google_news_rss", "bing_news_rss", "brave_search"}
                    and value.get("discovery_only") is True
                ),
            }
            result = self.acquisition_pipeline.acquire_and_ingest(
                direct_request,
                provider_name="direct_web",
                confirmation=confirmation,
            )
            # Replace discovery-only context immediately after publisher fetch.
            # If no publisher pages survive validation, downstream extraction
            # must see zero ingested documents, never the search snippets.
            context.acquisition = result.acquisition
            context.ingestion = result.ingested
            context.outputs["publisher_fetch"] = {
                "status": result.acquisition.status,
                "requested": result.acquisition.metadata.get("requested_sources"),
                "acquired": result.acquisition.metadata.get("acquired_sources"),
                "details": list(result.acquisition.metadata.get("errors", ()))[:20],
            }
            if not result.acquisition.sources:
                # Keep the original discovery result in context so the final
                # fail-closed response can still show unverified leads. Preserve
                # sanitized acquisition diagnostics in the job failure so a live
                # failure identifies the actual stage rather than only saying
                # that evidence was insufficient. Do not include page bodies,
                # authorization headers, or secrets in this diagnostic.
                acquisition_meta = result.acquisition.metadata or {}
                acquisition_errors = list(acquisition_meta.get("errors", ()))[:8]
                diagnostic = {
                    "status": result.acquisition.status,
                    "requested": acquisition_meta.get("requested_sources"),
                    "acquired": acquisition_meta.get("acquired_sources"),
                    "error_count": len(acquisition_errors),
                    "errors": [str(error)[:180] for error in acquisition_errors],
                }
                raise RuntimeError(
                    "no publisher pages passed acquisition and freshness checks; "
                    "search results remain unverified discovery leads; "
                    f"acquisition_diagnostic={diagnostic}"
                )
            result.acquisition.metadata["search_discovery_count"] = len(urls)
            result.acquisition.metadata["search_backend"] = (
                search_result.acquisition.metadata.get("backend")
            )
        else:
            result = self.acquisition_pipeline.acquire_and_ingest(
                request,
                provider_name=provider_name,
                confirmation=confirmation,
            )

        context.acquisition = result.acquisition
        context.ingestion = result.ingested
        context.outputs[self.STEP_ACQUISITION] = result

        return result

    def handle_extraction(
        self,
        step: ResearchStep,
        job: ResearchJob,
        plan: ResearchPlan,
    ) -> Any:
        context = self.context_for(job.job_id)

        if context.acquisition is None:
            raise RuntimeError(
                "source acquisition must complete before extraction"
            )

        if not context.ingestion:
            raise RuntimeError(
                "source acquisition produced no ingested documents"
            )

        results: List[ExtractionPipelineResult] = []

        for ingestion_result in context.ingestion:
            document = self.storage.get_document(
                ingestion_result.document_id
            )

            if document is None:
                raise RuntimeError(
                    "ingested document not found: "
                    f"{ingestion_result.document_id}"
                )

            if not document.content:
                continue

            result = self.extraction_pipeline.extract_and_verify(
                document
            )

            results.append(result)

        context.extraction = results
        context.outputs[self.STEP_EXTRACTION] = results

        return results

    def handle_verification(
        self,
        step: ResearchStep,
        job: ResearchJob,
        plan: ResearchPlan,
    ) -> Dict[str, Any]:
        context = self.context_for(job.job_id)

        if not context.extraction:
            raise RuntimeError(
                "evidence extraction must complete before verification"
            )

        extracted_count = 0
        finding_count = 0
        evidence_count = 0

        for result in context.extraction:
            extracted_count += result.extracted_count
            finding_count += len(result.findings)

            for finding_result in result.findings:
                if finding_result.evidence_stored:
                    evidence_count += 1

        output = {
            "step": step.step_id,
            "job_id": job.job_id,
            "documents": len(context.extraction),
            "extracted_count": extracted_count,
            "finding_count": finding_count,
            "evidence_count": evidence_count,
            # An extraction pass with zero persisted evidence is not a
            # successful verification. Report the missing-evidence state
            # explicitly so callers cannot mistake an empty result for proof.
            # This step only confirms that evidence records were persisted.
            # It does not establish the truth of any claim; claim verification
            # remains downstream in the knowledge/aggregation/answer gates.
            "status": (
                "evidence_available"
                if evidence_count > 0
                else "insufficient_evidence"
            ),
            "truth_status": "not_evaluated",
        }

        context.verification = output
        context.outputs[self.STEP_VERIFICATION] = output

        return output

    def handle_answer(
        self,
        step: ResearchStep,
        job: ResearchJob,
        plan: ResearchPlan,
    ) -> ResearchAnswerPipelineResult:
        context = self.context_for(job.job_id)

        if not context.extraction:
            raise RuntimeError(
                "evidence extraction must complete before answer synthesis"
            )

        # Research answers must be grounded in evidence acquired for this job.
        # Do not fall back to unrelated previously stored knowledge when this
        # job produced no persisted evidence.
        if (
            not isinstance(context.verification, dict)
            or context.verification.get("status") != "evidence_available"
            or context.verification.get("evidence_count", 0) <= 0
        ):
            raise RuntimeError(
                "answer synthesis blocked: insufficient persisted evidence"
            )

        evidence_items = []
        sources = []

        for extraction_result in context.extraction:
            for finding_result in extraction_result.findings:
                evidence = self.storage.get_evidence(
                    finding_result.evidence_id
                )

                if evidence is not None:
                    evidence_items.append(evidence)

                source = self.storage.get_source(
                    finding_result.source_id
                )

                if source is not None:
                    sources.append(source)

        if not evidence_items:
            raise RuntimeError(
                "answer synthesis blocked: persisted evidence could not be loaded"
            )

        unique_sources = {
            source.source_id: source
            for source in sources
        }

        if not unique_sources:
            raise RuntimeError(
                "answer synthesis blocked: source traceability is unavailable"
            )

        answer = self.answer_pipeline.run(
            job.query,
            verified_only=True,
            evidence_items=evidence_items,
            sources=list(unique_sources.values()),
            focus_on_provided_evidence=True,
        )

        freshness_gate = assess_query_source_freshness(
            job.query, list(unique_sources.values())
        )
        if freshness_gate is not None:
            context.outputs["current_news_freshness_gate"] = freshness_gate
            if freshness_gate.get("status") != "PASS" and getattr(answer.answer, "verified", False):
                # Claim verification is not enough for current news: the actual
                # final answer object must fail closed when source dates are
                # stale/unknown. Keep no stale claim in the user-facing answer.
                rejected_answer = replace(
                    answer.answer,
                    answer="No sufficiently supported fresh evidence was available for this current-news query.",
                    confidence=0.0,
                    verified=False,
                    status="STALE",
                    evidence=[],
                    knowledge_ids=[],
                )
                rejected_arbitration = replace(
                    answer.arbitration,
                    status="REJECTED",
                    accepted=False,
                    reasons=tuple(dict.fromkeys(
                        tuple(getattr(answer.arbitration, "reasons", ()) or ())
                        + ("current_news_freshness_gate_rejected",)
                    )),
                )
                answer = replace(
                    answer,
                    answer=rejected_answer,
                    arbitration=rejected_arbitration,
                )

        context.answer = answer
        context.outputs[self.STEP_ANSWER] = answer

        return answer

    def has_context(self, job_id: str) -> bool:
        return job_id in self._contexts

    def context_ids(self) -> list[str]:
        return list(self._contexts.keys())

    def count_contexts(self) -> int:
        return len(self._contexts)

    def remove_context(self, job_id: str) -> None:
        if job_id not in self._contexts:
            raise KeyError(
                f"research context not found: {job_id}"
            )

        del self._contexts[job_id]

    def close(self) -> None:
        self.storage.close()


    @staticmethod
    def _discovery_query_expansions(query: str) -> list[str]:
        """Add a small, explicit set of English variants for known Hindi intents.

        Expansions improve recall only. Their results remain untrusted discovery
        leads and must pass the normal publisher acquisition, independent-source,
        claim-linking, freshness, and arbitration gates before answering.
        """
        text = " ".join(str(query or "").casefold().split())
        has_devanagari = any(0x0900 <= ord(char) <= 0x097F for char in text)
        if not has_devanagari:
            return []

        # The stable capital-of-India question is a common Hindi query for which
        # Hindi/English publisher claims were not being linked across languages.
        asks_capital = any(term in text for term in ("राजधानी", "capital"))
        about_india = any(term in text for term in ("भारत", "india", "नई दिल्ली", "new delhi"))
        if asks_capital and about_india:
            return ["capital of India", "New Delhi capital of India"]

        has_ai = "ai" in text or "कृत्रिम बुद्धिमत्ता" in text
        has_safety = any(term in text for term in (
            "सुरक्षा", "खतरा", "साइबर", "safety", "security", "cyber",
        ))
        if has_ai and has_safety:
            return ["latest AI safety news", "latest AI security news"]
        return []
