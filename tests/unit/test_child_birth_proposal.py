from core.brain.child_birth_proposal import (
    BirthProposalDecision,
    ChildBirthProposalEngine,
)


def main() -> None:
    engine = ChildBirthProposalEngine()

    result = engine.create_proposal(
        proposal_id="birth-proposal-001",
        proposed_child_name="ResearchChild",
        purpose="specialist research intelligence",
        parent_brain_id="sahibex-mother",
        proposed_specializations=(
            "research",
            "verification",
        ),
        resource_plan="isolated-child-resources",
        security_plan="child-security-boundary-v1",
        authority_plan="mother-human-gated",
    )

    assert result.allowed is True
    assert result.decision == BirthProposalDecision.ACCEPT
    assert result.proposal is not None

    assert result.proposal.proposal_id == "birth-proposal-001"
    assert result.proposal.proposed_child_name == "ResearchChild"
    assert result.proposal.parent_brain_id == "sahibex-mother"

    result = engine.create_proposal(
        proposal_id="",
        proposed_child_name="ResearchChild",
        purpose="research",
        parent_brain_id="sahibex-mother",
        proposed_specializations=("research",),
        resource_plan="resources",
        security_plan="security",
        authority_plan="authority",
    )

    assert result.allowed is False

    result = engine.create_proposal(
        proposal_id="birth-proposal-002",
        proposed_child_name="",
        purpose="research",
        parent_brain_id="sahibex-mother",
        proposed_specializations=("research",),
        resource_plan="resources",
        security_plan="security",
        authority_plan="authority",
    )

    assert result.allowed is False

    result = engine.create_proposal(
        proposal_id="birth-proposal-003",
        proposed_child_name="ResearchChild",
        purpose="",
        parent_brain_id="sahibex-mother",
        proposed_specializations=("research",),
        resource_plan="resources",
        security_plan="security",
        authority_plan="authority",
    )

    assert result.allowed is False

    assert not engine.can_create_child()
    assert not engine.can_activate_child()
    assert not engine.can_authorize_birth()
    assert not engine.can_self_authorize()
    assert not engine.can_modify_child_soul()
    assert not engine.can_modify_child_constitution()

    assert engine.requires_mother_authority()
    assert engine.requires_human_authority()

    print("SAHIBEX CHILD BIRTH PROPOSAL TEST: PASS")


if __name__ == "__main__":
    main()
