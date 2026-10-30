from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from app.config import settings
from core.brain.prompt_injection_guard import (
    PromptInjectionGuard,
    PromptInjectionStatus,
)
from core.brain.universal_language_brain import UniversalLanguageBrain
from core.brain.translation_adapter import MyMemoryTranslationAdapter
from core.research.runtime_providers import (
    build_default_research_acquisition_engine,
)
from core.research.acquisition_pipeline import ResearchAcquisitionPipeline
from core.research.answer_pipeline import ResearchAnswerPipeline
from core.research.extraction_pipeline import ResearchExtractionPipeline
from core.research.query import ResearchQueryEngine
from core.research.research_execution_manager import (
    ResearchExecutionManager,
)
from core.research.research_pipeline_integration import (
    ResearchPipelineIntegration,
)
from core.research.storage import ResearchStorage


@dataclass(frozen=True)
class MotherResearchResult:
    """
    Result returned by the Mother Brain research integration.

    Conflict information is observational metadata only.
    It does not grant authority, mutate knowledge, or replace
    the existing research conflict resolver/aggregator.

    Prompt-injection information is also observational security
    metadata. Research content is untrusted data and never becomes
    authority, permission, or executable instruction.
    """

    success: bool
    query: str
    status: str
    answer: str
    job_id: str
    execution_id: str
    verification_status: str

    conflict_status: str = "NO_CONFLICT"
    conflict_count: int = 0
    resolved_conflict_count: int = 0
    unresolved_conflict_count: int = 0
    conflict_ids: tuple[str, ...] = ()
    resolved_knowledge_ids: tuple[str, ...] = ()

    prompt_injection_status: str = "SAFE"
    prompt_injection_safe_to_follow: bool = True
    prompt_injection_rules: tuple[str, ...] = ()

    error: str = ""
    diagnostics: dict[str, object] = field(default_factory=dict)


class MotherResearchIntegration:
    """
    Mother Brain bridge to the existing SAHIBEX research stack.

    MasterBrain remains authoritative for:
    - Constitution
    - Permission
    - Protected actions
    - Human authority
    - Verification

    This adapter connects an already-approved research request
    to the existing research execution pipeline.

    Network permission is NOT granted here. The existing
    ResearchAcquisitionPipeline remains responsible for enforcing
    NETWORK_ACCESS before a network-capable provider is executed.

    Conflict detection and resolution are NOT duplicated here.
    Existing ResearchAggregationResult already contains the
    authoritative conflict-resolution metadata.

    Prompt-injection protection is observational and defensive:
    research output is treated as untrusted data. Detected
    instruction-hijacking content cannot become executable
    authority through this integration.
    """

    VERSION = "1.2"

    def __init__(
        self,
        *,
        storage: ResearchStorage | None = None,
        acquisition_pipeline: ResearchAcquisitionPipeline | None = None,
        extraction_pipeline: ResearchExtractionPipeline | None = None,
        answer_pipeline: ResearchAnswerPipeline | None = None,
        research_pipeline: ResearchPipelineIntegration | None = None,
        execution_manager: ResearchExecutionManager | None = None,
    ) -> None:
        if storage is None:
            database_path = settings.data_dir / "sahibex_brain.db"
            database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            storage = ResearchStorage(database_path)

        self.storage = storage
        self.prompt_injection_guard = PromptInjectionGuard()
        self.research_provider_status = None

        if acquisition_pipeline is None:
            # The acquisition/ingestion registry and the research query/
            # knowledge store must target the same database when a caller
            # injects custom storage. Otherwise sources are ingested into the
            # default database while retrieval reads the injected database.
            database_path = Path(self.storage.database_path)

            acquisition_engine, provider_status = (
                build_default_research_acquisition_engine(
                    project_root=settings.project_root,
                )
            )

            acquisition_pipeline = ResearchAcquisitionPipeline(
                database_path=database_path,
                acquisition_engine=acquisition_engine,
            )

            self.research_provider_status = provider_status

        self.acquisition_pipeline = acquisition_pipeline

        ingestion_pipeline = (
            self.acquisition_pipeline.ingestion_pipeline
        )

        if extraction_pipeline is None:
            extraction_pipeline = ResearchExtractionPipeline(
                ingestion_pipeline,
            )

        self.extraction_pipeline = extraction_pipeline

        if answer_pipeline is None:
            query_engine = ResearchQueryEngine(
                ingestion_pipeline.engine,
                self.storage,
            )

            answer_pipeline = ResearchAnswerPipeline(
                query_engine,
            )

        self.answer_pipeline = answer_pipeline

        if research_pipeline is None:
            research_pipeline = ResearchPipelineIntegration(
                acquisition_pipeline=self.acquisition_pipeline,
                extraction_pipeline=self.extraction_pipeline,
                answer_pipeline=self.answer_pipeline,
                storage=self.storage,
            )

        self.research_pipeline = research_pipeline

        if execution_manager is None:
            execution_manager = ResearchExecutionManager()

        self.execution_manager = execution_manager

        self.research_pipeline.register_handlers(
            self.execution_manager.executor
        )

    @staticmethod
    def _conflict_metadata(answer) -> dict:
        """
        Extract conflict metadata from the existing
        ResearchAnswerPipelineResult.

        Source of truth:

        ResearchAnswerPipelineResult
            -> ResearchAggregationResult
            -> conflict metadata

        This method is observational only.
        It does not resolve, mutate, delete, or override conflicts.
        """

        aggregation = getattr(
            answer,
            "aggregation",
            None,
        )

        if aggregation is None:
            return {
                "conflict_status": "NO_CONFLICT",
                "conflict_count": 0,
                "resolved_conflict_count": 0,
                "unresolved_conflict_count": 0,
                "conflict_ids": (),
                "resolved_knowledge_ids": (),
            }

        conflict_count = int(
            getattr(
                aggregation,
                "conflict_count",
                0,
            )
        )

        resolved_conflict_count = int(
            getattr(
                aggregation,
                "resolved_conflict_count",
                0,
            )
        )

        unresolved_conflict_count = int(
            getattr(
                aggregation,
                "unresolved_conflict_count",
                0,
            )
        )

        conflict_ids = tuple(
            getattr(
                aggregation,
                "conflict_ids",
                [],
            )
            or []
        )

        resolved_knowledge_ids = tuple(
            getattr(
                aggregation,
                "resolved_knowledge_ids",
                [],
            )
            or []
        )

        if unresolved_conflict_count > 0:
            conflict_status = "UNRESOLVED_CONFLICT"
        elif resolved_conflict_count > 0:
            conflict_status = "CONFLICT_RESOLVED"
        elif conflict_count > 0:
            conflict_status = "CONFLICT_DETECTED"
        else:
            conflict_status = "NO_CONFLICT"

        return {
            "conflict_status": conflict_status,
            "conflict_count": conflict_count,
            "resolved_conflict_count": (
                resolved_conflict_count
            ),
            "unresolved_conflict_count": (
                unresolved_conflict_count
            ),
            "conflict_ids": conflict_ids,
            "resolved_knowledge_ids": (
                resolved_knowledge_ids
            ),
        }

    def _prompt_injection_metadata(
        self,
        answer: str,
    ) -> dict:
        """
        Inspect research output as untrusted content.

        This check never grants authority and never executes,
        approves, or rejects a protected action.
        """

        result = self.prompt_injection_guard.inspect(
            answer,
            source="research",
        )

        return {
            "prompt_injection_status": (
                result.status.value
            ),
            "prompt_injection_safe_to_follow": (
                result.safe_to_follow
            ),
            "prompt_injection_rules": (
                result.matched_rules
            ),
        }

    @staticmethod
    def _source_leads(context, *, limit: int = 3) -> list[str]:
        """Return bounded public HTTP(S) source leads, never verified claims."""
        acquisition = getattr(context, "acquisition", None)
        sources = getattr(acquisition, "sources", ())
        # If publisher fetching failed, retain only the separately recorded
        # search-discovery URLs as unverified leads. They are never evidence.
        if not sources:
            outputs = getattr(context, "outputs", {})
            discovery = (
                outputs.get("search_discovery_acquisition", {})
                if isinstance(outputs, dict) else {}
            )
            sources = getattr(discovery, "sources", ())
        leads: list[str] = []
        seen: set[str] = set()
        for source in sources:
            locator = getattr(source, "locator", "")
            title = " ".join(str(getattr(source, "title", "Source")).split())
            if not isinstance(locator, str) or not locator.strip():
                continue
            parsed = urlparse(locator)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                continue
            if locator in seen:
                continue
            seen.add(locator)
            leads.append(f"- {title[:140] or 'Source'} — {locator[:500]}")
            if len(leads) >= limit:
                break
        return leads

    @staticmethod
    def _insufficient_evidence_message(query: str, source_leads: list[str]) -> str:
        """Explain verification failure in the user's script/language where recognized."""
        is_hindi = any("\u0900" <= char <= "\u097f" for char in query)
        if is_hindi:
            answer = (
                "इस सवाल का भरोसेमंद जवाब देने के लिए पर्याप्त प्रमाण सत्यापित नहीं हो सके। "
                "नीचे दिए गए लिंक केवल आगे जाँचने के स्रोत हैं, सत्यापित निष्कर्ष नहीं।"
            )
            if source_leads:
                answer += "\nजाँच के लिए मिले स्रोत:\n" + "\n".join(source_leads)
            return answer

        answer = (
            "I couldn't verify enough reliable evidence to answer this query. "
            "The links below are research leads, not verified conclusions."
        )
        if source_leads:
            answer += "\nSources found for review:\n" + "\n".join(source_leads)
        return answer

    @staticmethod
    def _execution_failure_message(
        query: str, error: str | None, source_leads: list[str] | None = None
    ) -> str:
        """Return a safe, localized explanation without exposing raw internals."""
        source_leads = source_leads or []
        is_hindi = any("\u0900" <= char <= "\u097f" for char in query)
        normalized_error = (error or "").casefold()
        search_blocked = any(
            marker in normalized_error
            for marker in ("anti-bot challenge", "captcha", "no live search provider is configured")
        )
        if is_hindi:
            if search_blocked:
                message = (
                    "मैं अभी भरोसेमंद वेब स्रोत खोज नहीं सका, क्योंकि उपलब्ध सर्च सेवा ने "
                    "अनुरोध रोक दिया या कॉन्फ़िगर नहीं है। मैंने बिना जाँचे कोई निष्कर्ष नहीं बनाया। "
                    "कृपया बाद में दोबारा कोशिश करें या अनुमोदित वैकल्पिक सर्च सेवा कॉन्फ़िगर करें।"
                )
            else:
                message = (
                    "यह रिसर्च अभी पूरी नहीं हो सकी, इसलिए मैं सत्यापित जवाब नहीं दे सकता। "
                    "मैंने बिना प्रमाण के निष्कर्ष नहीं बनाया। कृपया दोबारा कोशिश करें।"
                )
            if source_leads:
                message += "\nआगे जाँचने के लिए स्रोत (सत्यापित निष्कर्ष नहीं):\n" + "\n".join(source_leads)
            return message
        if search_blocked:
            message = (
                "I couldn't reach a usable search service, so I couldn't verify this research. "
                "No unsupported conclusion was generated. Retry later or configure an approved alternative search backend."
            )
        else:
            message = (
                "This research attempt did not complete, so I can't provide a verified answer. "
                "No unsupported conclusion was generated. Please retry."
            )
        if source_leads:
            message += "\nResearch leads for review (not verified conclusions):\n" + "\n".join(source_leads)
        return message

    @staticmethod
    def _answer_matches_query_language(query: str, answer: str) -> bool:
        """Prevent a verified research claim from being returned in the wrong language."""
        try:
            return UniversalLanguageBrain().response_matches_language(query, answer)
        except Exception:
            # A language-check failure must not certify a mismatched answer.
            return False

    @staticmethod
    def _current_news_freshness_gate(query: str, sources, *, now: datetime | None = None):
        """Compatibility wrapper for the shared query-specific freshness gate."""
        from core.research.freshness import assess_query_source_freshness
        return assess_query_source_freshness(query, sources, reference_time=now)

    @staticmethod
    def _answer_text_and_verification(
        pipeline_result,
    ) -> tuple[str, str]:
        """Extract user-facing answer text without inventing verification."""
        synthesized_answer = getattr(
            pipeline_result,
            "answer",
            None,
        )
        answer_text = getattr(
            synthesized_answer,
            "answer",
            None,
        )
        if not isinstance(answer_text, str):
            answer_text = getattr(
                pipeline_result,
                "result",
                synthesized_answer
                if isinstance(synthesized_answer, str)
                else "",
            )
        answer = answer_text.strip() if isinstance(answer_text, str) else ""

        explicit_status = getattr(
            pipeline_result,
            "verification_status",
            None,
        )
        if isinstance(explicit_status, str) and explicit_status.strip():
            # Normalize status tokens at this boundary. Providers may emit
            # lowercase or padded strings; downstream acceptance compares
            # against canonical constants and must not silently reject a
            # genuinely VERIFIED result because of formatting alone.
            return answer, explicit_status.strip().upper()

        answer_verified = getattr(
            synthesized_answer,
            "verified",
            None,
        )
        answer_status = getattr(
            synthesized_answer,
            "status",
            None,
        )
        if answer_verified is True and answer_status == "VERIFIED":
            verification_status = "VERIFIED"
        elif answer_verified is False or answer_status in {
            "UNVERIFIED",
            "NO_RESULT",
            "CONFLICT_UNRESOLVED",
            "PARTIALLY_RESOLVED",
            "CONFLICT_RESOLVED",
            "STALE",
            "LOW_CONFIDENCE",
            "UNCERTAIN",
            "CONFLICTED",
        }:
            verification_status = "NOT_VERIFIED"
        else:
            verification_status = "UNKNOWN"
        return answer, verification_status

    @staticmethod
    def _pipeline_diagnostics(context) -> dict[str, object]:
        """Return bounded, secret-free stage telemetry for failed research audits."""
        outputs = context.outputs if isinstance(getattr(context, "outputs", None), dict) else {}
        diagnostics: dict[str, object] = {}

        publisher = outputs.get("publisher_fetch")
        if isinstance(publisher, dict):
            diagnostics["publisher_fetch"] = {
                "status": str(publisher.get("status", "UNKNOWN"))[:80],
                "requested": publisher.get("requested"),
                "acquired": publisher.get("acquired"),
                "errors": [str(item)[:180] for item in list(publisher.get("details") or [])[:5]],
            }

        timestamp_provenance = outputs.get("discovery_timestamp_provenance")
        if isinstance(timestamp_provenance, dict):
            diagnostics["discovery_timestamp_provenance"] = {
                key: timestamp_provenance.get(key)
                for key in ("candidate_sources_with_timestamp", "selected_urls_with_timestamp", "selected_urls_with_trusted_backend")
            }

        discovery = outputs.get("corroboration_discovery")
        if isinstance(discovery, dict):
            diagnostics["discovery"] = {
                "candidate_url_count": discovery.get("candidate_url_count"),
                "resolved_candidate_url_count": discovery.get("resolved_candidate_url_count"),
                "selected_diverse_url_count": discovery.get("selected_diverse_url_count"),
                "selected_publisher_hosts": list(discovery.get("selected_publisher_hosts") or [])[:10],
                "attempted_followups": len(discovery.get("attempted_queries") or []),
                "attempted_expansions": len(discovery.get("expansion_queries") or []),
                "failed_followups": [str(item)[:160] for item in list(discovery.get("failed_queries") or [])[:3]],
                "failed_expansions": [str(item)[:160] for item in list(discovery.get("expansion_failures") or [])[:3]],
            }

        verification = getattr(context, "verification", None)
        if isinstance(verification, dict):
            diagnostics["evidence_verification"] = {
                key: verification.get(key)
                for key in ("documents", "extracted_count", "finding_count", "evidence_count", "status")
                if key in verification
            }
        extraction = getattr(context, "extraction", None)
        if isinstance(extraction, list):
            diagnostics["extraction"] = {
                "documents_processed": len(extraction),
                "findings": sum(len(getattr(item, "findings", ()) or ()) for item in extraction),
                "evidence_stored": sum(
                    1 for item in extraction
                    for finding in (getattr(item, "findings", ()) or ())
                    if getattr(finding, "evidence_stored", False)
                ),
            }
        answer_pipeline_result = getattr(context, "answer", None)
        if answer_pipeline_result is not None:
            answer = getattr(answer_pipeline_result, "answer", answer_pipeline_result)
            answer_evidence = list(getattr(answer, "evidence", ()) or ())
            diagnostics["answer"] = {
                "status": str(getattr(answer, "status", "UNKNOWN"))[:80],
                "verified": getattr(answer, "verified", None),
                "confidence": getattr(answer, "confidence", None),
                "claim_count": len(answer_evidence),
                "claims_with_multiple_sources": sum(
                    1 for item in answer_evidence
                    if len(set(getattr(item, "source_ids", ()) or ())) >= 2
                ),
                "claims_with_evidence_text": sum(
                    1 for item in answer_evidence
                    if any(str(value).strip() for value in (getattr(item, "evidence_texts", ()) or ()))
                ),
            }
            query_result = getattr(answer_pipeline_result, "query_result", None)
            aggregation = getattr(answer_pipeline_result, "aggregation", None)
            quality_answer = getattr(aggregation, "answer", None) if aggregation is not None else None
            quality_claims = list(getattr(quality_answer, "claims", ()) or ())
            diagnostics["claim_pipeline"] = {
                "relevance_candidates_before_corroboration": getattr(
                    answer_pipeline_result, "relevance_candidate_count", None
                ),
                "corroborated_candidates_retained": getattr(
                    answer_pipeline_result, "corroborated_candidate_count", None
                ),
                "retrieval_matches_after_corroboration": getattr(query_result, "total_matches", None),
                "aggregation_results": len(getattr(aggregation, "results", ()) or ()) if aggregation is not None else None,
                "quality_claims": len(quality_claims),
                "multi_source_quality_claims": sum(
                    1 for item in quality_claims
                    if getattr(item, "status", "") == "MULTI_SOURCE_SUPPORTED"
                    and getattr(item, "source_count", 0) >= 2
                ),
                # Counts only; never log source text, queries, credentials, or raw errors.
                "claim_linking": dict(
                    getattr(answer_pipeline_result, "claim_link_diagnostics", None) or {}
                ),
            }
            arbitration = getattr(answer_pipeline_result, "arbitration", None)
            if arbitration is not None:
                arbitration_reasons = getattr(arbitration, "reasons", ()) or ()
                if isinstance(arbitration_reasons, str):
                    arbitration_reasons = (arbitration_reasons,)
                diagnostics["arbitration"] = {
                    "accepted": getattr(arbitration, "accepted", None),
                    "status": str(getattr(arbitration, "status", "UNKNOWN"))[:80],
                    "reasons": [str(item)[:180] for item in list(arbitration_reasons)[:8]],
                    # Preserve compatibility with older arbitration result objects.
                    "reason": str(getattr(arbitration, "reason", ""))[:180],
                }
            traceability = getattr(answer_pipeline_result, "traceability", None)
            if traceability is not None:
                diagnostics["traceability"] = {
                    "status": str(getattr(traceability, "status", "UNKNOWN"))[:80],
                    "linked_count": getattr(traceability, "linked_count", None),
                    "unlinked_count": getattr(traceability, "unlinked_count", None),
                }
        return diagnostics

    def _promote_verified_answer_knowledge(self, context, *, query: str, job_id: str) -> dict[str, object]:
        """Persist only claims that passed the final live answer gate.

        This is deliberately stricter than a verified answer flag: the
        arbitrator, end-to-end traceability, evidence linkage, multi-source
        support, language and freshness gates must already have passed.
        Conflicted or ambiguously selected knowledge is never promoted.
        """
        result = getattr(context, "answer", None)
        answer = getattr(result, "answer", None)
        arbitration = getattr(result, "arbitration", None)
        if (
            answer is None
            or getattr(answer, "verified", False) is not True
            or getattr(answer, "status", "") != "VERIFIED"
            or getattr(arbitration, "accepted", False) is not True
        ):
            return {"status": "BLOCKED", "reason": "final answer/arbitration gate not accepted", "promoted_count": 0}

        aggregation = getattr(result, "aggregation", None)
        if int(getattr(aggregation, "unresolved_conflict_count", 0) or 0) > 0:
            return {"status": "BLOCKED", "reason": "unresolved conflicts", "promoted_count": 0}

        selected_ids = {
            str(value).strip()
            for value in (getattr(answer, "knowledge_ids", ()) or ())
            if isinstance(value, str) and value.strip()
        }
        promoted: list[str] = []
        skipped: list[str] = []
        now = datetime.now(timezone.utc)
        traceability = getattr(aggregation, "answer_traceability", None)
        traces = {
            getattr(trace, "knowledge_id", ""): trace
            for trace in (getattr(traceability, "traces", ()) or ())
            if getattr(trace, "knowledge_id", "")
        }
        for knowledge_id in sorted(selected_ids):
            trace = traces.get(knowledge_id)
            source_ids = tuple(dict.fromkeys(
                str(value).strip()
                for value in (getattr(trace, "source_ids", ()) or ())
                if isinstance(value, str) and value.strip()
            ))
            evidence_ids = tuple(dict.fromkeys(
                str(value).strip()
                for value in (getattr(trace, "evidence_ids", ()) or ())
                if isinstance(value, str) and value.strip()
            ))
            if (
                trace is None
                or getattr(trace, "trace_complete", False) is not True
                or getattr(trace, "supported", False) is not True
                or getattr(trace, "verified", False) is not True
                or len(source_ids) < 2
                or not evidence_ids
            ):
                continue

            candidate = self.storage.get_knowledge(knowledge_id)
            if candidate is None or not candidate.evidence or candidate.confidence < 0.60:
                skipped.append(knowledge_id)
                continue

            conflict = self.storage.knowledge_verification_context(knowledge_id)
            if int(conflict.get("unresolved_conflict_count", 0) or 0) > 0:
                skipped.append(knowledge_id)
                continue
            conflict_count = int(conflict.get("conflict_count", 0) or 0)
            if conflict_count > 0 and conflict.get("selected_knowledge_id") != knowledge_id:
                skipped.append(knowledge_id)
                continue

            lifecycle = self.storage.knowledge_verification_lifecycle(knowledge_id)
            current_status = str(lifecycle.get("verification_status", "UNVERIFIED")).upper()
            if current_status == "CONFLICTED":
                skipped.append(knowledge_id)
                continue

            candidate.verified = True
            candidate.last_verified_at = now
            metadata = dict(candidate.metadata or {})
            metadata["verified_answer_promotion"] = {
                "query": query,
                "research_job_id": job_id,
                "arbitration": "ACCEPTED",
                "source_ids": list(source_ids),
                "evidence_ids": list(evidence_ids),
                "promoted_at": now.isoformat(),
                "verification_rule": "final verified answer + accepted arbitration + complete verified traceability + independent multi-source support + final answer gates",
            }
            candidate.metadata = metadata
            self.storage.save_knowledge(candidate)
            self.storage.record_knowledge_verification(
                knowledge_id=knowledge_id,
                status="VERIFIED",
                reason="Final Main Brain answer passed evidence, arbitration, traceability, freshness and language gates.",
                verified_at=now,
                metadata={
                    "query": query,
                    "research_job_id": job_id,
                    "source_ids": list(source_ids),
                    "evidence_ids": list(evidence_ids),
                    "arbitration": "ACCEPTED",
                },
            )
            promoted.append(knowledge_id)

        return {
            "status": "PROMOTED" if promoted else "NO_ELIGIBLE_CLAIMS",
            "promoted_count": len(promoted),
            "knowledge_ids": promoted,
            "skipped_knowledge_ids": skipped,
        }

    def research(
        self,
        *,
        query: str,
        confirmation: bool = False,
    ) -> MotherResearchResult:
        if not isinstance(query, str):
            raise TypeError("query must be str")

        query = query.strip()

        if not query:
            raise ValueError(
                "query must not be empty"
            )

        job_id = (
            f"mother-research-{uuid4().hex}"
        )

        execution_id = (
            f"execution-{uuid4().hex}"
        )

        try:
            self.execution_manager.create_job(
                job_id=job_id,
                query=query,
                metadata={"network_confirmation": bool(confirmation)},
            )

            self.execution_manager.create_plan(
                job_id
            )

            self.execution_manager.start_job(
                job_id
            )

            execution = self.execution_manager.execute(
                execution_id=execution_id,
                job_id=job_id,
            )

            context = self.research_pipeline.context_for(
                job_id
            )

            answer = ""
            verification_status = "UNKNOWN"

            conflict_metadata = {
                "conflict_status": "NO_CONFLICT",
                "conflict_count": 0,
                "resolved_conflict_count": 0,
                "unresolved_conflict_count": 0,
                "conflict_ids": (),
                "resolved_knowledge_ids": (),
            }

            prompt_injection_metadata = {
                "prompt_injection_status": (
                    PromptInjectionStatus.SAFE.value
                ),
                "prompt_injection_safe_to_follow": True,
                "prompt_injection_rules": (),
            }

            if context.answer is not None:
                # Do not stringify nested answer objects or infer verification.
                answer, verification_status = (
                    self._answer_text_and_verification(
                        context.answer
                    )
                )

                conflict_metadata = (
                    self._conflict_metadata(
                        context.answer
                    )
                )

                prompt_injection_metadata = (
                    self._prompt_injection_metadata(
                        answer
                    )
                )

            if execution.status != "completed":
                if context.answer is None:
                    # A permission-gated/failed acquisition did not produce an
                    # answer to verify; distinguish that from unknown truth.
                    verification_status = "NOT_EXECUTED"
                    answer = self._execution_failure_message(
                        query, execution.error, self._source_leads(context)
                    )
                return MotherResearchResult(
                    success=False,
                    query=query,
                    status=execution.status,
                    answer=answer,
                    job_id=job_id,
                    execution_id=execution_id,
                    verification_status=(
                        verification_status
                    ),
                    conflict_status=(
                        conflict_metadata[
                            "conflict_status"
                        ]
                    ),
                    conflict_count=(
                        conflict_metadata[
                            "conflict_count"
                        ]
                    ),
                    resolved_conflict_count=(
                        conflict_metadata[
                            "resolved_conflict_count"
                        ]
                    ),
                    unresolved_conflict_count=(
                        conflict_metadata[
                            "unresolved_conflict_count"
                        ]
                    ),
                    conflict_ids=(
                        conflict_metadata[
                            "conflict_ids"
                        ]
                    ),
                    resolved_knowledge_ids=(
                        conflict_metadata[
                            "resolved_knowledge_ids"
                        ]
                    ),
                    prompt_injection_status=(
                        prompt_injection_metadata[
                            "prompt_injection_status"
                        ]
                    ),
                    prompt_injection_safe_to_follow=(
                        prompt_injection_metadata[
                            "prompt_injection_safe_to_follow"
                        ]
                    ),
                    prompt_injection_rules=(
                        prompt_injection_metadata[
                            "prompt_injection_rules"
                        ]
                    ),
                    error=(
                        execution.error
                        or "research execution failed"
                    ),
                    diagnostics=self._pipeline_diagnostics(context),
                )

            freshness_diagnostics = self._current_news_freshness_gate(
                query,
                getattr(getattr(context, "acquisition", None), "sources", ()),
            )
            if (
                freshness_diagnostics is not None
                and freshness_diagnostics.get("status") != "PASS"
                and verification_status == "VERIFIED"
            ):
                # Do not let the answer be labelled VERIFIED merely because
                # claim support passed: a current-news answer also requires
                # every selected publisher source to pass the query-specific
                # publication-age gate. Stable facts do not enter this branch.
                verification_status = "STALE"

            # A verified claim is not a usable final answer if it switches
            # away from the user's language. Do not mislabel an English answer
            # to a Hindi query as a successful localized response. Until a
            # trusted translation adapter is available, fail closed in the
            # user's language rather than silently returning the wrong one.
            language_matches = self._answer_matches_query_language(query, answer)
            translation_diagnostics: dict[str, object] = {"attempted": False, "status": "NOT_CONFIGURED"}
            if verification_status == "VERIFIED" and not language_matches:
                translation_diagnostics["attempted"] = MyMemoryTranslationAdapter.configured()
                if MyMemoryTranslationAdapter.configured():
                    language_brain = UniversalLanguageBrain()
                    source_language = language_brain.detect(answer).language_code
                    target_language = language_brain.detect(query).language_code
                    translated = MyMemoryTranslationAdapter().translate(
                        answer,
                        source_language=source_language,
                        target_language=target_language,
                    )
                    if translated is not None and self._answer_matches_query_language(query, translated.text):
                        # The claim's evidence graph remains the original
                        # pipeline result. Translation is a rendering layer,
                        # never a source of facts or a new verification event.
                        answer = translated.text
                        language_matches = True
                        translation_diagnostics.update({
                            "status": "TRANSLATED_AND_LANGUAGE_CHECKED",
                            "provider": translated.provider,
                            "source_language": translated.source_language,
                            "target_language": translated.target_language,
                            "url_tokens_preserved": translated.url_tokens_preserved,
                            "numeric_tokens_preserved": translated.numeric_tokens_preserved,
                            "source_answer_kept_in_traceability": True,
                        })
                    else:
                        translation_diagnostics["status"] = "TRANSLATION_FAILED_OR_REJECTED"
                if not language_matches:
                    verification_status = "LANGUAGE_MISMATCH"

            # Completing acquisition/extraction is not the same as verifying
            # an answer. Never expose unverified page text as a successful
            # research answer; fail closed with a clear user-facing status.
            answer_verified = verification_status == "VERIFIED"
            if not answer_verified:
                source_leads = self._source_leads(context)
                answer = self._insufficient_evidence_message(query, source_leads)

            # The final fallback message is itself localized. Re-check the
            # text actually returned to the user, not the rejected candidate.
            language_matches = self._answer_matches_query_language(query, answer)
            final_diagnostics = self._pipeline_diagnostics(context)
            final_diagnostics["language_consistency"] = {
                "matches_query": language_matches,
                "status": "MATCH" if language_matches else "MISMATCH",
            }
            final_diagnostics["translation"] = translation_diagnostics
            if freshness_diagnostics is not None:
                final_diagnostics["current_news_freshness_gate"] = freshness_diagnostics

            promotion_diagnostics: dict[str, object] = {
                "status": "NOT_ATTEMPTED",
                "promoted_count": 0,
            }
            if answer_verified:
                try:
                    promotion_diagnostics = self._promote_verified_answer_knowledge(
                        context,
                        query=query,
                        job_id=job_id,
                    )
                except Exception as promotion_error:
                    # The answer remains independently verified, but a failed
                    # durable write must be visible and must not be reported as
                    # successful knowledge persistence.
                    promotion_diagnostics = {
                        "status": "PERSISTENCE_FAILED",
                        "promoted_count": 0,
                        "error": type(promotion_error).__name__,
                    }
            final_diagnostics["verified_knowledge_promotion"] = promotion_diagnostics

            return MotherResearchResult(
                success=answer_verified,
                query=query,
                status=(
                    execution.status
                    if answer_verified
                    else "insufficient_evidence"
                ),
                answer=answer,
                job_id=job_id,
                execution_id=execution_id,
                verification_status=(
                    verification_status
                ),
                conflict_status=(
                    conflict_metadata[
                        "conflict_status"
                    ]
                ),
                conflict_count=(
                    conflict_metadata[
                        "conflict_count"
                    ]
                ),
                resolved_conflict_count=(
                    conflict_metadata[
                        "resolved_conflict_count"
                    ]
                ),
                unresolved_conflict_count=(
                    conflict_metadata[
                        "unresolved_conflict_count"
                    ]
                ),
                conflict_ids=(
                    conflict_metadata[
                        "conflict_ids"
                    ]
                ),
                resolved_knowledge_ids=(
                    conflict_metadata[
                        "resolved_knowledge_ids"
                    ]
                ),
                prompt_injection_status=(
                    prompt_injection_metadata[
                        "prompt_injection_status"
                    ]
                ),
                prompt_injection_safe_to_follow=(
                    prompt_injection_metadata[
                        "prompt_injection_safe_to_follow"
                    ]
                ),
                prompt_injection_rules=(
                    prompt_injection_metadata[
                        "prompt_injection_rules"
                    ]
                ),
                error=(
                    "research answer language did not match the query language"
                    if verification_status == "LANGUAGE_MISMATCH"
                    else (
                        "research completed but answer did not meet the verification threshold"
                        if not answer_verified
                        else ""
                    )
                ),
                diagnostics=final_diagnostics,
            )

        except Exception as exc:
            # Failures thrown before the execution manager returns a result
            # still need bounded stage diagnostics. Without this, live failures
            # look like generic zero-extraction errors and the blocked stage is
            # impossible to distinguish from provider, fetch, or parser errors.
            diagnostics: dict[str, object] = {}
            try:
                failed_context = self.research_pipeline.context_for(job_id)
                diagnostics = self._pipeline_diagnostics(failed_context)
            except Exception:
                # Context creation itself may have failed; keep the result safe
                # and do not mask the original exception with a diagnostic error.
                diagnostics = {}
            return MotherResearchResult(
                success=False,
                query=query,
                status="failed",
                answer="",
                job_id=job_id,
                execution_id=execution_id,
                verification_status="FAILED",
                conflict_status="UNKNOWN",
                prompt_injection_status=(
                    PromptInjectionStatus.SAFE.value
                ),
                prompt_injection_safe_to_follow=True,
                prompt_injection_rules=(),
                error=str(exc),
                diagnostics=diagnostics,
            )
