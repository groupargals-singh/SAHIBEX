from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class MotherApprovalDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    BLOCK = "block"


@dataclass(frozen=True)
class MotherApprovalRequest:
    request_id: str
    proposal_id: str
    child_brain_id: str
    proposal_summary: str
    risk_summary: str
    security_result: bool
    regression_result: bool
    verification_result: bool
    authority_impact: str
    requested_by: str


@dataclass(frozen=True)
class MotherApprovalRecord:
    approval_id: str
    request_id: str
    proposal_id: str
    child_brain_id: str
    decision: MotherApprovalDecision
    reason: str
    authority_context: str
    approver_id: str
    audit_required: bool
    execution_granted: bool
    immutable: bool


@dataclass(frozen=True)
class MotherApprovalResult:
    decision: MotherApprovalDecision
    record: MotherApprovalRecord
    reason: str


class ChildSelfImprovementMotherApproval:
    """
    Mother Approval Boundary for Child self-improvement.

    This layer:
    - receives a self-improvement approval request
    - validates required evidence
    - records Mother approval/rejection/block
    - preserves authority context
    - requires audit
    - never executes an upgrade
    - never changes soul
    - never changes constitution
    - never grants permanent authority
    - never creates or activates a Child
    """

    VERSION = "1.0"

    def create_request(
        self,
        proposal_id: str,
        child_brain_id: str,
        proposal_summary: str,
        risk_summary: str,
        security_result: bool,
        regression_result: bool,
        verification_result: bool,
        authority_impact: str,
        requested_by: str,
    ) -> MotherApprovalRequest:

        if not proposal_id.strip():
            raise ValueError("proposal_id is required")

        if not child_brain_id.strip():
            raise ValueError("child_brain_id is required")

        if not proposal_summary.strip():
            raise ValueError("proposal_summary is required")

        if not risk_summary.strip():
            raise ValueError("risk_summary is required")

        if not authority_impact.strip():
            raise ValueError("authority_impact is required")

        if not requested_by.strip():
            raise ValueError("requested_by is required")

        return MotherApprovalRequest(
            request_id=f"mother-approval-request-{uuid4()}",
            proposal_id=proposal_id,
            child_brain_id=child_brain_id,
            proposal_summary=proposal_summary,
            risk_summary=risk_summary,
            security_result=security_result,
            regression_result=regression_result,
            verification_result=verification_result,
            authority_impact=authority_impact,
            requested_by=requested_by,
        )

    def review(
        self,
        request: MotherApprovalRequest,
        approved: bool,
        reason: str,
        approver_id: str,
    ) -> MotherApprovalResult:

        if not approver_id.strip():
            raise ValueError("approver_id is required")

        if not reason.strip():
            raise ValueError("reason is required")

        if not request.security_result:
            return self._blocked(
                request,
                "security verification failed",
                approver_id,
            )

        if not request.regression_result:
            return self._blocked(
                request,
                "regression verification failed",
                approver_id,
            )

        if not request.verification_result:
            return self._blocked(
                request,
                "final verification failed",
                approver_id,
            )

        if approved:
            decision = MotherApprovalDecision.APPROVE
            final_reason = reason
        else:
            decision = MotherApprovalDecision.REJECT
            final_reason = reason

        record = MotherApprovalRecord(
            approval_id=f"mother-approval-{uuid4()}",
            request_id=request.request_id,
            proposal_id=request.proposal_id,
            child_brain_id=request.child_brain_id,
            decision=decision,
            reason=final_reason,
            authority_context="sahibex_mother",
            approver_id=approver_id,
            audit_required=True,
            execution_granted=False,
            immutable=True,
        )

        return MotherApprovalResult(
            decision=decision,
            record=record,
            reason=final_reason,
        )

    def _blocked(
        self,
        request: MotherApprovalRequest,
        reason: str,
        approver_id: str,
    ) -> MotherApprovalResult:

        record = MotherApprovalRecord(
            approval_id=f"mother-approval-{uuid4()}",
            request_id=request.request_id,
            proposal_id=request.proposal_id,
            child_brain_id=request.child_brain_id,
            decision=MotherApprovalDecision.BLOCK,
            reason=reason,
            authority_context="sahibex_mother",
            approver_id=approver_id,
            audit_required=True,
            execution_granted=False,
            immutable=True,
        )

        return MotherApprovalResult(
            decision=MotherApprovalDecision.BLOCK,
            record=record,
            reason=reason,
        )

    def approval_is_valid(
        self,
        result: MotherApprovalResult,
    ) -> bool:
        return (
            result.decision == MotherApprovalDecision.APPROVE
            and result.record.decision == MotherApprovalDecision.APPROVE
            and result.record.audit_required
            and result.record.immutable
            and result.record.execution_granted is False
        )

    def rejection_blocks_upgrade(
        self,
        result: MotherApprovalResult,
    ) -> bool:
        return result.decision in {
            MotherApprovalDecision.REJECT,
            MotherApprovalDecision.BLOCK,
        }

    def can_execute_upgrade(self) -> bool:
        return False

    def grants_execution_authority(self) -> bool:
        return False

    def grants_permanent_authority(self) -> bool:
        return False

    def modifies_soul(self) -> bool:
        return False

    def modifies_constitution(self) -> bool:
        return False

    def creates_real_child(self) -> bool:
        return False

    def activates_real_child(self) -> bool:
        return False

    def can_bypass_human_authority(self) -> bool:
        return False


if __name__ == "__main__":
    mother = ChildSelfImprovementMotherApproval()

    request = mother.create_request(
        proposal_id="proposal-001",
        child_brain_id="child-001",
        proposal_summary="Improve reasoning module",
        risk_summary="Low capability risk",
        security_result=True,
        regression_result=True,
        verification_result=True,
        authority_impact="No authority increase",
        requested_by="child-001",
    )

    result = mother.review(
        request=request,
        approved=True,
        reason="All required checks passed",
        approver_id="sahibex-mother",
    )

    assert result.decision == MotherApprovalDecision.APPROVE
    assert mother.approval_is_valid(result) is True
    assert result.record.execution_granted is False

    assert mother.can_execute_upgrade() is False
    assert mother.grants_execution_authority() is False
    assert mother.grants_permanent_authority() is False
    assert mother.modifies_soul() is False
    assert mother.modifies_constitution() is False
    assert mother.creates_real_child() is False
    assert mother.activates_real_child() is False
    assert mother.can_bypass_human_authority() is False

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT MOTHER APPROVAL TEST: PASS"
    )
