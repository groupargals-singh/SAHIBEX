from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.brain.mother_learning_integration import (
    MotherLearningIntegration,
    MotherLearningResult,
)
from core.brain.mother_research_integration import (
    MotherResearchIntegration,
    MotherResearchResult,
)


@dataclass(frozen=True)
class ResearchLearningResult:
    """Unified Research & Learning Brain result."""

    success: bool
    operation: str
    result: Any
    verified: bool
    persisted: bool

    @property
    def error(self) -> str:
        return str(getattr(self.result, "error", "") or "")


class ResearchLearningBrain:
    """SAHIBEX Research & Learning Brain boundary.

    Research and learning remain delegated to the existing, tested
    Mother research/learning pipelines. This facade gives the Main Brain
    one stable capability boundary without creating a second authority.

    It never grants permission, executes protected actions, or changes
    the Constitution.
    """

    VERSION = "1.0"

    def __init__(
        self,
        *,
        research: MotherResearchIntegration,
        learning: MotherLearningIntegration | None = None,
    ) -> None:
        if not isinstance(research, MotherResearchIntegration):
            raise TypeError("research must be MotherResearchIntegration")
        self.research = research
        self.learning = (
            learning
            if learning is not None
            else MotherLearningIntegration(research=research)
        )

    def research_topic(
        self,
        query: str,
        *,
        confirmation: bool = False,
    ) -> ResearchLearningResult:
        result = self.research.research(
            query=query,
            confirmation=confirmation,
        )
        return ResearchLearningResult(
            success=result.success,
            operation="research",
            result=result,
            verified=result.verification_status == "VERIFIED",
            persisted=bool(result.success),
        )

    def learn_topic(
        self,
        topic: str,
        *,
        confirmation: bool = False,
    ) -> ResearchLearningResult:
        result = self.learning.learn(
            topic=topic,
            confirmation=confirmation,
        )
        verified = (
            result.success
            and result.verification_status == "VERIFIED"
            and result.verified_knowledge_count > 0
        )
        return ResearchLearningResult(
            success=result.success,
            operation="learn",
            result=result,
            verified=verified,
            persisted=bool(result.success and result.knowledge_count >= 0),
        )

    def capability_contract(self) -> dict[str, bool]:
        return {
            "research": True,
            "learning": True,
            "evidence_pipeline": True,
            "source_verification": True,
            "conflict_awareness": True,
            "knowledge_persistence": True,
            "permission_authority": False,
            "execution_authority": False,
            "constitution_mutation": False,
        }

    def summary(self) -> dict[str, object]:
        return {
            "version": self.VERSION,
            "research": True,
            "learning": True,
            "verified_evidence": True,
            "persistent_results": True,
            "permission_authority": False,
            "execution_authority": False,
            "constitution_mutation": False,
        }
