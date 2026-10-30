from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from statistics import mean
from typing import Any
from uuid import uuid4

from core.brain.self_improvement_state_store import SelfImprovementStateStore

from core.research.experience_memory import (
    ExperienceMemory,
    ExperienceMemoryStore,
)
from security.audit.child_self_improvement_audit_store import (
    ChildSelfImprovementAuditStore,
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

    VERSION = "PHASE-10-1.1"

    def __init__(
        self,
        *,
        experience_capacity: int = 512,
        audit_store: ChildSelfImprovementAuditStore | None = None,
        state_store: SelfImprovementStateStore | None = None,
    ) -> None:
        if audit_store is not None and not isinstance(
            audit_store, ChildSelfImprovementAuditStore
        ):
            raise TypeError("audit_store must be ChildSelfImprovementAuditStore or None")
        self.experience = ExperienceMemoryStore(capacity=experience_capacity)
        self._skills: dict[str, list[SkillVersion]] = {}
        self._proposals: dict[str, ImprovementProposal] = {}
        self.audit_store = audit_store
        if self.audit_store is not None and not self.audit_store.verify_chain():
            raise RuntimeError("self_improvement_audit_chain_invalid_on_startup")
        if state_store is not None and not isinstance(state_store, SelfImprovementStateStore):
            raise TypeError("state_store must be SelfImprovementStateStore or None")
        self.state_store = state_store
        if self.state_store is not None:
            persisted = self.state_store.load()
            if persisted is not None:
                self._restore_state(persisted)

    @staticmethod
    def _skill_to_dict(skill: SkillVersion) -> dict[str, Any]:
        data = dict(skill.__dict__)
        data["kind"] = skill.kind.value
        data["status"] = skill.status.value
        data["source_experience_ids"] = list(skill.source_experience_ids)
        return data

    @staticmethod
    def _skill_from_dict(data: dict[str, Any]) -> SkillVersion:
        item = dict(data)
        item["kind"] = ImprovementKind(item["kind"])
        item["status"] = SkillStatus(item["status"])
        item["source_experience_ids"] = tuple(item.get("source_experience_ids", ()))
        return SkillVersion(**item)

    @staticmethod
    def _proposal_to_dict(proposal: ImprovementProposal) -> dict[str, Any]:
        data = dict(proposal.__dict__)
        data["kind"] = proposal.kind.value
        data["status"] = proposal.status.value
        return data

    @staticmethod
    def _proposal_from_dict(data: dict[str, Any]) -> ImprovementProposal:
        item = dict(data)
        item["kind"] = ImprovementKind(item["kind"])
        item["status"] = SkillStatus(item["status"])
        return ImprovementProposal(**item)

    def _persist_state(self) -> None:
        if self.state_store is None:
            return
        state = {
            "skills": [self._skill_to_dict(skill) for versions in self._skills.values() for skill in versions],
            "proposals": [self._proposal_to_dict(item) for item in self._proposals.values()],
        }
        self.state_store.save(state)

    def _restore_state(self, state: dict[str, Any]) -> None:
        skills: dict[str, list[SkillVersion]] = {}
        proposals: dict[str, ImprovementProposal] = {}
        try:
            for raw in state["skills"]:
                skill = self._skill_from_dict(raw)
                skills.setdefault(skill.skill_id, []).append(skill)
            for versions in skills.values():
                versions.sort(key=lambda item: item.version)
                active = [item for item in versions if item.status == SkillStatus.ACTIVE]
                if len(active) > 1:
                    raise ValueError("multiple active versions for one skill")
                if len({item.version for item in versions}) != len(versions):
                    raise ValueError("duplicate skill version")
            for raw in state["proposals"]:
                proposal = self._proposal_from_dict(raw)
                if proposal.proposal_id in proposals:
                    raise ValueError("duplicate proposal id")
                if not any(item.version == proposal.version for item in skills.get(proposal.skill_id, [])):
                    raise ValueError("proposal references missing skill version")
                proposals[proposal.proposal_id] = proposal
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("self_improvement_state_schema_invalid") from exc
        self._skills = skills
        self._proposals = proposals

    def _audit_event(
        self,
        event: str,
        *,
        decision: str,
        reason: str,
        proposal: ImprovementProposal | None = None,
        skill_id: str | None = None,
        version_before: int | None = None,
        version_after: int | None = None,
        security_passed: bool | None = None,
        regression_passed: bool | None = None,
        verification_passed: bool | None = None,
        mother_approved: bool | None = None,
        human_approved: bool | None = None,
    ) -> None:
        """Persist lifecycle decisions before reporting them as successful.

        Production callers configure a durable append-only store. Tests and
        explicitly isolated callers may omit it; no authority is granted here.
        """
        if self.audit_store is None:
            return
        if not self.audit_store.verify_chain():
            raise RuntimeError("self_improvement_audit_chain_invalid")
        resolved_skill_id = skill_id or (proposal.skill_id if proposal else "")
        resolved_version = version_after if version_after is not None else (proposal.version if proposal else None)
        audit_id = f"self-improvement:{event}:{uuid4()}"
        self.audit_store.append(
            audit_id=audit_id,
            payload={
                "event": event,
                "decision": decision,
                "reason": reason,
                "proposal_id": proposal.proposal_id if proposal else None,
                "skill_id": resolved_skill_id,
                "version_before": str(version_before) if version_before is not None else None,
                "version_after": str(resolved_version) if resolved_version is not None else None,
                "protected_update": proposal.protected_update if proposal else True,
                "mother_approved": mother_approved,
                "human_approved": human_approved,
                "security_passed": security_passed,
                "regression_passed": regression_passed,
                "verification_passed": verification_passed,
                "constitution_changed": False,
                "authority_changed": False,
            },
        )
        if not self.audit_store.verify_chain():
            raise RuntimeError("self_improvement_audit_chain_invalid_after_append")

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
        self._audit_event(
            "proposal_created",
            decision="accept",
            reason=proposal.reason or "proposal created for review",
            proposal=proposal,
            version_before=predecessor,
            version_after=next_version,
        )
        self._skills.setdefault(selected_id, []).append(skill)
        self._proposals[proposal.proposal_id] = proposal
        self._persist_state()
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

        self._audit_event(
            "proposal_tests_completed",
            decision="accept" if updated.status == SkillStatus.VERIFIED else "block",
            reason="security, regression and verification gates evaluated",
            proposal=proposal,
            version_before=skill.predecessor_version,
            version_after=skill.version,
            security_passed=security_passed,
            regression_passed=regression_passed,
            verification_passed=verification_passed,
        )
        self._replace_version(updated)
        self._proposals[proposal_id] = replace(
            proposal,
            status=updated.status,
        )
        self._persist_state()
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
            self._audit_event(
                "approval_blocked", decision="block",
                reason="skill has not passed security, regression and verification",
                proposal=proposal, version_after=skill.version,
                mother_approved=mother_approved, human_approved=human_approved,
            )
            raise PermissionError(
                "Skill must pass security, regression and verification before approval."
            )

        if proposal.protected_update and not mother_approved:
            self._audit_event(
                "approval_blocked", decision="block", reason="Mother approval missing",
                proposal=proposal, version_after=skill.version,
                mother_approved=False, human_approved=human_approved,
            )
            raise PermissionError("Mother approval is required.")

        if proposal.protected_update and not human_approved:
            self._audit_event(
                "approval_blocked", decision="block", reason="explicit human approval missing",
                proposal=proposal, version_after=skill.version,
                mother_approved=mother_approved, human_approved=False,
            )
            raise PermissionError("Human approval is required for protected self-update.")

        self._audit_event(
            "approval_granted", decision="accept", reason="Mother and human approvals recorded",
            proposal=proposal, version_after=skill.version,
            mother_approved=mother_approved, human_approved=human_approved,
            security_passed=skill.security_passed,
            regression_passed=skill.regression_passed,
            verification_passed=skill.verification_passed,
        )
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
        self._persist_state()
        return updated

    def activate_skill(self, proposal_id: str) -> SkillVersion:
        proposal = self._get_proposal(proposal_id)
        skill = self._get_version(proposal.skill_id, proposal.version)

        if skill.status != SkillStatus.TESTED:
            self._audit_event(
                "activation_blocked", decision="block",
                reason="approved tested version required", proposal=proposal,
                version_after=skill.version,
            )
            raise PermissionError("Approved and tested skill is required before activation.")

        if proposal.protected_update and not (
            skill.mother_approved and skill.human_approved
        ):
            self._audit_event(
                "activation_blocked", decision="block",
                reason="Mother and explicit human approval are both required",
                proposal=proposal, version_after=skill.version,
                mother_approved=skill.mother_approved,
                human_approved=skill.human_approved,
            )
            raise PermissionError("Protected skill activation requires Mother + human approval.")

        active_versions = self._skills.get(skill.skill_id, [])
        previous_versions = list(active_versions)
        previous_proposal = self._proposals[proposal_id]
        previous_active = next(
            (item for item in active_versions if item.status == SkillStatus.ACTIVE),
            None,
        )
        self._audit_event(
            "activation_started", decision="accept",
            reason="all pre-activation gates passed", proposal=proposal,
            version_before=previous_active.version if previous_active else skill.predecessor_version,
            version_after=skill.version,
            security_passed=skill.security_passed,
            regression_passed=skill.regression_passed,
            verification_passed=skill.verification_passed,
            mother_approved=skill.mother_approved,
            human_approved=skill.human_approved,
        )
        try:
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
            self._persist_state()
            self._audit_event(
                "activation_committed", decision="accept",
                reason="metadata-only skill version activated", proposal=proposal,
                version_before=previous_active.version if previous_active else skill.predecessor_version,
                version_after=skill.version,
                security_passed=skill.security_passed,
                regression_passed=skill.regression_passed,
                verification_passed=skill.verification_passed,
                mother_approved=skill.mother_approved,
                human_approved=skill.human_approved,
            )
            return activated
        except Exception:
            active_versions[:] = previous_versions
            self._proposals[proposal_id] = previous_proposal
            try:
                self._persist_state()
            except Exception:
                pass
            try:
                self._audit_event(
                    "activation_recovery", decision="block",
                    reason="activation failed; prior in-memory version state restored",
                    proposal=proposal,
                    version_before=previous_active.version if previous_active else skill.predecessor_version,
                    version_after=skill.version,
                    mother_approved=skill.mother_approved,
                    human_approved=skill.human_approved,
                )
            except Exception:
                # Preserve the original failure; the hash chain is already
                # checked before every subsequent lifecycle operation.
                pass
            raise

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
            self._audit_event(
                "rollback_blocked", decision="block", reason="unknown skill",
                skill_id=skill_id,
            )
            raise ValueError("unknown skill")

        current = next(
            (item for item in versions if item.status == SkillStatus.ACTIVE),
            None,
        )
        if not mother_approved or not human_approved:
            self._audit_event(
                "rollback_blocked", decision="block",
                reason="Mother and explicit human approval required",
                skill_id=skill_id,
                version_before=current.version if current else None,
                version_after=target_version,
                mother_approved=mother_approved,
                human_approved=human_approved,
            )
            raise PermissionError("Rollback requires Mother + human approval.")

        if not verification_passed:
            self._audit_event(
                "rollback_blocked", decision="block",
                reason="restoration verification missing",
                skill_id=skill_id,
                version_before=current.version if current else None,
                version_after=target_version,
                mother_approved=mother_approved,
                human_approved=human_approved,
                verification_passed=False,
            )
            raise PermissionError("Rollback requires restoration verification.")

        current = next(
            (item for item in versions if item.status == SkillStatus.ACTIVE),
            None,
        )
        if current is None:
            self._audit_event(
                "rollback_blocked", decision="block", reason="skill has no active version",
                skill_id=skill_id,
                mother_approved=mother_approved, human_approved=human_approved,
                verification_passed=verification_passed,
            )
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
            self._audit_event(
                "rollback_blocked", decision="block",
                reason="no trusted previous version available",
                skill_id=skill_id, version_before=current.version,
                version_after=target_version,
                mother_approved=mother_approved, human_approved=human_approved,
                verification_passed=verification_passed,
            )
            raise ValueError("no trusted previous skill version available")

        target = max(candidates, key=lambda item: item.version)
        previous_versions = list(versions)
        self._audit_event(
            "rollback_started", decision="accept",
            reason="approved rollback to a trusted prior version",
            skill_id=skill_id, version_before=current.version,
            version_after=target.version,
            mother_approved=mother_approved, human_approved=human_approved,
            verification_passed=verification_passed,
        )
        try:
            self._replace_version(replace(current, status=SkillStatus.ROLLED_BACK))
            restored = replace(
                target,
                status=SkillStatus.ACTIVE,
                mother_approved=True,
                human_approved=True,
                verification_passed=True,
            )
            self._replace_version(restored)
            self._persist_state()
            self._audit_event(
                "rollback_completed", decision="accept",
                reason="prior trusted version restored and verified",
                skill_id=skill_id, version_before=current.version,
                version_after=target.version,
                mother_approved=mother_approved, human_approved=human_approved,
                verification_passed=verification_passed,
            )
            return restored
        except Exception:
            versions[:] = previous_versions
            try:
                self._persist_state()
            except Exception:
                pass
            try:
                self._audit_event(
                    "rollback_recovery", decision="block",
                    reason="rollback could not be verified; previous state restored",
                    skill_id=skill_id, version_before=current.version,
                    version_after=target.version,
                    mother_approved=mother_approved, human_approved=human_approved,
                    verification_passed=verification_passed,
                )
            except Exception:
                pass
            raise

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
            "persistent_audit": self.audit_store is not None,
            "persistent_skill_registry": self.state_store is not None,
            "restart_recovery": self.state_store is not None,
            "fail_closed_on_audit_tamper": self.audit_store is not None,
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
