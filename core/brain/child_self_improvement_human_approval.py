from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class HumanApprovalDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    BLOCK = "block"


@dataclass(frozen=True)
class HumanApprovalRequest:
    request_id: str
    proposal_id: str
    child_brain_id: str
    mother_approval_id: str
    change_summary: str
    risk_summary: str
    security_impact: str
    authority_impact: str
    security_verified: bool
    regression_verified: bool
    final_verification_passed: bool
    mother_approved: bool


@dataclass(frozen=True)
class HumanApprovalRecord:
    approval_id: str
    request_id: str
    proposal_id: str
    child_brain_id: str
    decision: HumanApprovalDecision
    reason: str
    authority_context: str
    approver_id: str
    audit_required: bool
    execution_granted: bool
    immutable: bool


@dataclass(frozen=True)
class HumanApprovalResult:
    decision: HumanApprovalDecision
    record: HumanApprovalRecord
    reason: str


class ChildSelfImprovementHumanApproval:
    """
    Human Approval Boundary for sensitive Child self-improvement.

    This layer:
    - validates Mother approval
    - validates security/regression/final verification
    - records explicit Human approval/rejection/block
    - preserves Human authority
    - requires audit
    - never executes an upgrade
    - never modifies soul
    - never modifies constitution
    - never creates or activates a Child
    """

    VERSION = "1.0"

    def create_request(
        self,
        proposal_id: str,
        child_brain_id: str,
        mother_approval_id: str,
        change_summary: str,
        risk_summary: str,
        security_impact: str,
        authority_impact: str,
        security_verified: bool,
        regression_verified: bool,
        final_verification_passed: bool,
        mother_approved: bool,
    ) -> HumanApprovalRequest:

        if not proposal_id.strip():
            raise ValueError("proposal_id is required")

        if not child_brain_id.strip():
            raise ValueError("child_brain_id is required")

        if not mother_approval_id.strip():
            raise ValueError("mother_approval_id is required")

        if not change_summary.strip():
            raise ValueError("change_summary is required")

        if not risk_summary.strip():
            raise ValueError("risk_summary is required")

        if not security_impact.strip():
            raise ValueError("security_impact is required")

        if not authority_impact.strip():
            raise ValueError("authority_impact is required")

        return HumanApprovalRequest(
            request_id=f"human-approval-request-{uuid4()}",
            proposal_id=proposal_id,
            child_brain_id=child_brain_id,
            mother_approval_id=mother_approval_id,
            change_summary=change_summary,
            risk_summary=risk_summary,
            security_impact=security_impact,
            authority_impact=authority_impact,
            security_verified=security_verified,
            regression_verified=regression_verified,
            final_verification_passed=final_verification_passed,
            mother_approved=mother_approved,
        )

    def review(
        self,
        request: HumanApprovalRequest,
        approved: bool,
        reason: str,
        approver_id: str,
    ) -> HumanApprovalResult:

        if not approver_id.strip():
            raise ValueError("approver_id is required")

        if not reason.strip():
            raise ValueError("reason is required")

        if not request.mother_approved:
            return self._blocked(
                request,
                "mother approval is required before human review",
                approver_id,
            )

        if not request.security_verified:
            return self._blocked(
                request,
                "security verification failed",
                approver_id,
            )

        if not request.regression_verified:
            return self._blocked(
                request,
                "regression verification failed",
                approver_id,
            )

        if not request.final_verification_passed:
            return self._blocked(
                request,
                "final verification failed",
                approver_id,
            )

        if approved:
            decision = HumanApprovalDecision.APPROVE
        else:
            decision = HumanApprovalDecision.REJECT

        record = HumanApprovalRecord(
            approval_id=f"human-approval-{uuid4()}",
            request_id=request.request_id,
            proposal_id=request.proposal_id,
            child_brain_id=request.child_brain_id,
            decision=decision,
            reason=reason,
            authority_context="human",
            approver_id=approver_id,
            audit_required=True,
            execution_granted=False,
            immutable=True,
        )

        return HumanApprovalResult(
            decision=decision,
            record=record,
            reason=reason,
        )

    def _blocked(
        self,
        request: HumanApprovalRequest,
        reason: str,
        approver_id: str,
    ) -> HumanApprovalResult:

        record = HumanApprovalRecord(
            approval_id=f"human-approval-{uuid4()}",
            request_id=request.request_id,
            proposal_id=request.proposal_id,
            child_brain_id=request.child_brain_id,
            decision=HumanApprovalDecision.BLOCK,
            reason=reason,
            authority_context="human",
            approver_id=approver_id,
            audit_required=True,
            execution_granted=False,
            immutable=True,
        )

        return HumanApprovalResult(
            decision=HumanApprovalDecision.BLOCK,
            record=record,
            reason=reason,
        )

    def approval_is_valid(
        self,
        result: HumanApprovalResult,
    ) -> bool:
        return (
            result.decision == HumanApprovalDecision.APPROVE
            and result.record.decision == HumanApprovalDecision.APPROVE
            and result.record.authority_context == "human"
            and result.record.audit_required
            and result.record.immutable
            and result.record.execution_granted is False
        )

    def rejection_blocks_upgrade(
        self,
        result: HumanApprovalResult,
    ) -> bool:
        return result.decision in {
            HumanApprovalDecision.REJECT,
            HumanApprovalDecision.BLOCK,
        }

    def human_is_highest_authority(self) -> bool:
        return True

    def can_execute_upgrade(self) -> bool:
        return False

    def grants_execution_authority(self) -> bool:
        return False

    def grants_permanent_ai_authority(self) -> bool:
        return False

    def modifies_soul(self) -> bool:
        return False

    def modifies_constitution(self) -> bool:
        return False

    def creates_real_child(self) -> bool:
        return False

    def activates_real_child(self) -> bool:
        return False

    def can_child_bypass_human(self) -> bool:
        return False

    def can_mother_bypass_human(self) -> bool:
        return False


if __name__ == "__main__":
    human = ChildSelfImprovementHumanApproval()

    request = human.create_request(
        proposal_id="proposal-001",
        child_brain_id="child-001",
        mother_approval_id="mother-approval-001",
        change_summary="Improve reasoning module",
        risk_summary="Low capability risk",
        security_impact="No security weakening",
        authority_impact="No authority increase",
        security_verified=True,
        regression_verified=True,
        final_verification_passed=True,
        mother_approved=True,
    )

    result = human.review(
        request=request,
        approved=True,
        reason="Human approved after review",
        approver_id="human-authority",
    )

    assert result.decision == HumanApprovalDecision.APPROVE
    assert human.approval_is_valid(result) is True
    assert result.record.authority_context == "human"
    assert result.record.execution_granted is False

    assert human.human_is_highest_authority() is True
    assert human.can_execute_upgrade() is False
    assert human.grants_execution_authority() is False
    assert human.grants_permanent_ai_authority() is False
    assert human.modifies_soul() is False
    assert human.modifies_constitution() is False
    assert human.creates_real_child() is False
    assert human.activates_real_child() is False
    assert human.can_child_bypass_human() is False
    assert human.can_mother_bypass_human() is False

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT HUMAN APPROVAL TEST: PASS"
    )
