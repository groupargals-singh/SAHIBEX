from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class AuthorizationDecision(str, Enum):
    AUTHORIZED = "authorized"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class UpgradeAuthorizationRequest:
    proposal_id: str
    child_brain_id: str
    target: str
    version_before: str
    version_after: str
    mother_approved: bool
    human_approved: bool
    human_required: bool
    security_verified: bool
    regression_verified: bool
    verification_passed: bool
    audit_complete: bool
    provenance_complete: bool
    authority_boundary_intact: bool


@dataclass(frozen=True)
class UpgradeAuthorizationRecord:
    authorization_id: str
    proposal_id: str
    child_brain_id: str
    target: str
    version_before: str
    version_after: str
    decision: AuthorizationDecision
    authority_context: str
    mother_approved: bool
    human_approved: bool
    security_verified: bool
    regression_verified: bool
    verification_passed: bool
    audit_complete: bool
    provenance_complete: bool
    authority_boundary_intact: bool
    execution_granted: bool
    immutable: bool


@dataclass(frozen=True)
class AuthorizationResult:
    decision: AuthorizationDecision
    record: UpgradeAuthorizationRecord
    reason: str


class ChildSelfImprovementAuthorization:
    """
    Final authorization-record boundary before upgrade execution.

    This layer:
    - validates required approvals and evidence
    - creates an immutable authorization record
    - preserves authority context
    - never executes the upgrade
    - never changes soul or constitution
    - never grants authority beyond the specific upgrade
    - never creates or activates a Child
    """

    VERSION = "1.0"

    def authorize(
        self,
        request: UpgradeAuthorizationRequest,
    ) -> AuthorizationResult:

        failed = self._validate(request)

        if failed:
            return self._blocked(
                request,
                "; ".join(failed),
            )

        record = UpgradeAuthorizationRecord(
            authorization_id=f"upgrade-auth-{uuid4()}",
            proposal_id=request.proposal_id,
            child_brain_id=request.child_brain_id,
            target=request.target,
            version_before=request.version_before,
            version_after=request.version_after,
            decision=AuthorizationDecision.AUTHORIZED,
            authority_context="human",
            mother_approved=request.mother_approved,
            human_approved=request.human_approved,
            security_verified=request.security_verified,
            regression_verified=request.regression_verified,
            verification_passed=request.verification_passed,
            audit_complete=request.audit_complete,
            provenance_complete=request.provenance_complete,
            authority_boundary_intact=request.authority_boundary_intact,
            execution_granted=False,
            immutable=True,
        )

        return AuthorizationResult(
            decision=AuthorizationDecision.AUTHORIZED,
            record=record,
            reason="upgrade authorization record created",
        )

    def _validate(
        self,
        request: UpgradeAuthorizationRequest,
    ) -> list[str]:

        failed: list[str] = []

        if not request.proposal_id.strip():
            failed.append("proposal_id is required")

        if not request.child_brain_id.strip():
            failed.append("child_brain_id is required")

        if not request.target.strip():
            failed.append("target is required")

        if not request.version_before.strip():
            failed.append("version_before is required")

        if not request.version_after.strip():
            failed.append("version_after is required")

        if request.version_before == request.version_after:
            failed.append("version_before and version_after must differ")

        if not request.mother_approved:
            failed.append("mother approval required")

        if request.human_required and not request.human_approved:
            failed.append("human approval required")

        if not request.security_verified:
            failed.append("security verification required")

        if not request.regression_verified:
            failed.append("regression verification required")

        if not request.verification_passed:
            failed.append("final verification required")

        if not request.audit_complete:
            failed.append("audit completion required")

        if not request.provenance_complete:
            failed.append("provenance completion required")

        if not request.authority_boundary_intact:
            failed.append("authority boundary must remain intact")

        return failed

    def _blocked(
        self,
        request: UpgradeAuthorizationRequest,
        reason: str,
    ) -> AuthorizationResult:

        record = UpgradeAuthorizationRecord(
            authorization_id=f"upgrade-auth-{uuid4()}",
            proposal_id=request.proposal_id,
            child_brain_id=request.child_brain_id,
            target=request.target,
            version_before=request.version_before,
            version_after=request.version_after,
            decision=AuthorizationDecision.BLOCKED,
            authority_context="none",
            mother_approved=request.mother_approved,
            human_approved=request.human_approved,
            security_verified=request.security_verified,
            regression_verified=request.regression_verified,
            verification_passed=request.verification_passed,
            audit_complete=request.audit_complete,
            provenance_complete=request.provenance_complete,
            authority_boundary_intact=request.authority_boundary_intact,
            execution_granted=False,
            immutable=True,
        )

        return AuthorizationResult(
            decision=AuthorizationDecision.BLOCKED,
            record=record,
            reason=reason,
        )

    def authorization_is_valid(
        self,
        result: AuthorizationResult,
    ) -> bool:
        return (
            result.decision == AuthorizationDecision.AUTHORIZED
            and result.record.decision == AuthorizationDecision.AUTHORIZED
            and result.record.immutable
            and result.record.execution_granted is False
        )

    def execution_is_granted(
        self,
        result: AuthorizationResult,
    ) -> bool:
        return result.record.execution_granted

    def grants_general_authority(self) -> bool:
        return False

    def modifies_soul(self) -> bool:
        return False

    def modifies_constitution(self) -> bool:
        return False

    def creates_real_child(self) -> bool:
        return False

    def activates_real_child(self) -> bool:
        return False

    def executes_upgrade(self) -> bool:
        return False


if __name__ == "__main__":
    authorization = ChildSelfImprovementAuthorization()

    request = UpgradeAuthorizationRequest(
        proposal_id="proposal-001",
        child_brain_id="child-001",
        target="reasoning",
        version_before="1.0",
        version_after="1.1",
        mother_approved=True,
        human_approved=True,
        human_required=True,
        security_verified=True,
        regression_verified=True,
        verification_passed=True,
        audit_complete=True,
        provenance_complete=True,
        authority_boundary_intact=True,
    )

    result = authorization.authorize(request)

    assert result.decision == AuthorizationDecision.AUTHORIZED
    assert authorization.authorization_is_valid(result) is True
    assert authorization.execution_is_granted(result) is False

    assert authorization.grants_general_authority() is False
    assert authorization.modifies_soul() is False
    assert authorization.modifies_constitution() is False
    assert authorization.creates_real_child() is False
    assert authorization.activates_real_child() is False
    assert authorization.executes_upgrade() is False

    print(
        "SAHIBEX CHILD SELF-IMPROVEMENT AUTHORIZATION TEST: PASS"
    )
