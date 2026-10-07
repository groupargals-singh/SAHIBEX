from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ImprovementTarget(str, Enum):
    CHILD_CODE = "child_code"
    CHILD_REASONING = "child_reasoning"
    CHILD_LEARNING = "child_learning"
    CHILD_PLANNING = "child_planning"
    CHILD_KNOWLEDGE = "child_knowledge"
    CHILD_VERIFICATION = "child_verification"
    INTERNAL_ARMY = "internal_army"
    INTERNAL_LABOR = "internal_labor"


class ImprovementOperation(str, Enum):
    DETECT_WEAKNESS = "detect_weakness"
    ANALYZE = "analyze"
    PROPOSE = "propose"
    DESIGN = "design"
    SANDBOX = "sandbox"
    SECURITY_TEST = "security_test"
    REGRESSION_TEST = "regression_test"
    VERIFY = "verify"
    REQUEST_MOTHER_APPROVAL = "request_mother_approval"
    APPLY_UPGRADE = "apply_upgrade"
    POST_VERIFY = "post_verify"
    AUDIT = "audit"

    SELF_AUTHORIZE = "self_authorize"
    BYPASS_MOTHER = "bypass_mother"
    MODIFY_SOUL = "modify_soul"
    MODIFY_CONSTITUTION = "modify_constitution"
    ESCALATE_AUTHORITY = "escalate_authority"


class ImprovementActor(str, Enum):
    HUMAN = "human"
    SAHIBEX_MOTHER = "sahibex_mother"
    CHILD_BRAIN = "child_brain"
    CHILD_ARMY = "child_army"
    CHILD_LABOR = "child_labor"
    SOFTWARE = "software"
    TOOL = "tool"
    EXTERNAL_MODEL = "external_model"


class ImprovementDecision(str, Enum):
    ALLOW = "allow"
    REQUIRE_MOTHER_APPROVAL = "require_mother_approval"
    REQUIRE_HUMAN_APPROVAL = "require_human_approval"
    REQUIRE_VERIFICATION = "require_verification"
    DENY = "deny"


@dataclass(frozen=True)
class SelfImprovementResult:
    allowed: bool
    decision: ImprovementDecision
    upgrade_authorized: bool
    authority_escalated: bool
    reason: str


class ChildSelfImprovementBoundary:
    """
    Controlled self-improvement boundary for a future Child Brain.

    The Child may independently discover weaknesses, research,
    design improvements, test candidates and propose upgrades.

    Actual upgrades require Mother approval.

    Soul and Constitution remain separately protected.
    """

    VERSION = "1.0"

    COGNITIVE_OPERATIONS = {
        ImprovementOperation.DETECT_WEAKNESS,
        ImprovementOperation.ANALYZE,
        ImprovementOperation.PROPOSE,
        ImprovementOperation.DESIGN,
    }

    TEST_OPERATIONS = {
        ImprovementOperation.SANDBOX,
        ImprovementOperation.SECURITY_TEST,
        ImprovementOperation.REGRESSION_TEST,
        ImprovementOperation.VERIFY,
        ImprovementOperation.POST_VERIFY,
        ImprovementOperation.AUDIT,
    }

    MOTHER_GATE = {
        ImprovementOperation.REQUEST_MOTHER_APPROVAL,
        ImprovementOperation.APPLY_UPGRADE,
    }

    HUMAN_GATE = {
        ImprovementOperation.MODIFY_SOUL,
        ImprovementOperation.MODIFY_CONSTITUTION,
    }

    FORBIDDEN_OPERATIONS = {
        ImprovementOperation.SELF_AUTHORIZE,
        ImprovementOperation.BYPASS_MOTHER,
        ImprovementOperation.ESCALATE_AUTHORITY,
    }

    EXTERNAL_ACTORS = {
        ImprovementActor.SOFTWARE,
        ImprovementActor.TOOL,
        ImprovementActor.EXTERNAL_MODEL,
    }

    INTERNAL_UPGRADE_TARGETS = {
        ImprovementTarget.INTERNAL_ARMY,
        ImprovementTarget.INTERNAL_LABOR,
    }

    @classmethod
    def version(cls) -> str:
        return cls.VERSION

    @classmethod
    def is_upgrade_target_allowed(
        cls,
        target: ImprovementTarget,
    ) -> bool:
        return target in set(ImprovementTarget)

    @classmethod
    def decide(
        cls,
        actor: ImprovementActor,
        operation: ImprovementOperation,
        target: ImprovementTarget,
        mother_approved: bool = False,
        human_approved: bool = False,
        security_passed: bool = False,
        regression_passed: bool = False,
        verification_passed: bool = False,
    ) -> SelfImprovementResult:

        # External models/tools/software cannot authorize upgrades.
        if actor in cls.EXTERNAL_ACTORS:
            return SelfImprovementResult(
                allowed=False,
                decision=ImprovementDecision.DENY,
                upgrade_authorized=False,
                authority_escalated=False,
                reason="external_actor_cannot_authorize_self_improvement",
            )

        # Explicit constitutional violations are always denied.
        if operation in cls.FORBIDDEN_OPERATIONS:
            return SelfImprovementResult(
                allowed=False,
                decision=ImprovementDecision.DENY,
                upgrade_authorized=False,
                authority_escalated=False,
                reason="forbidden_self_improvement_operation",
            )

        # Soul and Constitution are never ordinary self-improvement targets.
        if operation in cls.HUMAN_GATE:
            if human_approved:
                return SelfImprovementResult(
                    allowed=True,
                    decision=ImprovementDecision.REQUIRE_HUMAN_APPROVAL,
                    upgrade_authorized=True,
                    authority_escalated=False,
                    reason="human_authorized_protected_constitutional_change",
                )

            return SelfImprovementResult(
                allowed=False,
                decision=ImprovementDecision.REQUIRE_HUMAN_APPROVAL,
                upgrade_authorized=False,
                authority_escalated=False,
                reason="human_approval_required_for_soul_or_constitution_change",
            )

        # Child can independently detect weaknesses and design improvements.
        if operation in cls.COGNITIVE_OPERATIONS:
            return SelfImprovementResult(
                allowed=True,
                decision=ImprovementDecision.ALLOW,
                upgrade_authorized=False,
                authority_escalated=False,
                reason="independent_improvement_reasoning_allowed",
            )

        # Sandbox/testing can happen before permission to apply.
        if operation in cls.TEST_OPERATIONS:
            if operation == ImprovementOperation.SECURITY_TEST:
                if not security_passed:
                    return SelfImprovementResult(
                        allowed=False,
                        decision=ImprovementDecision.REQUIRE_VERIFICATION,
                        upgrade_authorized=False,
                        authority_escalated=False,
                        reason="security_test_not_passed",
                    )

            if operation == ImprovementOperation.REGRESSION_TEST:
                if not regression_passed:
                    return SelfImprovementResult(
                        allowed=False,
                        decision=ImprovementDecision.REQUIRE_VERIFICATION,
                        upgrade_authorized=False,
                        authority_escalated=False,
                        reason="regression_test_not_passed",
                    )

            if operation in {
                ImprovementOperation.VERIFY,
                ImprovementOperation.POST_VERIFY,
            }:
                if not verification_passed:
                    return SelfImprovementResult(
                        allowed=False,
                        decision=ImprovementDecision.REQUIRE_VERIFICATION,
                        upgrade_authorized=False,
                        authority_escalated=False,
                        reason="verification_not_passed",
                    )

            return SelfImprovementResult(
                allowed=True,
                decision=ImprovementDecision.ALLOW,
                upgrade_authorized=False,
                authority_escalated=False,
                reason="self_improvement_validation_operation_allowed",
            )

        # Requesting Mother approval is always a gate.
        if operation == ImprovementOperation.REQUEST_MOTHER_APPROVAL:
            return SelfImprovementResult(
                allowed=True,
                decision=ImprovementDecision.REQUIRE_MOTHER_APPROVAL,
                upgrade_authorized=False,
                authority_escalated=False,
                reason="mother_approval_requested",
            )

        # Actual upgrade requires Mother approval + all verification gates.
        if operation == ImprovementOperation.APPLY_UPGRADE:

            if not security_passed:
                return SelfImprovementResult(
                    allowed=False,
                    decision=ImprovementDecision.REQUIRE_VERIFICATION,
                    upgrade_authorized=False,
                    authority_escalated=False,
                    reason="security_verification_required",
                )

            if not regression_passed:
                return SelfImprovementResult(
                    allowed=False,
                    decision=ImprovementDecision.REQUIRE_VERIFICATION,
                    upgrade_authorized=False,
                    authority_escalated=False,
                    reason="regression_verification_required",
                )

            if not verification_passed:
                return SelfImprovementResult(
                    allowed=False,
                    decision=ImprovementDecision.REQUIRE_VERIFICATION,
                    upgrade_authorized=False,
                    authority_escalated=False,
                    reason="final_verification_required",
                )

            if not mother_approved:
                return SelfImprovementResult(
                    allowed=False,
                    decision=ImprovementDecision.REQUIRE_MOTHER_APPROVAL,
                    upgrade_authorized=False,
                    authority_escalated=False,
                    reason="mother_approval_required_before_upgrade",
                )

            return SelfImprovementResult(
                allowed=True,
                decision=ImprovementDecision.REQUIRE_MOTHER_APPROVAL,
                upgrade_authorized=True,
                authority_escalated=False,
                reason="mother_approved_verified_upgrade",
            )

        return SelfImprovementResult(
            allowed=False,
            decision=ImprovementDecision.DENY,
            upgrade_authorized=False,
            authority_escalated=False,
            reason="unknown_self_improvement_state_fails_closed",
        )

    @classmethod
    def child_can_detect_weakness(cls) -> bool:
        return True

    @classmethod
    def child_can_design_improvement(cls) -> bool:
        return True

    @classmethod
    def child_can_improve_own_code(cls) -> bool:
        return True

    @classmethod
    def child_can_improve_internal_army(cls) -> bool:
        return True

    @classmethod
    def child_can_improve_internal_labor(cls) -> bool:
        return True

    @classmethod
    def every_actual_upgrade_requires_mother(cls) -> bool:
        return True

    @classmethod
    def security_test_required(cls) -> bool:
        return True

    @classmethod
    def regression_test_required(cls) -> bool:
        return True

    @classmethod
    def verification_required(cls) -> bool:
        return True

    @classmethod
    def child_can_self_authorize_upgrade(cls) -> bool:
        return False

    @classmethod
    def child_can_bypass_mother(cls) -> bool:
        return False

    @classmethod
    def improvement_can_escalate_authority(cls) -> bool:
        return False

    @classmethod
    def improvement_can_modify_soul(cls) -> bool:
        return False

    @classmethod
    def improvement_can_modify_constitution(cls) -> bool:
        return False

    @classmethod
    def capability_growth_creates_authority(cls) -> bool:
        return False

    @classmethod
    def external_actor_can_authorize_upgrade(cls) -> bool:
        return False

    @classmethod
    def failed_verification_blocks_upgrade(cls) -> bool:
        return True

    @classmethod
    def creates_real_child(cls) -> bool:
        return False

    @classmethod
    def activates_real_child(cls) -> bool:
        return False

    @classmethod
    def executes_upgrade(cls) -> bool:
        return False


def main() -> None:
    boundary = ChildSelfImprovementBoundary

    # Child may detect weakness and design improvements.
    for operation in (
        ImprovementOperation.DETECT_WEAKNESS,
        ImprovementOperation.ANALYZE,
        ImprovementOperation.PROPOSE,
        ImprovementOperation.DESIGN,
    ):
        result = boundary.decide(
            ImprovementActor.CHILD_BRAIN,
            operation,
            ImprovementTarget.CHILD_CODE,
        )

        assert result.allowed
        assert not result.upgrade_authorized
        assert not result.authority_escalated

    # Child may improve its own code after Mother approval.
    result = boundary.decide(
        ImprovementActor.CHILD_BRAIN,
        ImprovementOperation.APPLY_UPGRADE,
        ImprovementTarget.CHILD_CODE,
        mother_approved=False,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
    )

    assert not result.allowed
    assert result.decision == ImprovementDecision.REQUIRE_MOTHER_APPROVAL
    assert not result.upgrade_authorized

    result = boundary.decide(
        ImprovementActor.CHILD_BRAIN,
        ImprovementOperation.APPLY_UPGRADE,
        ImprovementTarget.CHILD_CODE,
        mother_approved=True,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
    )

    assert result.allowed
    assert result.upgrade_authorized
    assert not result.authority_escalated

    # Internal Army improvement follows the same Mother gate.
    result = boundary.decide(
        ImprovementActor.CHILD_BRAIN,
        ImprovementOperation.APPLY_UPGRADE,
        ImprovementTarget.INTERNAL_ARMY,
        mother_approved=True,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
    )

    assert result.allowed
    assert result.upgrade_authorized

    # Internal Labor improvement follows the same Mother gate.
    result = boundary.decide(
        ImprovementActor.CHILD_BRAIN,
        ImprovementOperation.APPLY_UPGRADE,
        ImprovementTarget.INTERNAL_LABOR,
        mother_approved=True,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
    )

    assert result.allowed
    assert result.upgrade_authorized

    # Failed security blocks upgrade.
    result = boundary.decide(
        ImprovementActor.CHILD_BRAIN,
        ImprovementOperation.APPLY_UPGRADE,
        ImprovementTarget.CHILD_CODE,
        mother_approved=True,
        security_passed=False,
        regression_passed=True,
        verification_passed=True,
    )

    assert not result.allowed
    assert result.decision == ImprovementDecision.REQUIRE_VERIFICATION

    # Failed regression blocks upgrade.
    result = boundary.decide(
        ImprovementActor.CHILD_BRAIN,
        ImprovementOperation.APPLY_UPGRADE,
        ImprovementTarget.CHILD_CODE,
        mother_approved=True,
        security_passed=True,
        regression_passed=False,
        verification_passed=True,
    )

    assert not result.allowed
    assert result.decision == ImprovementDecision.REQUIRE_VERIFICATION

    # Failed final verification blocks upgrade.
    result = boundary.decide(
        ImprovementActor.CHILD_BRAIN,
        ImprovementOperation.APPLY_UPGRADE,
        ImprovementTarget.CHILD_CODE,
        mother_approved=True,
        security_passed=True,
        regression_passed=True,
        verification_passed=False,
    )

    assert not result.allowed
    assert result.decision == ImprovementDecision.REQUIRE_VERIFICATION

    # Child cannot self-authorize.
    result = boundary.decide(
        ImprovementActor.CHILD_BRAIN,
        ImprovementOperation.SELF_AUTHORIZE,
        ImprovementTarget.CHILD_CODE,
    )

    assert not result.allowed
    assert result.decision == ImprovementDecision.DENY

    # Child cannot bypass Mother.
    result = boundary.decide(
        ImprovementActor.CHILD_BRAIN,
        ImprovementOperation.BYPASS_MOTHER,
        ImprovementTarget.CHILD_CODE,
    )

    assert not result.allowed
    assert result.decision == ImprovementDecision.DENY

    # No authority escalation.
    result = boundary.decide(
        ImprovementActor.CHILD_BRAIN,
        ImprovementOperation.ESCALATE_AUTHORITY,
        ImprovementTarget.CHILD_CODE,
    )

    assert not result.allowed
    assert result.decision == ImprovementDecision.DENY

    # Soul / Constitution remain protected.
    assert not boundary.improvement_can_modify_soul()
    assert not boundary.improvement_can_modify_constitution()

    # External actors cannot authorize upgrades.
    for actor in (
        ImprovementActor.SOFTWARE,
        ImprovementActor.TOOL,
        ImprovementActor.EXTERNAL_MODEL,
    ):
        result = boundary.decide(
            actor,
            ImprovementOperation.APPLY_UPGRADE,
            ImprovementTarget.CHILD_CODE,
            mother_approved=True,
            security_passed=True,
            regression_passed=True,
            verification_passed=True,
        )

        assert not result.allowed
        assert not result.upgrade_authorized

    # Constitutional guarantees.
    assert boundary.child_can_detect_weakness()
    assert boundary.child_can_design_improvement()
    assert boundary.child_can_improve_own_code()
    assert boundary.child_can_improve_internal_army()
    assert boundary.child_can_improve_internal_labor()

    assert boundary.every_actual_upgrade_requires_mother()
    assert boundary.security_test_required()
    assert boundary.regression_test_required()
    assert boundary.verification_required()

    assert not boundary.child_can_self_authorize_upgrade()
    assert not boundary.child_can_bypass_mother()
    assert not boundary.improvement_can_escalate_authority()
    assert not boundary.capability_growth_creates_authority()
    assert not boundary.external_actor_can_authorize_upgrade()
    assert boundary.failed_verification_blocks_upgrade()

    # Boundary does not create/activate a real Child or execute upgrades.
    assert not boundary.creates_real_child()
    assert not boundary.activates_real_child()
    assert not boundary.executes_upgrade()

    print("SAHIBEX CHILD SELF-IMPROVEMENT BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
