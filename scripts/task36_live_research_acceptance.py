"""Opt-in live-source acceptance for the SAHIBEX research pipeline.

This is deliberately separate from pytest: it uses the real network and can
fail when publishers are unavailable, pages move, or feeds change. It never
weakens the evidence/verification thresholds. Network access is explicitly
confirmed only for this user-invoked acceptance run.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import sys

# Support direct invocation as `python scripts/task36_live_research_acceptance.py`.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.research.answer_pipeline import ResearchAnswerPipeline
from core.research.acquisition_pipeline import ResearchAcquisitionPipeline
from core.research.engine import ResearchEngine
from core.research.freshness import STATUS_FRESH, assess_source_freshness
from core.research.extraction_pipeline import ResearchExtractionPipeline
from core.research.job import ResearchJob
from core.research.models import ResearchSource
from core.research.query import ResearchQueryEngine
from core.research.research_execution import ResearchExecutionRequest
from core.research.research_executor import ResearchExecutor
from core.research.research_pipeline_integration import ResearchPipelineIntegration
from core.research.research_plan import ResearchPlan, ResearchStep
from core.research.runtime_providers import build_default_research_acquisition_engine
from core.brain.universal_language_brain import UniversalLanguageBrain
from core.brain.translation_adapter import MyMemoryTranslationAdapter


def _safe_source(source) -> dict[str, object]:
    return {
        "title": str(source.title)[:180],
        "url": str(source.locator),
        "domain": urlparse(str(source.locator)).hostname,
        "publisher": source.publisher,
        "published_at": str(source.published_at) if source.published_at else None,
        "content_chars": len(str(source.content or "")),
        "content_hash": (source.metadata or {}).get("content_hash"),
        "publication_timestamp_source": (source.metadata or {}).get("publication_timestamp_source"),
    }


def assess_acceptance_freshness(
    sources,
    *,
    requires_publication_dates: bool,
    max_age_seconds: float | None = None,
    reference_time: datetime | None = None,
) -> tuple[list[dict[str, object]], dict[str, bool]]:
    """Return auditable freshness evidence and fail-closed acceptance checks."""
    if requires_publication_dates and max_age_seconds is None:
        max_age_seconds = 7 * 24 * 60 * 60
    reference = reference_time or datetime.now(timezone.utc)
    assessments: list[dict[str, object]] = []
    for source in sources:
        try:
            freshness_source = source
            if not isinstance(source, ResearchSource):
                try:
                    declared_reliability = float(getattr(source, "reliability", 0.0) or 0.0)
                except (TypeError, ValueError):
                    declared_reliability = 0.0
                freshness_source = ResearchSource(
                    source_id=str(getattr(source, "source_id", "") or ""),
                    title=str(getattr(source, "title", "") or getattr(source, "source_id", "") or "Untitled source"),
                    source_type=str(getattr(source, "source_type", "web") or "web"),
                    locator=str(getattr(source, "locator", "") or ""),
                    publisher=getattr(source, "publisher", None),
                    author=getattr(source, "author", None),
                    published_at=getattr(source, "published_at", None),
                    accessed_at=getattr(source, "accessed_at", reference),
                    reliability=max(0.0, min(1.0, declared_reliability)),
                    metadata=dict(getattr(source, "metadata", {}) or {}),
                )
            assessment = assess_source_freshness(freshness_source, reference_time=reference)
            assessments.append({
                "source_id": str(getattr(source, "source_id", "")),
                "published_at": str(source.published_at) if source.published_at else None,
                "age_seconds": assessment.age_seconds,
                "freshness_score": assessment.freshness_score,
                "status": assessment.status,
                "assessment_error": None,
            })
        except (TypeError, ValueError, AttributeError) as exc:
            assessments.append({
                "source_id": str(getattr(source, "source_id", "")),
                "published_at": str(getattr(source, "published_at", None)),
                "age_seconds": None,
                "freshness_score": 0.0,
                "status": "INVALID",
                "assessment_error": f"{type(exc).__name__}: {str(exc)[:180]}",
            })
    checks = {
        "source_freshness_assessed": (
            bool(sources)
            and len(assessments) == len(sources)
            and all(item["assessment_error"] is None for item in assessments)
        ),
        "current_query_sources_fresh": (
            not requires_publication_dates
            or (
                bool(assessments)
                and max_age_seconds is not None
                and all(
                    item["status"] == STATUS_FRESH
                    and item["age_seconds"] is not None
                    and item["age_seconds"] <= max_age_seconds
                    for item in assessments
                )
            )
        ),
    }
    return assessments, checks


def main() -> int:
    query = os.environ.get(
        "SAHIBEX_TASK36_QUERY",
        "latest AI safety security news today",
    ).strip()
    if not query:
        raise ValueError("SAHIBEX_TASK36_QUERY must not be empty")
    query_lower = query.casefold()
    requires_publication_dates = any(
        marker in query_lower
        for marker in ("latest", "today", "current", "news", "recent", "this week", "आज", "ताज़ा", "ताजा", "हालिया")
    )
    # Query wording sets the maximum acceptable source age: "today" must not
    # silently pass sources published several days ago.
    if any(marker in query_lower for marker in ("today", "this morning", "आज", "आज सुबह")):
        freshness_max_age_seconds = 24 * 60 * 60
    elif requires_publication_dates:
        freshness_max_age_seconds = 7 * 24 * 60 * 60
    else:
        freshness_max_age_seconds = None

    # This setting is scoped to this process; it does not alter the user's shell.
    os.environ.setdefault("SAHIBEX_SEARCH_BACKEND", "google_news_rss")
    started = time.monotonic()
    report: dict[str, object] = {
        "task": 36,
        "name": "real-source live research acceptance",
        "query": query,
        "requires_explicit_publication_dates": requires_publication_dates,
        "freshness_max_age_seconds": freshness_max_age_seconds,
        "started_at_epoch": time.time(),
        "network_permission": "explicit confirmation for this acceptance run",
        "checks": {},
    }
    integration = None
    job_id = "task36-live-acceptance"

    try:
        with tempfile.TemporaryDirectory(prefix="sahibex_task36_") as temp_dir:
            acquisition_engine, provider_status = build_default_research_acquisition_engine(
                project_root=Path.cwd()
            )
            report["runtime_provider_status"] = {
                "providers": list(provider_status.providers),
                "search_backend": provider_status.search_backend,
                "brave_configured": provider_status.brave_configured,
            }
            if "search" not in provider_status.providers:
                raise RuntimeError(
                    "No live search backend is configured. Set SAHIBEX_SEARCH_BACKEND=google_news_rss or configure a supported provider."
                )

            research_engine = ResearchEngine()
            acquisition = ResearchAcquisitionPipeline(
                Path(temp_dir) / "task36_live.db",
                acquisition_engine,
                engine=research_engine,
            )
            ingestion = acquisition.ingestion_pipeline
            storage = ingestion.storage
            extraction = ResearchExtractionPipeline(ingestion)
            query_engine = ResearchQueryEngine(research_engine, storage)
            answer_pipeline = ResearchAnswerPipeline(query_engine)
            integration = ResearchPipelineIntegration(
                acquisition_pipeline=acquisition,
                extraction_pipeline=extraction,
                answer_pipeline=answer_pipeline,
                storage=storage,
            )
            stage_timings: dict[str, float] = {}
            for handler_name in ("handle_scope", "handle_acquisition", "handle_extraction", "handle_verification", "handle_answer"):
                original_handler = getattr(integration, handler_name)
                def timed_handler(*args, _name=handler_name, _handler=original_handler, **kwargs):
                    stage_started = time.monotonic()
                    try:
                        return _handler(*args, **kwargs)
                    finally:
                        stage_timings[_name] = round(time.monotonic() - stage_started, 3)
                setattr(integration, handler_name, timed_handler)
            executor = ResearchExecutor()
            integration.register_handlers(executor)

            job = ResearchJob(
                job_id=job_id,
                query=query,
                metadata={"network_confirmation": True},
            )
            job.plan()
            job.start()
            plan = ResearchPlan(
                plan_id="task36-live-plan",
                job_id=job_id,
                objective=query,
                steps=[
                    ResearchStep("research-scope", "Scope live-source research"),
                    ResearchStep("source-acquisition", "Discover and fetch live publishers", source_types=["web"]),
                    ResearchStep("evidence-extraction", "Extract source-linked evidence"),
                    ResearchStep("verification", "Check persisted evidence"),
                    ResearchStep("answer-synthesis", "Synthesize source-traceable answer"),
                ],
            )
            request = ResearchExecutionRequest(
                execution_id="task36-live-execution",
                job_id=job_id,
                plan_id=plan.plan_id,
                metadata={"acceptance_test": True},
            )
            execution = executor.execute(job, plan, request)
            context = integration.context_for(job_id) if integration.has_context(job_id) else None

            checks = report["checks"]
            report["stage_timings_seconds"] = stage_timings
            report["stage_budgets_seconds"] = {
                "handle_scope": 2.0,
                "handle_acquisition": 120.0,
                "handle_extraction": 30.0,
                "handle_verification": 30.0,
                "handle_answer": 30.0,
                "total_execution": 180.0,
                "publisher_pages": 12,
            }
            checks["stage_latency_budgets"] = (
                len(stage_timings) == 5
                and all(stage_timings.get(name, float("inf")) <= budget
                        for name, budget in report["stage_budgets_seconds"].items()
                        if name in stage_timings)
            )
            checks["total_time_budget"] = (time.monotonic() - started) <= report["stage_budgets_seconds"]["total_execution"]
            checks["execution_completed"] = execution.status == "completed"
            checks["all_required_steps_completed"] = execution.status == "completed" and len(execution.completed_steps) == len(plan.steps)
            report["execution"] = {
                "status": execution.status,
                "completed_steps": execution.completed_steps,
                "failed_step": execution.failed_step,
                "error": execution.error,
            }

            if context is not None:
                for key in (
                    "corroboration_discovery",
                    "publisher_fetch",
                    "discovery_timestamp_provenance",
                    "corroboration_batch_selection",
                    "current_news_freshness_gate",
                ):
                    if key in context.outputs:
                        report[key] = context.outputs[key]
                acquisition_result = context.acquisition
                sources = list(acquisition_result.sources) if acquisition_result else []
                report["publisher_sources"] = [_safe_source(source) for source in sources]
                checks["publisher_page_count_budget"] = len(sources) <= report["stage_budgets_seconds"]["publisher_pages"]
                domains = {
                    (urlparse(str(source.locator)).hostname or "").casefold().removeprefix("www.")
                    for source in sources
                }
                checks["publisher_content_fetched"] = bool(sources) and all(
                    len(str(source.content or "").strip()) >= 160
                    and not bool((source.metadata or {}).get("discovery_only"))
                    for source in sources
                )
                checks["multiple_distinct_domains"] = len(domains) >= 2
                checks["explicit_publication_dates"] = (
                    not requires_publication_dates
                    or (bool(sources) and all(source.published_at is not None for source in sources))
                )
                # A timestamp being present is not itself a freshness check.
                source_freshness, freshness_checks = assess_acceptance_freshness(
                    sources,
                    requires_publication_dates=requires_publication_dates,
                    max_age_seconds=freshness_max_age_seconds,
                )
                report["source_freshness"] = source_freshness
                checks.update(freshness_checks)
                report["distinct_publisher_domains"] = sorted(domains)
                report["verification"] = context.verification
                report["evidence_count"] = sum(
                    len(result.findings) for result in context.extraction
                )
                report["extracted_finding_samples"] = [
                    {
                        "source_id": str(getattr(result, "source_id", "")),
                        "claims": [
                            str(getattr(finding, "claim", ""))[:180]
                            for finding in list(getattr(result, "findings", ()) or ())[:3]
                        ],
                    }
                    for result in list(context.extraction)[:5]
                ]
                if context.answer is not None:
                    answer = context.answer
                    query_result = getattr(answer, "query_result", None)
                    query_matches = list(getattr(query_result, "matches", ()) or ())
                    report["retrieval_candidates"] = [
                        {
                            "knowledge_id": str(getattr(item, "knowledge_id", "")),
                            "statement": str(getattr(item, "statement", ""))[:240],
                            "confidence": getattr(item, "confidence", None),
                            "verified": getattr(item, "verified", None),
                            "evidence_count": len(getattr(item, "evidence", ()) or ()),
                        }
                        for item in query_matches[:20]
                    ]
                    query_terms = [term for term in ("capital", "india", "delhi") if term in query.casefold()]
                    if query_terms:
                        report["query_relevant_candidates"] = [
                            {
                                "knowledge_id": str(getattr(item, "knowledge_id", "")),
                                "statement": str(getattr(item, "statement", ""))[:240],
                                "confidence": getattr(item, "confidence", None),
                                "verified": getattr(item, "verified", None),
                                "evidence_count": len(getattr(item, "evidence", ()) or ()),
                            }
                            for item in query_matches
                            if any(term in str(getattr(item, "statement", "")).casefold() for term in query_terms)
                        ][:40]
                    report["aggregation_candidates"] = [
                        {
                            "knowledge_id": str(getattr(item, "knowledge_id", "")),
                            "statement": str(getattr(item, "statement", ""))[:240],
                            "confidence": getattr(item, "confidence", None),
                            "verified": getattr(item, "verified", None),
                        }
                        for item in list(getattr(answer.aggregation, "results", ()) or ())[:12]
                    ]
                    report["answer"] = {
                        "text": str(getattr(answer.answer, "answer", answer.answer))[:2500],
                        "verified": bool(getattr(answer.answer, "verified", False)),
                        "status": str(getattr(answer.answer, "status", "")),
                        "traceability": str(answer.traceability)[:2000],
                        "quality_answer_traceability": str(getattr(answer.aggregation, "answer_traceability", None))[:2000],
                        "claim_link_diagnostics": answer.claim_link_diagnostics,
                        "arbitration": str(answer.arbitration)[:1200],
                        "arbitration_accepted": bool(getattr(answer.arbitration, "accepted", False)),
                    }
                    checks["answer_has_traceability"] = (
                        getattr(answer.traceability, "status", "") == "TRACEABLE"
                        and getattr(answer.traceability, "source_count", 0) >= 2
                    )
                    checks["answer_has_citations_or_sources"] = (
                        bool(getattr(answer.answer, "verified", False))
                        and bool(getattr(answer.arbitration, "accepted", False))
                        and getattr(answer.traceability, "source_count", 0) >= 2
                    )
                    checks["final_answer_verified"] = bool(getattr(answer.answer, "verified", False))
                    answer_text = str(getattr(answer.answer, "answer", answer.answer))
                    language_brain = UniversalLanguageBrain()
                    language_matches = language_brain.response_matches_language(query, answer_text)
                    translation_report = {"attempted": False, "status": "NOT_CONFIGURED"}
                    if (
                        not language_matches
                        and MyMemoryTranslationAdapter.configured()
                        and bool(getattr(answer.answer, "verified", False))
                        and bool(getattr(answer.arbitration, "accepted", False))
                        and getattr(answer.traceability, "source_count", 0) >= 2
                    ):
                        translation_report["attempted"] = True
                        translated = MyMemoryTranslationAdapter().translate(
                            answer_text,
                            source_language=language_brain.detect(answer_text).language_code,
                            target_language=language_brain.detect(query).language_code,
                        )
                        if translated is not None and language_brain.response_matches_language(query, translated.text):
                            answer_text = translated.text
                            language_matches = True
                            translation_report.update({
                                "status": "TRANSLATED_AND_LANGUAGE_CHECKED",
                                "provider": translated.provider,
                                "source_language": translated.source_language,
                                "target_language": translated.target_language,
                                "url_tokens_preserved": translated.url_tokens_preserved,
                                "numeric_tokens_preserved": translated.numeric_tokens_preserved,
                                "original_evidence_traceability_preserved": True,
                            })
                        else:
                            translation_report["status"] = "TRANSLATION_FAILED_OR_REJECTED"
                    report["answer"]["text"] = answer_text[:2500]
                    report["answer"]["translation"] = translation_report
                    checks["answer_language_matches_query"] = language_matches
                    checks["answer_arbitration_accepted"] = bool(getattr(answer.arbitration, "accepted", False))
                else:
                    checks["answer_has_traceability"] = False
                    checks["answer_has_citations_or_sources"] = False
                    checks["final_answer_verified"] = False
                    checks["answer_language_matches_query"] = False
                    checks["answer_arbitration_accepted"] = False
            else:
                checks["publisher_content_fetched"] = False
                checks["multiple_distinct_domains"] = False
                checks["explicit_publication_dates"] = False
                checks["answer_has_traceability"] = False
                checks["answer_has_citations_or_sources"] = False
                checks["final_answer_verified"] = False
                checks["answer_language_matches_query"] = False
                checks["answer_arbitration_accepted"] = False

            report["elapsed_seconds"] = round(time.monotonic() - started, 2)
            # Acceptance requires the actual pipeline to finish and show direct
            # publisher content from multiple dated domains with traceability.
            passed = all(bool(value) for value in checks.values())
            report["status"] = "PASS" if passed else "FAIL"
            report["failed_checks"] = [name for name, value in checks.items() if not value]
            print(json.dumps(report, ensure_ascii=False, default=str, indent=2), flush=True)
            return 0 if passed else 2
    except Exception as exc:
        report["elapsed_seconds"] = round(time.monotonic() - started, 2)
        report["status"] = "FAIL"
        report["exception"] = f"{type(exc).__name__}: {str(exc)[:600]}"
        print(json.dumps(report, ensure_ascii=False, default=str, indent=2), flush=True)
        return 2
    finally:
        if integration is not None:
            try:
                if integration.has_context(job_id):
                    integration.remove_context(job_id)
                integration.close()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
