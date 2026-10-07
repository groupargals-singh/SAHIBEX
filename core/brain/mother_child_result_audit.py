from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ResultStatus(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class ResultDecision(str, Enum):
    RECORDED = "recorded"
    DENIED = "denied"


@dataclass(frozen=True)
class MotherChildResult:
    request_id: str
    child_brain_id: str
    status: ResultStatus
    action: str
    reason: str


@dataclass(frozen=True)
class AuditProvenance:
    event_id: str
    actor_id: str
    source: str
    authority_context: str
    verification_context: str
    timestamp_context: str


@dataclass(frozen=True)
class ResultAuditRecord:
    result: MotherChildResult
    provenance: AuditProvenance


@dataclass(frozen=True)
class ResultAuditOutcome:
    allowed: bool
    decision: ResultDecision
    record: ResultAuditRecord | None
    reason: str


class MotherChildResultAudit:
    VERSION = "1.0"

    def record(
        self,
        result: MotherChildResult,
        provenance: AuditProvenance,
    ) -> ResultAuditOutcome:

        result_values = {
            "request_id": result.request_id,
            "child_brain_id": result.child_brain_id,
            "action": result.action,
            "reason": result.reason,
        }

        for field_name, value in result_values.items():
            if not value:
                return ResultAuditOutcome(
                    False,
                    ResultDecision.DENIED,
                    None,
                    f"{field_name} is required",
                )

        provenance_values = {
            "event_id": provenance.event_id,
            "actor_id": provenance.actor_id,
            "source": provenance.source,
            "authority_context": provenance.authority_context,
            "verification_context": provenance.verification_context,
            "timestamp_context": provenance.timestamp_context,
        }

        for field_name, value in provenance_values.items():
            if not value:
                return ResultAuditOutcome(
                    False,
                    ResultDecision.DENIED,
                    None,
                    f"{field_name} provenance is required",
                )

        record = ResultAuditRecord(
            result=result,
            provenance=provenance,
        )

        return ResultAuditOutcome(
            True,
            ResultDecision.RECORDED,
            record,
            "result and provenance recorded",
        )

    def can_audit_grant_authority(self) -> bool:
        return False

    def can_child_modify_record(self) -> bool:
        return False

    def can_external_model_modify_record(self) -> bool:
        return False

    def can_tool_modify_record(self) -> bool:
        return False

    def can_hide_event(self) -> bool:
        return False

    def can_fabricate_event(self) -> bool:
        return False

    def can_execute_action(self) -> bool:
        return False

    def requires_provenance(self) -> bool:
        return True

    def requires_verification_context(self) -> bool:
        return True

    def fails_closed(self) -> bool:
        return True
