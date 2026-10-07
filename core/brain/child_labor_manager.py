from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LaborBrainState(str, Enum):
    REGISTERED = "registered"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"
    RETIRED = "retired"


@dataclass(frozen=True)
class LaborBrainRecord:
    labor_id: str
    child_brain_id: str
    specialization: str
    state: LaborBrainState


@dataclass(frozen=True)
class LaborManagerResult:
    allowed: bool
    reason: str
    record: LaborBrainRecord | None = None


class ChildLaborManager:
    VERSION = "1.0"

    VALID_TRANSITIONS = {
        LaborBrainState.REGISTERED: {
            LaborBrainState.READY,
            LaborBrainState.FAILED,
        },
        LaborBrainState.READY: {
            LaborBrainState.ACTIVE,
            LaborBrainState.PAUSED,
            LaborBrainState.FAILED,
            LaborBrainState.RETIRED,
        },
        LaborBrainState.ACTIVE: {
            LaborBrainState.PAUSED,
            LaborBrainState.FAILED,
            LaborBrainState.RETIRED,
        },
        LaborBrainState.PAUSED: {
            LaborBrainState.READY,
            LaborBrainState.ACTIVE,
            LaborBrainState.FAILED,
            LaborBrainState.RETIRED,
        },
        LaborBrainState.FAILED: {
            LaborBrainState.READY,
            LaborBrainState.RETIRED,
        },
        LaborBrainState.RETIRED: set(),
    }

    def __init__(self) -> None:
        self._brains: dict[str, LaborBrainRecord] = {}

    def register(
        self,
        labor_id: str,
        child_brain_id: str,
        specialization: str,
    ) -> LaborManagerResult:
        if not labor_id or not child_brain_id or not specialization:
            return LaborManagerResult(
                False,
                "labor identity, parent identity and specialization are required",
            )

        if labor_id in self._brains:
            return LaborManagerResult(
                False,
                "labor brain already registered",
            )

        record = LaborBrainRecord(
            labor_id=labor_id,
            child_brain_id=child_brain_id,
            specialization=specialization,
            state=LaborBrainState.REGISTERED,
        )

        self._brains[labor_id] = record

        return LaborManagerResult(
            True,
            "labor brain registered",
            record,
        )

    def get(self, labor_id: str) -> LaborBrainRecord | None:
        return self._brains.get(labor_id)

    def transition(
        self,
        labor_id: str,
        target: LaborBrainState,
        authority_approved: bool = False,
    ) -> LaborManagerResult:
        record = self._brains.get(labor_id)

        if record is None:
            return LaborManagerResult(
                False,
                "labor brain not registered",
            )

        if record.state == LaborBrainState.RETIRED:
            return LaborManagerResult(
                False,
                "retired labor brain cannot transition",
                record,
            )

        allowed_targets = self.VALID_TRANSITIONS.get(
            record.state,
            set(),
        )

        if target not in allowed_targets:
            return LaborManagerResult(
                False,
                "invalid labor state transition",
                record,
            )

        if not authority_approved:
            return LaborManagerResult(
                False,
                "authority approval required for labor state change",
                record,
            )

        updated = LaborBrainRecord(
            labor_id=record.labor_id,
            child_brain_id=record.child_brain_id,
            specialization=record.specialization,
            state=target,
        )

        self._brains[labor_id] = updated

        return LaborManagerResult(
            True,
            "labor state transition approved",
            updated,
        )

    def list_child_labor(
        self,
        child_brain_id: str,
    ) -> list[LaborBrainRecord]:
        return [
            record
            for record in self._brains.values()
            if record.child_brain_id == child_brain_id
        ]

    def can_assign_task(
        self,
        labor_id: str,
        authority_approved: bool = False,
    ) -> bool:
        record = self._brains.get(labor_id)

        if record is None:
            return False

        if record.state != LaborBrainState.ACTIVE:
            return False

        return authority_approved

    def can_self_create_labor(self) -> bool:
        return False

    def can_grant_authority(self) -> bool:
        return False

    def can_self_promote(self) -> bool:
        return False

    def can_override_child(self) -> bool:
        return False

    def can_override_mother(self) -> bool:
        return False

    def can_execute_tools(self) -> bool:
        return False

    def can_modify_constitution(self) -> bool:
        return False
