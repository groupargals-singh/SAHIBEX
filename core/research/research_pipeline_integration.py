from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.research.acquisition import AcquisitionRequest
from core.research.acquisition_pipeline import ResearchAcquisitionPipeline
from core.research.answer_pipeline import (
    ResearchAnswerPipeline,
    ResearchAnswerPipelineResult,
)
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
            urls = [
                source.locator
                for source in search_result.acquisition.sources
                if source.locator
            ][:3]
            if not urls:
                raise RuntimeError("search provider returned no source URLs")

            direct_request = AcquisitionRequest(
                query=job.query,
                source_type="web",
                max_sources=len(urls),
                metadata={"urls": urls},
            )
            result = self.acquisition_pipeline.acquire_and_ingest(
                direct_request,
                provider_name="direct_web",
                confirmation=confirmation,
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
            "status": (
                "verified"
                if evidence_count > 0
                else "insufficient_evidence"
            ),
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
            or context.verification.get("status") != "verified"
            or context.verification.get("evidence_count", 0) <= 0
        ):
            raise RuntimeError(
                "answer synthesis blocked: insufficient verified evidence"
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
