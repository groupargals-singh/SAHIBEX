from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from app.config import settings
from core.brain.operational_memory_knowledge import (
    OperationalMemoryKnowledgeIntegration,
)
from core.brain.operational_model import OperationalModelIntegration
from core.brain.operational_reasoning import OperationalReasoningResult
from core.brain.operational_verification import (
    OperationalVerificationRecovery,
)
from core.model_gateway.base import ModelGateway
from core.model_gateway.local_llama_provider import LocalLlamaProvider
from core.model_gateway.mock_provider import MockModelProvider
from core.research.storage import ResearchStorage


@dataclass(frozen=True)
class MotherOperationalResult:
    success: bool
    response: str
    memory_ids: tuple[str, ...]
    knowledge_ids: tuple[str, ...]
    verification_status: str
    provider: str


class MotherOperationalIntegration:
    """
    Mother Brain controlled bridge to SAHIBEX operational intelligence.

    This layer is called only after the Mother Brain's existing
    Constitution, Permission and Verification gates have passed.

    It does not grant authority and does not execute protected actions.
    """

    VERSION = "1.0"

    def __init__(
        self,
        *,
        storage: ResearchStorage | None = None,
        model_gateway: ModelGateway | None = None,
    ) -> None:
        if storage is None:
            database_path = settings.data_dir / "sahibex_brain.db"
            database_path.parent.mkdir(parents=True, exist_ok=True)
            storage = ResearchStorage(database_path)

        self.storage = storage

        self.memory_knowledge = OperationalMemoryKnowledgeIntegration(
            storage=self.storage
        )

        if model_gateway is None:
            model_gateway = ModelGateway()
            configured_provider = os.getenv("SAHIBEX_MODEL_PROVIDER", "mock").strip().lower()
            if configured_provider == "local":
                model_gateway.register_provider(LocalLlamaProvider())
            elif configured_provider == "mock":
                model_gateway.register_provider(MockModelProvider())
            else:
                raise ValueError(f"Unsupported SAHIBEX_MODEL_PROVIDER: {configured_provider}")

        self.model = OperationalModelIntegration(
            gateway=model_gateway
        )
        providers = model_gateway.providers()
        if not providers:
            raise RuntimeError("No model provider is registered.")
        self.default_provider = providers[0]

        self.verification = OperationalVerificationRecovery()

    def process_approved_request(
        self,
        *,
        objective: str,
        intent: str,
        provider: str = "mock",
    ) -> MotherOperationalResult:
        if not isinstance(objective, str) or not objective.strip():
            raise ValueError("objective must be a non-empty string")

        if not isinstance(intent, str) or not intent.strip():
            raise ValueError("intent must be a non-empty string")

        if not isinstance(provider, str) or not provider.strip():
            raise ValueError("provider must be a non-empty string")

        objective = objective.strip()
        intent = intent.strip()
        provider = provider.strip()

        retrieval = self.memory_knowledge.retrieve(
            query=objective
        )

        memory_context = "\n".join(
            f"- {memory_id}"
            for memory_id in retrieval.memory_ids
        )

        knowledge_context = "\n".join(
            f"- {knowledge_id}"
            for knowledge_id in retrieval.knowledge_ids
        )

        prompt = self._build_prompt(
            objective=objective,
            intent=intent,
            memory_context=memory_context,
            knowledge_context=knowledge_context,
        )

        model_result = self.model.generate(
            objective=objective,
            intent=intent,
            prompt=prompt,
            provider=provider,
        )

        if not model_result.success:
            return MotherOperationalResult(
                success=False,
                response=model_result.response_text,
                memory_ids=tuple(retrieval.memory_ids),
                knowledge_ids=tuple(retrieval.knowledge_ids),
                verification_status="FAILED",
                provider=provider,
            )

        reasoning_result = OperationalReasoningResult(
            success=model_result.success,
            user_input=objective,
            intent=intent,
            action="approved_cognitive_response",
            reasoning_response="Mother Brain approved cognitive processing.",
            model_response=model_result.response_text,
            model_provider=model_result.provider,
            model=model_result.model,
            requires_confirmation=False,
            verification_status="VERIFIED",
        )

        verification = self.verification.verify_reasoning(
            reasoning_result
        )

        if not verification.success:
            return MotherOperationalResult(
                success=False,
                response=verification.reason,
                memory_ids=tuple(retrieval.memory_ids),
                knowledge_ids=tuple(retrieval.knowledge_ids),
                verification_status=verification.verification_status,
                provider=provider,
            )

        return MotherOperationalResult(
            success=True,
            response=verification.result,
            memory_ids=tuple(retrieval.memory_ids),
            knowledge_ids=tuple(retrieval.knowledge_ids),
            verification_status=verification.verification_status,
            provider=provider,
        )

    @staticmethod
    def _build_prompt(
        *,
        objective: str,
        intent: str,
        memory_context: str,
        knowledge_context: str,
    ) -> str:
        return (
            "You are the local cognitive engine operating inside SAHIBEX Mother Brain.\n"
            "AUTHORITATIVE SAHIBEX IDENTITY: SAHIBEX is the user's own personal AI Main Brain / AI operating system. "
            "It is model-independent: local or external models are cognitive engines under SAHIBEX control, not SAHIBEX itself. "
            "SAHIBEX owns the authority boundary, memory, planning, verification, security, tools, execution orchestration, and specialist-child-brain lifecycle.\n"
            "Never redefine SAHIBEX as a company, product, person, or external AI provider. "
            "Never claim authority to bypass SAHIBEX permission or constitution controls.\n\n"
            f"Intent: {intent}\n"
            f"Objective: {objective}\n\n"
            "Relevant local memory IDs:\n"
            f"{memory_context or '(none)'}\n\n"
            "Relevant local knowledge IDs:\n"
            f"{knowledge_context or '(none)'}\n\n"
            "Provide the best cognitive response to the objective. "
            "Do not claim authority to execute protected actions."
        )
