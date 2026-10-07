from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ArmyBrainState(str, Enum):
    REGISTERED = "registered"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"
    RETIRED = "retired"


@dataclass(frozen=True)
class ArmyBrainRecord:
    army_id: str
    child_brain_id: str
    specialization: str
    state: ArmyBrainState


@dataclass(frozen=True)
class ArmyManagerResult:
    allowed: bool
    reason: str
    record: ArmyBrainRecord | None = None


class ChildArmyManager:
    VERSION = "1.0"

    VALID_TRANSITIONS = {
        ArmyBrainState.REGISTERED: {
            ArmyBrainState.READY,
            ArmyBrainState.FAILED,
        },
        ArmyBrainState.READY: {
            ArmyBrainState.ACTIVE,
            ArmyBrainState.PAUSED,
            ArmyBrainState.FAILED,
            ArmyBrainState.RETIRED,
        },
        ArmyBrainState.ACTIVE: {
            ArmyBrainState.PAUSED,
            ArmyBrainState.FAILED,
            ArmyBrainState.RETIRED,
        },
        ArmyBrainState.PAUSED: {
            ArmyBrainState.READY,
            ArmyBrainState.ACTIVE,
            ArmyBrainState.FAILED,
            ArmyBrainState.RETIRED,
        },
        ArmyBrainState.FAILED: {
            ArmyBrainState.READY,
            ArmyBrainState.RETIRED,
        },
        ArmyBrainState.RETIRED: set(),
    }

    def __init__(self) -> None:
        self._brains: dict[str, ArmyBrainRecord] = {}

    def register(
        self,
        army_id: str,
        child_brain_id: str,
        specialization: str,
    ) -> ArmyManagerResult:
        if not army_id or not child_brain_id or not specialization:
            return ArmyManagerResult(
                False,
                "army identity, parent identity and specialization are required",
            )

        if army_id in self._brains:
            return ArmyManagerResult(
                False,
                "army brain already registered",
            )

        record = ArmyBrainRecord(
            army_id=army_id,
            child_brain_id=child_brain_id,
            specialization=specialization,
            state=ArmyBrainState.REGISTERED,
        )

        self._brains[army_id] = record

        return ArmyManagerResult(
            True,
            "army brain registered",
            record,
        )

    def get(self, army_id: str) -> ArmyBrainRecord | None:
        return self._brains.get(army_id)

    def transition(
        self,
        army_id: str,
        target: ArmyBrainState,
        authority_approved: bool = False,
    ) -> ArmyManagerResult:
        record = self._brains.get(army_id)

        if record is None:
            return ArmyManagerResult(
                False,
                "army brain not registered",
            )

        if record.state == ArmyBrainState.RETIRED:
            return ArmyManagerResult(
                False,
                "retired army brain cannot transition",
                record,
            )

        allowed_targets = self.VALID_TRANSITIONS.get(
            record.state,
            set(),
        )

        if target not in allowed_targets:
            return ArmyManagerResult(
                False,
                "invalid army state transition",
                record,
            )

        if not authority_approved:
            return ArmyManagerResult(
                False,
                "authority approval required for army state change",
                record,
            )

        updated = ArmyBrainRecord(
            army_id=record.army_id,
            child_brain_id=record.child_brain_id,
            specialization=record.specialization,
            state=target,
        )

        self._brains[army_id] = updated

        return ArmyManagerResult(
            True,
            "army state transition approved",
            updated,
        )

    def list_child_army(self, child_brain_id: str) -> list[ArmyBrainRecord]:
        return [
            record
            for record in self._brains.values()
            if record.child_brain_id == child_brain_id
        ]

    def can_assign_task(
        self,
        army_id: str,
        authority_approved: bool = False,
    ) -> bool:
        record = self._brains.get(army_id)

        if record is None:
            return False

        if record.state != ArmyBrainState.ACTIVE:
            return False

        return authority_approved

    def can_self_create_army(self) -> bool:
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
