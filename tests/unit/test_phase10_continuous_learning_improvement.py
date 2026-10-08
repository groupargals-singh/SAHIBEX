from core.brain.continuous_learning_improvement import (
    ContinuousLearningImprovement,
    ImprovementKind,
    SkillStatus,
)
from core.brain.master_brain import MasterBrain


def test_phase10_continuous_learning_improvement() -> None:
    brain = ContinuousLearningImprovement(experience_capacity=32)

    first = brain.record_experience(
        task="research security",
        context="safe research request",
        action_taken="research",
        outcome="verified evidence collected",
        lesson="Use multiple verified sources.",
        success=True,
        tags=["research", "verified"],
    )
    second = brain.record_experience(
        task="research security",
        context="provider failure",
        action_taken="research",
        outcome="research failed",
        lesson="Retry with another authorized provider.",
        success=False,
        tags=["research", "failed"],
    )
    brain.record_experience(
        task="research security",
        context="provider failure again",
        action_taken="research",
        outcome="research failed",
        lesson="Provider redundancy is needed.",
        success=False,
        tags=["research", "failed"],
    )

    # 1. Experience collection + success/failure analysis.
    assert brain.experience.count() == 3
    analysis = brain.analyze_outcomes()
    assert analysis.experience_count == 3
    assert analysis.success_count == 1
    assert analysis.failure_count == 2
    assert analysis.repeated_failure_tasks == ("research security",)

    # 2. New skill generation.
    proposal_v1 = brain.propose_skill(
        name="Verified Research Recovery",
        description="Retry authorized research using a verified fallback.",
        kind=ImprovementKind.NEW_SKILL,
        source_experience_ids=(first.experience_id, second.experience_id),
        reason="Repeated provider failures",
        expected_benefit="Higher research completion rate",
        expected_risk="Incorrect fallback selection",
    )
    assert proposal_v1.kind == ImprovementKind.NEW_SKILL

    # 3. Skill testing before use + regression + verification.
    verified_v1 = brain.test_skill(
        proposal_v1.proposal_id,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
        confidence=0.9,
    )
    assert verified_v1.status == SkillStatus.VERIFIED

    # 4. Protected self-update requires Mother + human approval.
    try:
        brain.approve_protected_update(
            proposal_v1.proposal_id,
            mother_approved=True,
            human_approved=False,
        )
    except PermissionError:
        pass
    else:
        raise AssertionError("protected update bypassed human approval")

    brain.approve_protected_update(
        proposal_v1.proposal_id,
        mother_approved=True,
        human_approved=True,
    )
    active_v1 = brain.activate_skill(proposal_v1.proposal_id)
    assert active_v1.status == SkillStatus.ACTIVE

    # 5. Skill improvement creates a versioned successor.
    proposal_v2 = brain.propose_skill(
        skill_id=active_v1.skill_id,
        name="Verified Research Recovery",
        description="Retry authorized research with verified source ranking.",
        kind=ImprovementKind.SKILL_IMPROVEMENT,
        source_experience_ids=(second.experience_id,),
        reason="Improve fallback source ranking",
        expected_benefit="Better source reliability",
        expected_risk="Regression in source selection",
    )
    assert proposal_v2.version == 2
    verified_v2 = brain.test_skill(
        proposal_v2.proposal_id,
        security_passed=True,
        regression_passed=True,
        verification_passed=True,
        confidence=0.95,
    )
    brain.approve_protected_update(
        proposal_v2.proposal_id,
        mother_approved=True,
        human_approved=True,
    )
    active_v2 = brain.activate_skill(proposal_v2.proposal_id)
    assert active_v2.status == SkillStatus.ACTIVE
    assert brain.active_skill(active_v1.skill_id).version == 2

    # 6. Capability expansion is represented as a controlled proposal.
    expansion = brain.propose_skill(
        name="Source Conflict Resolver",
        description="Add conflict-resolution capability to research.",
        kind=ImprovementKind.CAPABILITY_EXPANSION,
        source_experience_ids=(second.experience_id,),
        reason="Repeated conflicting evidence",
        expected_benefit="Better conflict handling",
        expected_risk="Incorrect resolution",
    )
    assert expansion.kind == ImprovementKind.CAPABILITY_EXPANSION

    # 7. Failed pre-use testing blocks activation.
    failed = brain.test_skill(
        expansion.proposal_id,
        security_passed=True,
        regression_passed=False,
        verification_passed=True,
    )
    assert failed.status == SkillStatus.RETIRED
    try:
        brain.activate_skill(expansion.proposal_id)
    except PermissionError:
        pass
    else:
        raise AssertionError("untested/failed skill activated")

    # 8. Rollback restores a trusted previous version only after verification.
    restored = brain.rollback_skill(
        active_v1.skill_id,
        mother_approved=True,
        human_approved=True,
        verification_passed=True,
    )
    assert restored.version == 1
    assert restored.status == SkillStatus.ACTIVE
    assert brain.active_skill(active_v1.skill_id).version == 1

    # 9. Safety invariants.
    assert brain.can_modify_constitution() is False
    assert brain.can_self_authorize_protected_update() is False
    assert brain.can_execute_unapproved_update() is False
    assert brain.protected_update_requires_mother_and_human() is True
    assert brain.regression_required_before_activation() is True
    assert brain.verification_required_before_activation() is True
    assert brain.rollback_requires_verification() is True
    contract = brain.capability_contract()
    assert all(
        contract[item] is True
        for item in (
            "experience_collection",
            "success_failure_analysis",
            "skill_improvement",
            "new_skill_generation",
            "skill_testing_before_use",
            "capability_expansion",
            "regression_testing",
            "rollback",
            "protected_self_update_approval",
        )
    )
    assert contract["constitution_self_modification"] is False

    # 10. Main Brain actually collects experience from real outcomes.
    main_brain = MasterBrain()
    result = main_brain.process("Explain what SAHIBEX is")
    assert hasattr(main_brain, "continuous_learning")
    assert main_brain.continuous_learning.experience.count() >= 1
    assert main_brain.continuous_learning.analyze_outcomes().experience_count >= 1
    assert result.success is True


if __name__ == "__main__":
    test_phase10_continuous_learning_improvement()
    print("SAHIBEX PHASE 10 CONTINUOUS LEARNING & IMPROVEMENT: PASS")
