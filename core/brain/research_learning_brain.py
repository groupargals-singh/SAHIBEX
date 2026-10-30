from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from core.brain.research_learning_command import (
    DepartmentOperation,
    ResearchLearningCommander,
)

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

    @staticmethod
    def normalize_research_query(request: str) -> str:
        """Remove common command framing before sending the topic to search.

        MainBrain receives natural-language commands such as ``Search the
        internet for X``. Passing the whole command to a search backend can
        change retrieval and select irrelevant publishers. This parser only
        removes a recognized leading command phrase; it never invents a topic.
        """
        if not isinstance(request, str):
            raise TypeError("research request must be str")
        query = " ".join(request.strip().split())
        if not query:
            raise ValueError("research request must not be empty")
        patterns = (
            r"^(?:please\s+)?search\s+the\s+internet\s+for(?:\s+|$)",
            r"^(?:please\s+)?search\s+online\s+for\s+",
            r"^(?:please\s+)?search\s+for\s+",
            r"^(?:please\s+)?look\s+up\s+",
            r"^(?:please\s+)?find\s+information\s+about\s+",
            r"^(?:please\s+)?research\s+",
            r"^internet\s+par\s+(?:search|khoj)\s+(?:karo|kijiye|karen)\s*",
            r"^(?:please\s+)?(?:इंटरनेट\s+पर\s+)?(?:खोजो|खोजिए|सर्च\s+करो|रिसर्च\s+करो)\s*",
            r"^(?:कृपया\s+)?(?:के\s+बारे\s+में\s+)?जानकारी\s+खोजो\s*",
        )
        for pattern in patterns:
            updated = re.sub(pattern, "", query, count=1, flags=re.IGNORECASE).strip()
            if updated != query:
                query = updated
                break
        query = query.rstrip(" .!?।")
        if not query:
            raise ValueError("research request did not contain a topic")
        return query

    def __init__(
        self,
        *,
        research: MotherResearchIntegration,
        learning: MotherLearningIntegration | None = None,
    ) -> None:
        if not isinstance(research, MotherResearchIntegration):
            raise TypeError("research must be MotherResearchIntegration")
        self.research = research
        self.commander = ResearchLearningCommander()
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
        query = self.normalize_research_query(query)
        command = self.commander.dispatch(
            DepartmentOperation.RESEARCH,
            query,
            lambda: self.research.research(
                query=query,
                confirmation=confirmation,
            ),
        )
        result = command.result
        verified = bool(
            result.success
            and result.verification_status == "VERIFIED"
        )
        return ResearchLearningResult(
            success=verified,
            operation="research",
            result=result,
            verified=verified,
            # A successful-looking result without the verification marker must
            # never be reported as persisted trusted knowledge.
            persisted=verified,
        )

    def learn_topic(
        self,
        topic: str,
        *,
        confirmation: bool = False,
    ) -> ResearchLearningResult:
        command = self.commander.dispatch(
            DepartmentOperation.LEARN,
            topic,
            lambda: self.learning.learn(
                topic=topic,
                confirmation=confirmation,
            ),
        )
        result = command.result
        verified = (
            result.success
            and result.verification_status == "VERIFIED"
            and result.verified_knowledge_count > 0
        )
        return ResearchLearningResult(
            success=verified,
            operation="learn",
            result=result,
            verified=verified,
            # Require at least one verified knowledge item; `>= 0` was a bug
            # that incorrectly marked zero-item learning as persisted.
            persisted=verified and result.verified_knowledge_count > 0,
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
            "department_commander": True,
            "army_routing": True,
            "labour_pipeline_delegation": True,
            "dual_worker_execution": True,
            "joint_result_verification": True,
            "task_trace": True,
            "independent_worker_models": False,
            "child_brain_creation": False,
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
            "department_commander": True,
            "army_routing": True,
            "labour_pipeline_delegation": True,
            "dual_worker_execution": True,
            "joint_result_verification": True,
            "task_trace": True,
            "independent_worker_models": False,
            "child_brain_creation": False,
        }
