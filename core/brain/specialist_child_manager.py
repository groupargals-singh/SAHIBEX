from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
from uuid import uuid4

from core.brain.brain_registry import BrainRegistry
from core.brain.child_brain_core import ChildBrainCore
from core.brain.child_communication_runtime import ChildCommunicationRuntime
from core.brain.child_memory_runtime import ChildMemoryRuntime
from core.brain.child_runtime_state import (
    ChildRuntimeState,
    ChildRuntimeStateManager,
)
from core.brain.operational_specialist_dispatch import (
    OperationalSpecialistDispatcher,
    SpecialistDispatchResult,
)
from core.brain.specialist_brain import (
    BrainCapability,
    BrainStatus,
    SpecialistBrain,
)
from core.policies.constitution import BrainRole
from core.brain.verification import BrainTrustStatus


@dataclass
class ChildPerformance:
    completed: int = 0
    failed: int = 0
    verified: int = 0
    last_success: bool | None = None
    last_error: str | None = None

    @property
    def total(self) -> int:
        return self.completed + self.failed

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.completed / self.total


@dataclass
class SpecialistChildRecord:
    brain: SpecialistBrain
    runtime_state: ChildRuntimeState
    memory: ChildMemoryRuntime
    core: ChildBrainCore
    communication: ChildCommunicationRuntime
    performance: ChildPerformance = field(
        default_factory=ChildPerformance
    )
    predecessor_brain_id: str | None = None
    trust_lineage_id: str = field(default_factory=lambda: str(uuid4()))


SpecialistHandler = Callable[[str, dict[str, Any]], Any]


class SpecialistChildBrainManager:
    """
    Real Phase-9 runtime boundary for SAHIBEX specialist Child Brains.

    This manager owns Child-Brain registration, lifecycle, specialist
    capability assignment, isolated memory, parent/child communication,
    trust state, performance tracking, suspension, retirement and
    replacement.

    It never grants constitutional authority. Protected execution still
    belongs to the Mother Brain permission/tool pipeline.
    """

    VERSION = "1.0"

    SPECIALIST_PROFILES: dict[str, frozenset[BrainCapability]] = {
        "research": frozenset({
            BrainCapability.THINK,
            BrainCapability.RESEARCH,
            BrainCapability.ANALYZE,
            BrainCapability.VERIFY,
            BrainCapability.READ,
        }),
        "coding": frozenset({
            BrainCapability.THINK,
            BrainCapability.ANALYZE,
            BrainCapability.CODE,
            BrainCapability.CREATE,
            BrainCapability.VERIFY,
            BrainCapability.READ,
        }),
        "trading": frozenset({
            BrainCapability.THINK,
            BrainCapability.RESEARCH,
            BrainCapability.ANALYZE,
            BrainCapability.VERIFY,
            BrainCapability.PLAN,
            BrainCapability.READ,
        }),
        "business": frozenset({
            BrainCapability.THINK,
            BrainCapability.RESEARCH,
            BrainCapability.ANALYZE,
            BrainCapability.CREATE,
            BrainCapability.PLAN,
            BrainCapability.VERIFY,
            BrainCapability.READ,
        }),
        "computer-control": frozenset({
            BrainCapability.THINK,
            BrainCapability.ANALYZE,
            BrainCapability.PLAN,
            BrainCapability.VERIFY,
            BrainCapability.READ,
        }),
    }

    REQUIRED_CAPABILITY_BY_SPECIALIZATION: dict[str, BrainCapability] = {
        "research": BrainCapability.RESEARCH,
        "coding": BrainCapability.CODE,
        "trading": BrainCapability.ANALYZE,
        "business": BrainCapability.PLAN,
        "computer-control": BrainCapability.PLAN,
    }

    def __init__(self, *, registry: BrainRegistry | None = None) -> None:
        self.registry = registry or BrainRegistry()
        self._ensure_mother_identity()
        self.dispatcher = OperationalSpecialistDispatcher(self.registry)
        self._records: dict[str, SpecialistChildRecord] = {}
        self._runtime = ChildRuntimeStateManager()

    def _ensure_mother_identity(self) -> SpecialistBrain:
        existing = self.registry.get_mother_brain()
        if existing is not None:
            return existing
        mother = SpecialistBrain(
            name="SAHIBEX Mother Brain",
            description="Registry identity for the SAHIBEX constitutional root",
            specialization="mother",
            capabilities={
                BrainCapability.THINK,
                BrainCapability.RESEARCH,
                BrainCapability.ANALYZE,
                BrainCapability.VERIFY,
                BrainCapability.PLAN,
                BrainCapability.READ,
            },
            brain_id="sahibex-master-brain",
            brain_role=BrainRole.MOTHER_BRAIN,
        )
        self.registry.register(mother)
        mother.transition_to(BrainStatus.READY)
        mother.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="SAHIBEX root identity binding verified",
        )
        return mother

    @classmethod
    def specialist_profiles(cls) -> dict[str, frozenset[BrainCapability]]:
        return dict(cls.SPECIALIST_PROFILES)

    def create_child(
        self,
        *,
        name: str,
        description: str,
        specialization: str,
        capabilities: set[BrainCapability] | None = None,
        mother_approved: bool = False,
        human_approved: bool = False,
        parent_brain_id: str | None = None,
    ) -> SpecialistChildRecord:
        if not mother_approved or not human_approved:
            raise PermissionError(
                "Child creation requires Mother and human approval."
            )

        parent = (
            self.registry.get_mother_brain()
            if parent_brain_id is None
            else self.registry.get(parent_brain_id)
        )
        if parent is None:
            raise ValueError("A registered Mother Brain parent is required.")
        if parent.brain_role != BrainRole.MOTHER_BRAIN:
            raise ValueError("A Child Brain must be directly owned by Mother Brain.")

        normalized_specialization = specialization.strip().lower()
        assigned = set(capabilities or self.SPECIALIST_PROFILES.get(
            normalized_specialization,
            frozenset({BrainCapability.THINK, BrainCapability.READ}),
        ))
        if not assigned:
            raise ValueError("At least one cognitive capability is required.")

        brain = SpecialistBrain(
            name=name,
            description=description,
            specialization=specialization,
            capabilities=assigned,
            brain_role=BrainRole.CHILD_BRAIN,
            parent_brain_id=parent.brain_id,
        )

        # Build the runtime record and pass through every declared lifecycle
        # state. Do not jump CREATED -> READY or register a partially born child.
        memory = ChildMemoryRuntime(
            child_brain_id=brain.brain_id,
            memory_namespace=brain.memory_namespace,
        )
        record = SpecialistChildRecord(
            brain=brain,
            runtime_state=ChildRuntimeState.CREATED,
            memory=memory,
            core=ChildBrainCore(),
            communication=ChildCommunicationRuntime(),
        )

        # Birth lifecycle verification does not itself establish trust.
        # Trust stays UNVERIFIED until a separate evidence-backed approval.
        verified = self._runtime.transition(
            record.runtime_state,
            ChildRuntimeState.VERIFIED,
            authority_approved=True,
            verification_passed=True,
        )
        if not verified.allowed:
            raise ValueError(verified.reason)
        record.runtime_state = ChildRuntimeState.VERIFIED

        ready = self._runtime.transition(
            record.runtime_state,
            ChildRuntimeState.READY,
            authority_approved=True,
            verification_passed=True,
        )
        if not ready.allowed:
            raise ValueError(ready.reason)
        brain.transition_to(BrainStatus.READY)
        record.runtime_state = ChildRuntimeState.READY

        # Register only after birth verification and the full lifecycle sequence.
        self.registry.register(brain)
        self._records[brain.brain_id] = record
        return record

    def get(self, brain_id: str) -> SpecialistChildRecord | None:
        return self._records.get(brain_id)

    def list_children(self, specialization: str | None = None) -> list[SpecialistChildRecord]:
        records = list(self._records.values())
        if specialization is None:
            return records
        normalized = specialization.strip().lower()
        return [
            r for r in records
            if r.brain.specialization.strip().lower() == normalized
        ]

    def verify_trust(
        self,
        brain_id: str,
        *,
        evidence: str,
        mother_approved: bool = False,
        human_approved: bool = False,
        verification_passed: bool = False,
    ) -> SpecialistChildRecord:
        record = self._require(brain_id)
        self._require_not_retired(record)
        if not (mother_approved and human_approved):
            raise PermissionError("Trust verification requires Mother and human approval.")
        if not verification_passed:
            raise PermissionError("Independent trust verification must pass.")
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError("Explicit trust evidence is required.")
        if record.runtime_state != ChildRuntimeState.READY:
            raise ValueError("Trust verification requires a READY child.")
        if record.brain.trust_status == BrainTrustStatus.VERIFIED:
            raise ValueError("Trust is already verified; suspend/revoke before re-verification.")
        record.brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence=evidence.strip(),
        )
        return record

    def activate(
        self,
        brain_id: str,
        *,
        mother_approved: bool = False,
        human_approved: bool = False,
    ) -> SpecialistChildRecord:
        record = self._require(brain_id)
        self._require_not_retired(record)
        if not (mother_approved and human_approved):
            raise PermissionError("Child activation requires Mother and human approval.")
        if record.brain.trust_status != BrainTrustStatus.VERIFIED:
            raise PermissionError("Verified trust is required before activation.")
        if record.runtime_state != ChildRuntimeState.READY:
            raise ValueError("Child must be READY before activation.")
        decision = self._runtime.transition(
            record.runtime_state,
            ChildRuntimeState.ACTIVE,
            authority_approved=True,
            verification_passed=True,
        )
        if not decision.allowed:
            raise ValueError(decision.reason)
        record.brain.transition_to(BrainStatus.ACTIVE)
        record.runtime_state = ChildRuntimeState.ACTIVE
        return record

    def suspend(
        self,
        brain_id: str,
        *,
        mother_approved: bool = False,
        human_approved: bool = False,
        reason: str = "suspended by Mother or Human",
    ) -> SpecialistChildRecord:
        record = self._require(brain_id)
        self._require_not_retired(record)
        if not (mother_approved or human_approved):
            raise PermissionError("Child suspension requires Mother or human approval.")
        if record.runtime_state not in {
            ChildRuntimeState.READY,
            ChildRuntimeState.ACTIVE,
        }:
            raise ValueError("Child must be READY or ACTIVE to suspend.")
        decision = self._runtime.transition(
            record.runtime_state,
            ChildRuntimeState.PAUSED,
            authority_approved=True,
            verification_passed=False,
        )
        if not decision.allowed:
            raise ValueError(decision.reason)
        if record.brain.status == BrainStatus.ACTIVE:
            record.brain.transition_to(BrainStatus.PAUSED)
        # A READY brain is already non-executing. Keep its identity READY
        # while the manager runtime state is PAUSED so it can be safely resumed.
        record.brain.set_trust_status(
            BrainTrustStatus.SUSPENDED,
            evidence=reason,
        )
        record.runtime_state = ChildRuntimeState.PAUSED
        return record

    def resume(
        self,
        brain_id: str,
        *,
        mother_approved: bool = False,
        human_approved: bool = False,
        verification_passed: bool = False,
        verification_evidence: str | None = None,
    ) -> SpecialistChildRecord:
        record = self._require(brain_id)
        self._require_not_retired(record)
        if not (mother_approved and human_approved):
            raise PermissionError("Child resume requires Mother and human approval.")
        if not verification_passed:
            raise PermissionError("Fresh verification is required before resume.")
        if not isinstance(verification_evidence, str) or not verification_evidence.strip():
            raise ValueError("Explicit post-suspension verification evidence is required.")
        if record.runtime_state != ChildRuntimeState.PAUSED:
            raise ValueError("Only a paused child can be resumed.")
        decision = self._runtime.transition(
            record.runtime_state,
            ChildRuntimeState.READY,
            authority_approved=True,
            verification_passed=True,
        )
        if not decision.allowed:
            raise ValueError(decision.reason)
        record.brain.set_trust_status(
            BrainTrustStatus.UNVERIFIED,
            evidence="Previous trust invalidated by suspension; awaiting explicit verification.",
        )
        if record.brain.status in {BrainStatus.PAUSED, BrainStatus.FAILED}:
            record.brain.transition_to(BrainStatus.READY)
        elif record.brain.status != BrainStatus.READY:
            raise ValueError("Child identity is not in a resumable brain status.")
        record.runtime_state = ChildRuntimeState.READY
        self.verify_trust(
            brain_id,
            evidence=verification_evidence.strip(),
            mother_approved=mother_approved,
            human_approved=human_approved,
            verification_passed=True,
        )
        return record

    def retire(
        self,
        brain_id: str,
        *,
        human_approved: bool = False,
    ) -> SpecialistChildRecord:
        record = self._require(brain_id)
        if not human_approved:
            raise PermissionError("Child retirement requires human approval.")
        if record.runtime_state == ChildRuntimeState.RETIRED:
            return record
        if record.runtime_state == ChildRuntimeState.ACTIVE:
            raise ValueError("Suspend the active child before retirement.")
        decision = self._runtime.transition(
            record.runtime_state,
            ChildRuntimeState.RETIRED,
            authority_approved=True,
            verification_passed=True,
        )
        if not decision.allowed:
            raise ValueError(decision.reason)
        if record.brain.status != BrainStatus.DISABLED:
            if record.brain.status == BrainStatus.READY:
                record.brain.transition_to(BrainStatus.DISABLED)
            elif record.brain.status == BrainStatus.PAUSED:
                record.brain.transition_to(BrainStatus.DISABLED)
            elif record.brain.status == BrainStatus.FAILED:
                record.brain.transition_to(BrainStatus.DISABLED)
        record.runtime_state = ChildRuntimeState.RETIRED
        return record

    def replace(
        self,
        brain_id: str,
        *,
        name: str,
        description: str,
        specialization: str,
        capabilities: set[BrainCapability] | None = None,
        mother_approved: bool = False,
        human_approved: bool = False,
    ) -> SpecialistChildRecord:
        old = self._require(brain_id)
        if not mother_approved or not human_approved:
            raise PermissionError("Replacement requires Mother and human approval.")
        if old.runtime_state not in {
            ChildRuntimeState.READY,
            ChildRuntimeState.PAUSED,
        }:
            raise ValueError("Child must be READY or PAUSED before replacement.")
        # Create and verify the replacement before retiring the old child.
        # A malformed replacement must never destroy the working predecessor.
        replacement = self.create_child(
            name=name,
            description=description,
            specialization=specialization,
            capabilities=capabilities,
            mother_approved=True,
            human_approved=True,
            parent_brain_id=old.brain.parent_brain_id,
        )
        try:
            self.retire(brain_id, human_approved=True)
        except Exception:
            # Roll back the newly registered replacement if predecessor
            # retirement fails; the old child remains the active record.
            self._records.pop(replacement.brain.brain_id, None)
            self.registry.remove(replacement.brain.brain_id)
            raise
        replacement.predecessor_brain_id = old.brain.brain_id
        replacement.trust_lineage_id = old.trust_lineage_id
        return replacement

    def register_handler(self, brain_id: str, handler: SpecialistHandler) -> None:
        record = self._require(brain_id)
        if record.runtime_state == ChildRuntimeState.RETIRED:
            raise ValueError("Cannot register a handler for a retired child.")
        self.dispatcher.register_handler(record.brain.brain_id, handler)

    def dispatch(
        self,
        brain_id: str,
        request: str,
        *,
        metadata: dict[str, Any] | None = None,
        mother_approved: bool = False,
    ) -> SpecialistDispatchResult:
        record = self._require(brain_id)
        if record.runtime_state not in {
            ChildRuntimeState.READY,
            ChildRuntimeState.ACTIVE,
        }:
            return SpecialistDispatchResult(
                success=False,
                brain_id=brain_id,
                request=request,
                result=None,
                error="Child is not ready for specialist work.",
            )
        if not mother_approved and record.runtime_state == ChildRuntimeState.PAUSED:
            raise PermissionError("Paused child requires Mother approval.")
        if record.brain.status not in {
            BrainStatus.READY,
            BrainStatus.ACTIVE,
        }:
            return SpecialistDispatchResult(
                success=False,
                brain_id=brain_id,
                request=request,
                result=None,
                error="Child is not in READY/ACTIVE brain status.",
            )
        specialization_key = record.brain.specialization.strip().lower()
        required_capability = self.REQUIRED_CAPABILITY_BY_SPECIALIZATION.get(
            specialization_key,
            BrainCapability.THINK,
        )
        if not record.brain.has_capability(required_capability):
            return SpecialistDispatchResult(
                success=False,
                brain_id=brain_id,
                request=request,
                result=None,
                error=(
                    "Child lacks required capability for specialization: "
                    + required_capability.value
                ),
            )
        result = self.dispatcher.dispatch(
            request=request,
            specialization=record.brain.specialization,
            metadata=metadata,
        )
        record.performance.last_success = result.success
        if result.success:
            # Dispatch success means the handler ran, not that its answer
            # was independently verified. Verified counts are recorded only
            # through record_performance(..., verified=True).
            record.performance.completed += 1
        else:
            record.performance.failed += 1
            record.performance.last_error = result.error
        return result

    def record_performance(
        self,
        brain_id: str,
        *,
        success: bool,
        verified: bool = False,
        error: str | None = None,
    ) -> ChildPerformance:
        record = self._require(brain_id)
        if success:
            record.performance.completed += 1
        else:
            record.performance.failed += 1
        if verified:
            record.performance.verified += 1
        record.performance.last_success = success
        record.performance.last_error = error
        return record.performance

    def performance(self, brain_id: str) -> ChildPerformance:
        return self._require(brain_id).performance

    def can_child_grant_authority(self) -> bool:
        return False

    def can_child_modify_constitution(self) -> bool:
        return False

    def can_child_override_mother(self) -> bool:
        return False

    def can_external_model_create_child(self) -> bool:
        return False

    def can_tool_create_child(self) -> bool:
        return False

    def can_child_self_activate(self) -> bool:
        return False

    def protected_actions_stay_with_mother(self) -> bool:
        return True

    def _require(self, brain_id: str) -> SpecialistChildRecord:
        if not isinstance(brain_id, str) or not brain_id.strip():
            raise ValueError("brain_id is required.")
        record = self._records.get(brain_id.strip())
        if record is None:
            raise KeyError(f"Unknown Child Brain: {brain_id}")
        return record

    @staticmethod
    def _require_not_retired(record: SpecialistChildRecord) -> None:
        if record.runtime_state == ChildRuntimeState.RETIRED:
            raise ValueError("Retired Child Brain is terminal.")
