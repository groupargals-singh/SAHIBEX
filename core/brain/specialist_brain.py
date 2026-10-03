from __future__ import annotations
from security.audit.brain_trust_lifecycle import (
    BrainTrustEvidenceLifecycle,
)
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from pathlib import Path
from core.brain.resource import BrainResourceState
from core.brain.verification import BrainTrustStatus
from security.audit.brain_trust_provenance import (
    BrainTrustProvenance,
)
from security.audit.brain_trust_replacement_store import (
    BrainTrustReplacementStore,
)
from core.policies.constitution import BrainRole


class BrainCapability(str, Enum):
    THINK = "think"
    RESEARCH = "research"
    ANALYZE = "analyze"
    CODE = "code"
    CREATE = "create"
    VERIFY = "verify"
    PLAN = "plan"
    READ = "read"


class BrainStatus(str, Enum):
    REGISTERED = "registered"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    FAILED = "failed"


@dataclass
class SpecialistBrain:
    """
    Model-independent identity, hierarchy, capability, lifecycle,
    memory-isolation, trust, and resource/load contract
    for a SAHIBEX specialist brain.

    Brain hierarchy:
        SAHIBEX Mother Brain
            -> Internal Army Brain
            -> Child Brain
                -> Child Brain Internal Army

    Capability does not grant authority.
    Authority is enforced by the Constitutional Core.
    """

    name: str
    description: str
    specialization: str
    capabilities: set[BrainCapability]

    brain_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    status: BrainStatus = BrainStatus.REGISTERED

    trust_status: BrainTrustStatus = BrainTrustStatus.UNVERIFIED
    trust_evidence: str | None = None

    resource_state: BrainResourceState = field(
        default_factory=BrainResourceState
    )

    # Hierarchy identity.
    #
    # Existing specialist brains remain INTERNAL_ARMY by default
    # so existing contracts remain backward compatible.
    brain_role: BrainRole = BrainRole.INTERNAL_ARMY

    # Parent identity.
    #
    # None is allowed for legacy/root registration compatibility.
    # Hierarchy-aware registration can enforce the required parent.
    parent_brain_id: str | None = None

    _ALLOWED_TRANSITIONS = {
        BrainStatus.REGISTERED: {
            BrainStatus.READY,
        },
        BrainStatus.READY: {
            BrainStatus.ACTIVE,
            BrainStatus.DISABLED,
            BrainStatus.FAILED,
        },
        BrainStatus.ACTIVE: {
            BrainStatus.READY,
            BrainStatus.PAUSED,
            BrainStatus.DISABLED,
            BrainStatus.FAILED,
        },
        BrainStatus.PAUSED: {
            BrainStatus.READY,
            BrainStatus.DISABLED,
            BrainStatus.FAILED,
        },
        BrainStatus.FAILED: {
            BrainStatus.READY,
            BrainStatus.DISABLED,
        },
        BrainStatus.DISABLED: set(),
    }

    @property
    def memory_namespace(self) -> str:
        return f"brain:{self.brain_id}"

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a non-empty string.")

        if (
            not isinstance(self.description, str)
            or not self.description.strip()
        ):
            raise ValueError(
                "description must be a non-empty string."
            )

        if (
            not isinstance(self.specialization, str)
            or not self.specialization.strip()
        ):
            raise ValueError(
                "specialization must be a non-empty string."
            )

        if not isinstance(self.brain_id, str) or not self.brain_id.strip():
            raise ValueError(
                "brain_id must be a non-empty string."
            )

        if not isinstance(self.capabilities, set):
            raise TypeError(
                "capabilities must be a set of BrainCapability."
            )

        if not all(
            isinstance(capability, BrainCapability)
            for capability in self.capabilities
        ):
            raise TypeError(
                "capabilities must contain only BrainCapability values."
            )

        if not isinstance(self.status, BrainStatus):
            raise TypeError(
                "status must be a BrainStatus."
            )

        if not isinstance(
            self.trust_status,
            BrainTrustStatus,
        ):
            raise TypeError(
                "trust_status must be a BrainTrustStatus."
            )

        if self.trust_evidence is not None:
            if (
                not isinstance(self.trust_evidence, str)
                or not self.trust_evidence.strip()
            ):
                raise ValueError(
                    "trust_evidence must be a non-empty string "
                    "when provided."
                )

        if not isinstance(
            self.resource_state,
            BrainResourceState,
        ):
            raise TypeError(
                "resource_state must be a BrainResourceState."
            )

        if not isinstance(self.brain_role, BrainRole):
            raise TypeError(
                "brain_role must be a BrainRole."
            )

        if self.parent_brain_id is not None:
            if (
                not isinstance(self.parent_brain_id, str)
                or not self.parent_brain_id.strip()
            ):
                raise ValueError(
                    "parent_brain_id must be a non-empty string "
                    "when provided."
                )

            self.parent_brain_id = self.parent_brain_id.strip()

        # Mother Brain is the root of the hierarchy.
        if (
            self.brain_role == BrainRole.MOTHER_BRAIN
            and self.parent_brain_id is not None
        ):
            raise ValueError(
                "Mother Brain cannot have a parent_brain_id."
            )

    @property
    def is_mother_brain(self) -> bool:
        return self.brain_role == BrainRole.MOTHER_BRAIN

    @property
    def is_internal_army(self) -> bool:
        return self.brain_role == BrainRole.INTERNAL_ARMY

    @property
    def is_child_brain(self) -> bool:
        return self.brain_role == BrainRole.CHILD_BRAIN

    @property
    def has_parent(self) -> bool:
        return self.parent_brain_id is not None

    def has_capability(
        self,
        capability: BrainCapability,
    ) -> bool:
        if not isinstance(capability, BrainCapability):
            raise TypeError(
                "capability must be a BrainCapability."
            )

        return capability in self.capabilities

    def list_capabilities(self) -> set[BrainCapability]:
        return set(self.capabilities)

    def transition_to(
        self,
        target_status: BrainStatus,
    ) -> BrainStatus:
        if not isinstance(target_status, BrainStatus):
            raise TypeError(
                "target_status must be a BrainStatus."
            )

        allowed_targets = self._ALLOWED_TRANSITIONS.get(
            self.status,
            set(),
        )

        if target_status not in allowed_targets:
            raise ValueError(
                f"Invalid brain lifecycle transition: "
                f"{self.status.value} -> {target_status.value}"
            )

        self.status = target_status

        return self.status

    def set_trust_status(
        self,
        target_status: BrainTrustStatus,
        *,
        evidence: str | None = None,
    ) -> BrainTrustStatus:
        if not isinstance(
            target_status,
            BrainTrustStatus,
        ):
            raise TypeError(
                "target_status must be a BrainTrustStatus."
            )

        if target_status == BrainTrustStatus.UNVERIFIED:
            self.trust_status = target_status
            self.trust_evidence = None
            return self.trust_status

        if (
            not isinstance(evidence, str)
            or not evidence.strip()
        ):
            raise ValueError(
                "Explicit evidence is required for this trust status."
            )

        self.trust_status = target_status
        self.trust_evidence = evidence.strip()

        return self.trust_status

    def create_authenticated_trust_record(
        self,
        *,
        storage_directory: Path,
    ) -> dict[str, str]:
        """
        Create authenticated trust evidence bound to this brain identity.

        This method records the current trust state and evidence.
        It does NOT grant permission, authority, or execution rights.
        """

        if self.trust_status == BrainTrustStatus.UNVERIFIED:
            raise ValueError(
                "UNVERIFIED brain cannot create authenticated trust evidence."
            )

        if (
            not isinstance(self.trust_evidence, str)
            or not self.trust_evidence.strip()
        ):
            raise ValueError(
                "Authenticated trust evidence requires trust_evidence."
            )

        provenance = BrainTrustProvenance(
            Path(storage_directory)
        )
        lifecycle = BrainTrustEvidenceLifecycle.ACTIVE

        proof = provenance.sign(
            brain_id=self.brain_id,
            trust_status=self.trust_status.value,
            evidence=self.trust_evidence.strip(),
            lifecycle=lifecycle.value,
        )

        return {
            "brain_id": self.brain_id,
            "trust_status": self.trust_status.value,
            "evidence": self.trust_evidence.strip(),
            "lifecycle": lifecycle.value,
            "provenance": proof,
        }

    def verify_authenticated_trust_record(
        self,
        record: dict[str, str],
        *,
        storage_directory: Path,
    ) -> bool:
        """
        Verify that a trust record belongs to this exact brain.

        Trust provenance does NOT grant permission or authority.
        """

        if not isinstance(record, dict):
            raise TypeError(
                "record must be a dictionary."
            )

        record_brain_id = str(
            record.get("brain_id", "")
        ).strip()

        if record_brain_id != self.brain_id:
            return False

        provenance = BrainTrustProvenance(
            Path(storage_directory)
        )

        result = provenance.verify(record)

        return result.verified

    def invalidate_authenticated_trust_record(
        self,
        record: dict[str, str],
        *,
        storage_directory: Path,
        reason: str,
    ) -> dict[str, str]:
        """
        Create an authenticated invalidated version of a trust record.

        Invalidation affects evidence lifecycle only.
        It does NOT change brain trust status, capabilities,
        permissions, authority, execution rights, or constitution.
        """

        if not isinstance(record, dict):
            raise TypeError(
                "record must be a dictionary."
            )

        if (
            not isinstance(reason, str)
            or not reason.strip()
        ):
            raise ValueError(
                "A reason is required to invalidate trust evidence."
            )

        record_brain_id = str(
            record.get("brain_id", "")
        ).strip()

        if record_brain_id != self.brain_id:
            raise ValueError(
                "Trust record belongs to a different brain."
            )

        provenance = BrainTrustProvenance(
            Path(storage_directory)
        )

        result = provenance.verify(record)

        if not result.verified:
            raise ValueError(
                "Cannot invalidate unauthenticated trust evidence."
            )

        lifecycle = (
            BrainTrustEvidenceLifecycle.INVALIDATED
        )

        invalidated_record = {
            "brain_id": record["brain_id"],
            "trust_status": record["trust_status"],
            "evidence": record["evidence"],
            "lifecycle": lifecycle.value,
            "reason": reason.strip(),
        }

        proof = provenance.sign(
            brain_id=invalidated_record["brain_id"],
            trust_status=invalidated_record["trust_status"],
            evidence=invalidated_record["evidence"],
            lifecycle=invalidated_record["lifecycle"],
        )

        invalidated_record["provenance"] = proof

        return invalidated_record
    def replace_authenticated_trust_record(
        self,
        record: dict[str, str],
        *,
        storage_directory: Path,
        new_evidence: str,
        reason: str,
        new_trust_status: BrainTrustStatus | None = None,
    ) -> dict[str, str]:
        """
        Create a new authenticated trust-evidence record
        while preserving the previous evidence history.

        The previous record is verified before replacement.

        Replacement:
        - does not overwrite the previous record
        - does not silently discard evidence history
        - creates a new authenticated evidence record
        - authenticates the relationship between old and new evidence
        - does not grant permission
        - does not grant authority
        - does not execute actions
        - does not modify the constitution
        """

        if not isinstance(record, dict):
            raise TypeError(
                "record must be a dictionary."
            )

        if (
            not isinstance(new_evidence, str)
            or not new_evidence.strip()
        ):
            raise ValueError(
                "New trust evidence is required."
            )

        if (
            not isinstance(reason, str)
            or not reason.strip()
        ):
            raise ValueError(
                "A replacement reason is required."
            )

        record_brain_id = str(
            record.get("brain_id", "")
        ).strip()

        if record_brain_id != self.brain_id:
            raise ValueError(
                "Trust record belongs to a different brain."
            )

        provenance = BrainTrustProvenance(
            Path(storage_directory)
        )

        previous_result = provenance.verify(record)

        if not previous_result.verified:
            raise ValueError(
                "Cannot replace unauthenticated trust evidence."
            )

        previous_provenance = str(
            record.get("provenance", "")
        ).strip()

        if not previous_provenance:
            raise ValueError(
                "Previous trust provenance is required."
            )

        target_status = (
            new_trust_status
            if new_trust_status is not None
            else self.trust_status
        )

        if not isinstance(
            target_status,
            BrainTrustStatus,
        ):
            raise TypeError(
                "new_trust_status must be a BrainTrustStatus."
            )

        lifecycle = BrainTrustEvidenceLifecycle.ACTIVE

        replacement_provenance = provenance.sign(
            brain_id=self.brain_id,
            trust_status=target_status.value,
            evidence=new_evidence.strip(),
            lifecycle=lifecycle.value,
        )

        if replacement_provenance == previous_provenance:
            raise ValueError(
                "Replacement provenance must differ "
                "from previous provenance."
            )

        replacement_authentication = (
            provenance.sign_replacement(
                brain_id=self.brain_id,
                previous_provenance=previous_provenance,
                replacement_provenance=replacement_provenance,
                reason=reason.strip(),
            )
        )

        new_record = {
            "brain_id": self.brain_id,
            "trust_status": target_status.value,
            "evidence": new_evidence.strip(),
            "lifecycle": lifecycle.value,
            "provenance": replacement_provenance,
        }

        replacement_record = {
            "brain_id": self.brain_id,
            "previous_provenance": previous_provenance,
            "replacement_provenance": replacement_provenance,
            "reason": reason.strip(),
            "provenance": replacement_authentication,
        }

        replacement_store = BrainTrustReplacementStore(
            Path(storage_directory)
        )

        replacement_store.append(
            replacement_record
        )

        return new_record


    def update_load(
        self,
        *,
        active_tasks: int,
    ) -> BrainResourceState:
        if not isinstance(active_tasks, int):
            raise TypeError(
                "active_tasks must be an integer."
            )

        if active_tasks < 0:
            raise ValueError(
                "active_tasks cannot be negative."
            )

        if (
            active_tasks
            > self.resource_state.max_concurrent_tasks
        ):
            raise ValueError(
                "active_tasks cannot exceed max_concurrent_tasks."
            )

        self.resource_state.active_tasks = active_tasks

        return self.resource_state

    def can_accept_work(self) -> bool:
        return (
            self.resource_state.active_tasks
            < self.resource_state.max_concurrent_tasks
        )
