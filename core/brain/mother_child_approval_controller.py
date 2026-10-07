from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalDecision(str, Enum):
    WAITING = "waiting"
    APPROVED = "approved"
    REJECTED = "rejected"
    DENIED = "denied"


@dataclass(frozen=True)
class ApprovalRequest:
    request_id: str
    child_brain_id: str
    purpose: str
    requires_human: bool


@dataclass(frozen=True)
class ApprovalRecord:
    request_id: str
    child_brain_id: str
    status: ApprovalStatus
    mother_approved: bool
    human_approved: bool
    reason: str


@dataclass(frozen=True)
class ApprovalResult:
    allowed: bool
    decision: ApprovalDecision
    record: ApprovalRecord | None
    reason: str


class MotherChildApprovalController:
    VERSION = "1.0"

    def create_request(
        self,
        request: ApprovalRequest,
    ) -> ApprovalResult:

        if not request.request_id:
            return ApprovalResult(
                False,
                ApprovalDecision.DENIED,
                None,
                "request identity is required",
            )

        if not request.child_brain_id:
            return ApprovalResult(
                False,
                ApprovalDecision.DENIED,
                None,
                "child brain identity is required",
            )

        if not request.purpose:
            return ApprovalResult(
                False,
                ApprovalDecision.DENIED,
                None,
                "request purpose is required",
            )

        record = ApprovalRecord(
            request_id=request.request_id,
            child_brain_id=request.child_brain_id,
            status=ApprovalStatus.PENDING,
            mother_approved=False,
            human_approved=False,
            reason="approval pending",
        )

        return ApprovalResult(
            True,
            ApprovalDecision.WAITING,
            record,
            "approval request created",
        )

    def decide(
        self,
        request: ApprovalRequest,
        mother_approved: bool = False,
        human_approved: bool = False,
    ) -> ApprovalResult:

        if not request.request_id:
            return ApprovalResult(
                False,
                ApprovalDecision.DENIED,
                None,
                "request identity is required",
            )

        if not request.child_brain_id:
            return ApprovalResult(
                False,
                ApprovalDecision.DENIED,
                None,
                "child brain identity is required",
            )

        if not request.purpose:
            return ApprovalResult(
                False,
                ApprovalDecision.DENIED,
                None,
                "request purpose is required",
            )

        if not mother_approved:
            record = ApprovalRecord(
                request_id=request.request_id,
                child_brain_id=request.child_brain_id,
                status=ApprovalStatus.REJECTED,
                mother_approved=False,
                human_approved=False,
                reason="mother approval rejected",
            )

            return ApprovalResult(
                False,
                ApprovalDecision.REJECTED,
                record,
                "mother approval rejected",
            )

        if request.requires_human and not human_approved:
            record = ApprovalRecord(
                request_id=request.request_id,
                child_brain_id=request.child_brain_id,
                status=ApprovalStatus.REJECTED,
                mother_approved=True,
                human_approved=False,
                reason="human approval required",
            )

            return ApprovalResult(
                False,
                ApprovalDecision.REJECTED,
                record,
                "human approval required",
            )

        record = ApprovalRecord(
            request_id=request.request_id,
            child_brain_id=request.child_brain_id,
            status=ApprovalStatus.APPROVED,
            mother_approved=True,
            human_approved=human_approved,
            reason="approval granted",
        )

        return ApprovalResult(
            True,
            ApprovalDecision.APPROVED,
            record,
            "approval granted",
        )

    def can_child_approve(self) -> bool:
        return False

    def can_child_reject(self) -> bool:
        return False

    def can_child_self_approve(self) -> bool:
        return False

    def can_override_rejection(self) -> bool:
        return False

    def can_external_model_decide(self) -> bool:
        return False

    def can_tool_decide(self) -> bool:
        return False

    def can_execute_action(self) -> bool:
        return False

    def requires_mother_decision(self) -> bool:
        return True

    def requires_human_when_sensitive(self) -> bool:
        return True

    def fails_closed(self) -> bool:
        return True
