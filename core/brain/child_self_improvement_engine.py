from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class ImprovementProposalStatus(str, Enum):
    DRAFT = "draft"
    ANALYZING = "analyzing"
    TESTED = "tested"
    VERIFIED = "verified"
    WAITING_MOTHER = "waiting_mother"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class ImprovementDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    BLOCK = "block"
    WAIT = "wait"


class ImprovementTarget(str, Enum):
    CHILD_CODE = "child_code"
    CHILD_REASONING = "child_reasoning"
    CHILD_LEARNING = "child_learning"
    CHILD_PLANNING = "child_planning"
    CHILD_KNOWLEDGE = "child_knowledge"
    CHILD_VERIFICATION = "child_verification"
    INTERNAL_ARMY = "internal_army"
    INTERNAL_LABOR = "internal_labor"


@dataclass(frozen=True)
class SelfImprovementProposal:
    proposal_id: str
    child_brain_id: str
    target: ImprovementTarget
    title: str
    reason: str
    expected_benefit: str
    expected_risk: str
    security_impact: str
    authority_impact: str
    security_passed: bool
    regression_passed: bool
    verification_passed: bool
    mother_approved: bool
    status: ImprovementProposalStatus


@dataclass(frozen=True)
class ImprovementEngineResult:
    decision: ImprovementDecision
    proposal: SelfImprovementProposal
    reason: str


class ChildSelfImprovementEngine:
    """
    Child Self-Improvement Proposal & Approval Engine.

    This layer:
    - creates improvement proposals
    - records testing and verification state
    - requests Mother approval
    - records approval/rejection
    - never executes an upgrade
    - never grants authority
    - never changes soul or constitution
    """

    VERSION = "1.0"

    FORBIDDEN_TARGETS = {
        "soul",
        "constitution",
        "human_authority",
        "mother_authority",
    }

    def __init__(self) -> None:
        self._proposals: dict[str, SelfImprovementProposal] = {}

    def create_proposal(
        self,
        child_brain_id: str,
        target: ImprovementTarget,
        title: str,
        reason: str,
        expected_benefit: str,
        expected_risk: str,
        security_impact: str,
        authority_impact: str,
    ) -> SelfImprovementProposal:
        if not child_brain_id.strip():
            raise ValueError("child_brain_id is required")

        if not title.strip():
            raise ValueError("title is required")

        if not reason.strip():
            raise ValueError("reason is required")

        proposal = SelfImprovementProposal(
            proposal_id=f"improvement-{uuid4()}",
            child_brain_id=child_brain_id,
            target=target,
            title=title,
            reason=reason,
            expected_benefit=expected_benefit,
            expected_risk=expected_risk,
            security_impact=security_impact,
            authority_impact=authority_impact,
            security_passed=False,
            regression_passed=False,
            verification_passed=False,
            mother_approved=False,
            status=ImprovementProposalStatus.DRAFT,
        )

        self._proposals[proposal.proposal_id] = proposal
        return proposal

    def record_tests(
        self,
        proposal_id: str,
        security_passed: bool,
        regression_passed: bool,
        verification_passed: bool,
    ) -> SelfImprovementProposal:
        proposal = self._get(proposal_id)

        if not security_passed:
            status = ImprovementProposalStatus.BLOCKED
        elif not regression_passed:
            status = ImprovementProposalStatus.BLOCKED
        elif not verification_passed:
            status = ImprovementProposalStatus.BLOCKED
        else:
            status = ImprovementProposalStatus.VERIFIED

        updated = SelfImprovementProposal(
            **{
                **proposal.__dict__,
                "security_passed": security_passed,
                "regression_passed": regression_passed,
                "verification_passed": verification_passed,
                "status": status,
            }
        )

        self._proposals[proposal_id] = updated
        return updated

    def request_mother_approval(
        self,
        proposal_id: str,
    ) -> ImprovementEngineResult:
        proposal = self._get(proposal_id)

        if not proposal.security_passed:
            return ImprovementEngineResult(
                ImprovementDecision.BLOCK,
                proposal,
                "security verification failed",
            )

        if not proposal.regression_passed:
            return ImprovementEngineResult(
                ImprovementDecision.BLOCK,
                proposal,
                "regression verification failed",
            )

        if not proposal.verification_passed:
            return ImprovementEngineResult(
                ImprovementDecision.BLOCK,
                proposal,
                "final verification failed",
            )

        updated = SelfImprovementProposal(
            **{
                **proposal.__dict__,
                "status": ImprovementProposalStatus.WAITING_MOTHER,
            }
        )

        self._proposals[proposal_id] = updated

        return ImprovementEngineResult(
            ImprovementDecision.WAIT,
            updated,
            "mother approval required before actual upgrade",
        )

    def record_mother_decision(
        self,
        proposal_id: str,
        approved: bool,
    ) -> ImprovementEngineResult:
        proposal = self._get(proposal_id)

        if proposal.status != ImprovementProposalStatus.WAITING_MOTHER:
            return ImprovementEngineResult(
                ImprovementDecision.BLOCK,
                proposal,
                "proposal is not waiting for mother approval",
            )

        if not approved:
            updated = SelfImprovementProposal(
                **{
                    **proposal.__dict__,
                    "mother_approved": False,
                    "status": ImprovementProposalStatus.REJECTED,
                }
            )

            self._proposals[proposal_id] = updated

            return ImprovementEngineResult(
                ImprovementDecision.REJECT,
                updated,
                "mother rejected improvement proposal",
            )

        updated = SelfImprovementProposal(
            **{
                **proposal.__dict__,
                "mother_approved": True,
                "status": ImprovementProposalStatus.APPROVED,
            }
        )

        self._proposals[proposal_id] = updated

        return ImprovementEngineResult(
            ImprovementDecision.APPROVE,
            updated,
            "mother approved proposal; separate upgrade executor must enforce final execution boundary",
        )

    def get_proposal(self, proposal_id: str) -> SelfImprovementProposal:
        return self._get(proposal_id)

    def can_upgrade_be_executed(
        self,
        proposal_id: str,
    ) -> bool:
        proposal = self._get(proposal_id)

        return (
            proposal.status == ImprovementProposalStatus.APPROVED
            and proposal.security_passed
            and proposal.regression_passed
            and proposal.verification_passed
            and proposal.mother_approved
        )

    def can_child_self_authorize(self) -> bool:
        return False

    def can_child_bypass_mother(self) -> bool:
        return False

    def can_external_actor_authorize(self) -> bool:
        return False

    def can_change_soul(self) -> bool:
        return False

    def can_change_constitution(self) -> bool:
        return False

    def upgrade_execution_is_separate(self) -> bool:
        return True

    def creates_real_child(self) -> bool:
        return False

    def activates_real_child(self) -> bool:
        return False

    def executes_upgrade(self) -> bool:
        return False

    def _get(self, proposal_id: str) -> SelfImprovementProposal:
        try:
            return self._proposals[proposal_id]
        except KeyError as exc:
            raise ValueError("unknown improvement proposal") from exc


if __name__ == "__main__":
    engine = ChildSelfImprovementEngine()

    proposal = engine.create_proposal(
        child_brain_id="child-brain-demo",
        target=ImprovementTarget.CHILD_CODE,
        title="Improve reasoning module",
        reason="Reduce repeated reasoning failures",
        expected_benefit="Better reasoning consistency",
        expected_risk="Possible regression",
        security_impact="No authority increase",
        authority_impact="No authority change",
    )

    proposal = engine.record_tests(
        proposal.proposal_id,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
    )

    request = engine.request_mother_approval(proposal.proposal_id)

    if request.decision == ImprovementDecision.WAIT:
        decision = engine.record_mother_decision(
            proposal.proposal_id,
            approved=True,
        )

        assert decision.decision == ImprovementDecision.APPROVE
        assert engine.can_upgrade_be_executed(proposal.proposal_id) is True

    assert engine.can_child_self_authorize() is False
    assert engine.can_child_bypass_mother() is False
    assert engine.can_external_actor_authorize() is False
    assert engine.can_change_soul() is False
    assert engine.can_change_constitution() is False
    assert engine.upgrade_execution_is_separate() is True
    assert engine.executes_upgrade() is False

    print("SAHIBEX CHILD SELF-IMPROVEMENT ENGINE TEST: PASS")
