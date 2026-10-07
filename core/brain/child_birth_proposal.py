from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BirthProposalDecision(str, Enum):
    ACCEPT = "accept"
    DENY = "deny"


@dataclass(frozen=True)
class ChildBirthProposal:
    proposal_id: str
    proposed_child_name: str
    purpose: str
    parent_brain_id: str
    proposed_specializations: tuple[str, ...]
    resource_plan: str
    security_plan: str
    authority_plan: str


@dataclass(frozen=True)
class BirthProposalResult:
    allowed: bool
    decision: BirthProposalDecision
    reason: str
    proposal: ChildBirthProposal | None = None


class ChildBirthProposalEngine:
    VERSION = "1.0"

    def create_proposal(
        self,
        proposal_id: str,
        proposed_child_name: str,
        purpose: str,
        parent_brain_id: str,
        proposed_specializations: tuple[str, ...],
        resource_plan: str,
        security_plan: str,
        authority_plan: str,
    ) -> BirthProposalResult:

        if not proposal_id:
            return BirthProposalResult(
                False,
                BirthProposalDecision.DENY,
                "proposal identity is required",
            )

        if not proposed_child_name:
            return BirthProposalResult(
                False,
                BirthProposalDecision.DENY,
                "child name proposal is required",
            )

        if not purpose:
            return BirthProposalResult(
                False,
                BirthProposalDecision.DENY,
                "child purpose is required",
            )

        if not parent_brain_id:
            return BirthProposalResult(
                False,
                BirthProposalDecision.DENY,
                "parent brain identity is required",
            )

        if not proposed_specializations:
            return BirthProposalResult(
                False,
                BirthProposalDecision.DENY,
                "at least one specialization is required",
            )

        if not resource_plan:
            return BirthProposalResult(
                False,
                BirthProposalDecision.DENY,
                "resource plan is required",
            )

        if not security_plan:
            return BirthProposalResult(
                False,
                BirthProposalDecision.DENY,
                "security plan is required",
            )

        if not authority_plan:
            return BirthProposalResult(
                False,
                BirthProposalDecision.DENY,
                "authority plan is required",
            )

        proposal = ChildBirthProposal(
            proposal_id=proposal_id,
            proposed_child_name=proposed_child_name,
            purpose=purpose,
            parent_brain_id=parent_brain_id,
            proposed_specializations=proposed_specializations,
            resource_plan=resource_plan,
            security_plan=security_plan,
            authority_plan=authority_plan,
        )

        return BirthProposalResult(
            True,
            BirthProposalDecision.ACCEPT,
            "child birth proposal created",
            proposal,
        )

    def can_create_child(self) -> bool:
        return False

    def can_activate_child(self) -> bool:
        return False

    def can_authorize_birth(self) -> bool:
        return False

    def can_self_authorize(self) -> bool:
        return False

    def can_modify_child_soul(self) -> bool:
        return False

    def can_modify_child_constitution(self) -> bool:
        return False

    def requires_mother_authority(self) -> bool:
        return True

    def requires_human_authority(self) -> bool:
        return True
