from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from statistics import mean
from typing import Any
from uuid import uuid4

from core.research.experience_memory import (
    ExperienceMemory,
    ExperienceMemoryStore,
)


class SkillStatus(str, Enum):
    PROPOSED = "proposed"
    TESTED = "tested"
    VERIFIED = "verified"
    ACTIVE = "active"
    RETIRED = "retired"
    ROLLED_BACK = "rolled_back"


class ImprovementKind(str, Enum):
    NEW_SKILL = "new_skill"
    SKILL_IMPROVEMENT = "skill_improvement"
    CAPABILITY_EXPANSION = "capability_expansion"


@dataclass(frozen=True)
class SkillVersion:
    skill_id: str
    version: int
    name: str
    description: str
    kind: ImprovementKind
    status: SkillStatus
    source_experience_ids: tuple[str, ...]
    confidence: float
    security_passed: bool = False
    regression_passed: bool = False
    verification_passed: bool = False
    mother_approved: bool = False
    human_approved: bool = False
    predecessor_version: int | None = None
    created_at: str = ""


@dataclass(frozen=True)
class LearningAnalysis:
    experience_count: int
    success_count: int
    failure_count: int
    success_rate: float
    failure_rate: float
    lessons: tuple[str, ...]
    repeated_failure_tasks: tuple[str, ...]


@dataclass(frozen=True)
class ImprovementProposal:
    proposal_id: str
    skill_id: str
    version: int
    kind: ImprovementKind
    reason: str
    expected_benefit: str
    expected_risk: str
    protected_update: bool
    status: SkillStatus


class ContinuousLearningImprovement:
    """
    Phase-10 runtime: Continuous Learning & Improvement.

    This is a controlled learning/skill registry, not an unrestricted
    self-modifying code executor. It collects experience, analyzes
    outcomes, creates skill/capability proposals, tests them before
    activation, supports versioned rollback, and requires Mother +
    human approval for protected updates.

    Constitution and human authority are immutable from this layer.
    """

    VERSION = "PHASE-10-1.0"

    def __init__(self, *, experience_capacity: int = 512) -> None:
        self.experience = ExperienceMemoryStore(capacity=experience_capacity)
        self._skills: dict[str, list[SkillVersion]] = {}
        self._proposals: dict[str, ImprovementProposal] = {}

    # ------------------------------------------------------------------
    # Experience collection and outcome analysis
    # ------------------------------------------------------------------

    def record_experience(
        self,
        *,
        task: str,
        context: str,
        action_taken: str,
        outcome: str,
        lesson: str,
        success: bool,
        source: str = "master_brain",
        confidence: float = 0.7,
        importance: float = 0.7,
        tags: list[str] | None = None,
        provenance: dict[str, Any] | None = None,
    ) -> ExperienceMemory:
        experience = ExperienceMemory(
            experience_id=f"experience-{uuid4()}",
            task=task,
            context=context,
            action_taken=action_taken,
            outcome=outcome,
            lesson=lesson,
            source=source,
            success=success,
            confidence=confidence,
            importance=importance,
            tags=list(tags or []),
            provenance=dict(provenance or {}),
        )
        return self.experience.store(experience)

    def analyze_outcomes(self) -> LearningAnalysis:
        all_items = self.experience.all()
        successes = tuple(item for item in all_items if item.success)
        failures = tuple(item for item in all_items if not item.success)

        repeated: dict[str, int] = {}
        for item in failures:
            key = item.task.strip().lower()
            repeated[key] = repeated.get(key, 0) + 1

        repeated_failure_tasks = tuple(
            task for task, count in sorted(repeated.items())
            if count >= 2
        )

        total = len(all_items)
        success_rate = (len(successes) / total) if total else 0.0

        return LearningAnalysis(
            experience_count=total,
            success_count=len(successes),
            failure_count=len(failures),
            success_rate=round(success_rate, 6),
            failure_rate=round(1.0 - success_rate, 6) if total else 0.0,
            lessons=tuple(item.lesson for item in all_items),
            repeated_failure_tasks=repeated_failure_tasks,
        )

    # ------------------------------------------------------------------
    # Skill generation, improvement and capability expansion
    # ------------------------------------------------------------------

    def propose_skill(
        self,
        *,
        name: str,
        description: str,
        kind: ImprovementKind,
        source_experience_ids: tuple[str, ...] = (),
        reason: str = "",
        expected_benefit: str = "",
        expected_risk: str = "",
        protected_update: bool = True,
        skill_id: str | None = None,
    ) -> ImprovementProposal:
        if not name.strip() or not description.strip():
            raise ValueError("skill name and description are required")

        if not isinstance(kind, ImprovementKind):
            raise TypeError("kind must be ImprovementKind")

        for experience_id in source_experience_ids:
            if not self.experience.contains(experience_id):
                raise ValueError(f"unknown source experience: {experience_id}")

        selected_id = skill_id or f"skill-{uuid4()}"
        versions = self._skills.get(selected_id, [])
        next_version = (versions[-1].version + 1) if versions else 1
        predecessor = versions[-1].version if versions else None

        skill = SkillVersion(
            skill_id=selected_id,
            version=next_version,
            name=name.strip(),
            description=description.strip(),
            kind=kind,
            status=SkillStatus.PROPOSED,
            source_experience_ids=tuple(source_experience_ids),
            confidence=0.0,
            predecessor_version=predecessor,
        )
        self._skills.setdefault(selected_id, []).append(skill)

        proposal = ImprovementProposal(
            proposal_id=f"learning-proposal-{uuid4()}",
            skill_id=selected_id,
            version=next_version,
            kind=kind,
            reason=reason.strip(),
            expected_benefit=expected_benefit.strip(),
            expected_risk=expected_risk.strip(),
            protected_update=protected_update,
            status=SkillStatus.PROPOSED,
        )
        self._proposals[proposal.proposal_id] = proposal
        return proposal

    def test_skill(
        self,
        proposal_id: str,
        *,
        security_passed: bool,
        regression_passed: bool,
        verification_passed: bool,
        confidence: float = 0.8,
    ) -> SkillVersion:
        proposal = self._get_proposal(proposal_id)
        skill = self._get_version(proposal.skill_id, proposal.version)

        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if not (security_passed and regression_passed and verification_passed):
            updated = replace(
                skill,
                status=SkillStatus.RETIRED,
                security_passed=security_passed,
                regression_passed=regression_passed,
                verification_passed=verification_passed,
                confidence=confidence,
            )
        else:
            updated = replace(
                skill,
                status=SkillStatus.VERIFIED,
                security_passed=True,
                regression_passed=True,
                verification_passed=True,
                confidence=confidence,
            )

        self._replace_version(updated)
        self._proposals[proposal_id] = replace(
            proposal,
            status=updated.status,
        )
        return updated

    def approve_protected_update(
        self,
        proposal_id: str,
        *,
        mother_approved: bool,
        human_approved: bool,
    ) -> SkillVersion:
        proposal = self._get_proposal(proposal_id)
        skill = self._get_version(proposal.skill_id, proposal.version)

        if skill.status != SkillStatus.VERIFIED:
            raise PermissionError(
                "Skill must pass security, regression and verification before approval."
            )

        if proposal.protected_update and not mother_approved:
            raise PermissionError("Mother approval is required.")

        if proposal.protected_update and not human_approved:
            raise PermissionError("Human approval is required for protected self-update.")

        updated = replace(
            skill,
            status=SkillStatus.TESTED,
            mother_approved=mother_approved,
            human_approved=human_approved,
        )
        self._replace_version(updated)
        self._proposals[proposal_id] = replace(
            proposal,
            status=SkillStatus.TESTED,
        )
        return updated

    def activate_skill(self, proposal_id: str) -> SkillVersion:
        proposal = self._get_proposal(proposal_id)
        skill = self._get_version(proposal.skill_id, proposal.version)

        if skill.status != SkillStatus.TESTED:
            raise PermissionError("Approved and tested skill is required before activation.")

        if proposal.protected_update and not (
            skill.mother_approved and skill.human_approved
        ):
            raise PermissionError("Protected skill activation requires Mother + human approval.")

        active_versions = self._skills.get(skill.skill_id, [])
        for existing in active_versions:
            if existing.status == SkillStatus.ACTIVE:
                self._replace_version(
                    replace(existing, status=SkillStatus.ROLLED_BACK)
                )

        activated = replace(skill, status=SkillStatus.ACTIVE)
        self._replace_version(activated)
        self._proposals[proposal_id] = replace(
            proposal,
            status=SkillStatus.ACTIVE,
        )
        return activated

    # ------------------------------------------------------------------
    # Rollback / recovery
    # ------------------------------------------------------------------

    def rollback_skill(
        self,
        skill_id: str,
        *,
        target_version: int | None = None,
        mother_approved: bool = False,
        human_approved: bool = False,
        verification_passed: bool = False,
    ) -> SkillVersion:
        versions = self._skills.get(skill_id)
        if not versions:
            raise ValueError("unknown skill")

        if not mother_approved or not human_approved:
            raise PermissionError("Rollback requires Mother + human approval.")

        if not verification_passed:
            raise PermissionError("Rollback requires restoration verification.")

        current = next(
            (item for item in versions if item.status == SkillStatus.ACTIVE),
            None,
        )
        if current is None:
            raise ValueError("skill has no active version")

        candidates = [
            item for item in versions
            if item.version < current.version
            and item.status in {
                SkillStatus.ROLLED_BACK,
                SkillStatus.VERIFIED,
            }
        ]
        if target_version is not None:
            candidates = [
                item for item in candidates
                if item.version == target_version
            ]

        if not candidates:
            raise ValueError("no trusted previous skill version available")

        target = max(candidates, key=lambda item: item.version)

        self._replace_version(replace(current, status=SkillStatus.ROLLED_BACK))
        restored = replace(
            target,
            status=SkillStatus.ACTIVE,
            mother_approved=True,
            human_approved=True,
            verification_passed=True,
        )
        self._replace_version(restored)
        return restored

    # ------------------------------------------------------------------
    # Read-only safety/capability contracts
    # ------------------------------------------------------------------

    def active_skill(self, skill_id: str) -> SkillVersion | None:
        for skill in self._skills.get(skill_id, []):
            if skill.status == SkillStatus.ACTIVE:
                return skill
        return None

    def skill_versions(self, skill_id: str) -> tuple[SkillVersion, ...]:
        return tuple(self._skills.get(skill_id, ()))

    def proposal(self, proposal_id: str) -> ImprovementProposal:
        return self._get_proposal(proposal_id)

    def capability_contract(self) -> dict[str, bool]:
        return {
            "experience_collection": True,
            "success_failure_analysis": True,
            "skill_improvement": True,
            "new_skill_generation": True,
            "skill_testing_before_use": True,
            "capability_expansion": True,
            "regression_testing": True,
            "rollback": True,
            "protected_self_update_approval": True,
            "constitution_self_modification": False,
            "self_authorization": False,
            "uncontrolled_live_code_execution": False,
        }

    def can_modify_constitution(self) -> bool:
        return False

    def can_self_authorize_protected_update(self) -> bool:
        return False

    def can_execute_unapproved_update(self) -> bool:
        return False

    def protected_update_requires_mother_and_human(self) -> bool:
        return True

    def regression_required_before_activation(self) -> bool:
        return True

    def verification_required_before_activation(self) -> bool:
        return True

    def rollback_requires_verification(self) -> bool:
        return True

    def _get_proposal(self, proposal_id: str) -> ImprovementProposal:
        try:
            return self._proposals[proposal_id]
        except KeyError as exc:
            raise ValueError("unknown improvement proposal") from exc

    def _get_version(self, skill_id: str, version: int) -> SkillVersion:
        for skill in self._skills.get(skill_id, []):
            if skill.version == version:
                return skill
        raise ValueError("unknown skill version")

    def _replace_version(self, updated: SkillVersion) -> None:
        versions = self._skills[updated.skill_id]
        for index, existing in enumerate(versions):
            if existing.version == updated.version:
                versions[index] = updated
                return
        raise ValueError("unknown skill version")
