from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from app.config import settings
from core.brain.prompt_injection_guard import (
    PromptInjectionGuard,
    PromptInjectionStatus,
)
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
            database_path = (
                Path(settings.data_dir)
                / "sahibex_brain.db"
            )

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
    def _execution_failure_message(query: str, error: str | None) -> str:
        """Return a safe, localized explanation without exposing raw internals."""
        is_hindi = any("\u0900" <= char <= "\u097f" for char in query)
        normalized_error = (error or "").casefold()
        search_blocked = any(
            marker in normalized_error
            for marker in ("anti-bot challenge", "captcha", "no live search provider is configured")
        )
        if is_hindi:
            if search_blocked:
                return (
                    "मैं अभी भरोसेमंद वेब स्रोत खोज नहीं सका, क्योंकि उपलब्ध सर्च सेवा ने "
                    "अनुरोध रोक दिया या कॉन्फ़िगर नहीं है। मैंने बिना जाँचे कोई निष्कर्ष नहीं बनाया। "
                    "कृपया बाद में दोबारा कोशिश करें या अनुमोदित वैकल्पिक सर्च सेवा कॉन्फ़िगर करें।"
                )
            return (
                "यह रिसर्च अभी पूरी नहीं हो सकी, इसलिए मैं सत्यापित जवाब नहीं दे सकता। "
                "मैंने बिना प्रमाण के निष्कर्ष नहीं बनाया। कृपया दोबारा कोशिश करें।"
            )
        if search_blocked:
            return (
                "I couldn't reach a usable search service, so I couldn't verify this research. "
                "No unsupported conclusion was generated. Retry later or configure an approved alternative search backend."
            )
        return (
            "This research attempt did not complete, so I can't provide a verified answer. "
            "No unsupported conclusion was generated. Please retry."
        )

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
        if isinstance(explicit_status, str) and explicit_status:
            return answer, explicit_status

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
                        query, execution.error
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
                )

            # Completing acquisition/extraction is not the same as verifying
            # an answer. Never expose unverified page text as a successful
            # research answer; fail closed with a clear user-facing status.
            answer_verified = verification_status == "VERIFIED"
            if not answer_verified:
                source_leads = self._source_leads(context)
                answer = self._insufficient_evidence_message(query, source_leads)

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
                    "research completed but answer did not meet the "
                    "verification threshold"
                    if not answer_verified
                    else ""
                ),
            )

        except Exception as exc:
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
            )
