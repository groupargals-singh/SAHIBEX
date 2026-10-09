from core.brain.child_lifecycle_boundary import (
    ChildLifecycleBoundary as Boundary,
    ChildLifecycleState as State,
    LifecycleActor as Actor,
    LifecycleOperation as Operation,
)


def test_child_birth_to_activation_requires_ordered_approvals_and_verification():
    birth = Boundary.decide(
        Actor.SAHIBEX_MOTHER, Operation.AUTHORIZE_BIRTH,
        State.PROPOSED, State.BIRTH_AUTHORIZED,
        mother_approved=True, authorization_valid=True,
    )
    assert birth.allowed is True

    created_without_human = Boundary.decide(
        Actor.SAHIBEX_MOTHER, Operation.CREATE,
        State.BIRTH_AUTHORIZED, State.CREATED,
        mother_approved=True, human_approved=False, authorization_valid=True,
    )
    assert created_without_human.allowed is False

    created = Boundary.decide(
        Actor.SAHIBEX_MOTHER, Operation.CREATE,
        State.BIRTH_AUTHORIZED, State.CREATED,
        mother_approved=True, human_approved=True, authorization_valid=True,
    )
    assert created.allowed is True

    verified_without_check = Boundary.decide(
        Actor.SAHIBEX_MOTHER, Operation.VERIFY,
        State.CREATED, State.VERIFIED, verification_passed=False,
    )
    assert verified_without_check.allowed is False

    verified = Boundary.decide(
        Actor.SAHIBEX_MOTHER, Operation.VERIFY,
        State.CREATED, State.VERIFIED, verification_passed=True,
    )
    assert verified.allowed is True

    ready = Boundary.decide(
        Actor.SAHIBEX_MOTHER, Operation.MARK_READY,
        State.VERIFIED, State.READY, verification_passed=True,
    )
    assert ready.allowed is True

    activated = Boundary.decide(
        Actor.SAHIBEX_MOTHER, Operation.ACTIVATE,
        State.READY, State.ACTIVE, mother_approved=True,
    )
    assert activated.allowed is True


def test_lifecycle_operation_cannot_be_reused_for_an_unrelated_transition():
    mismatched = Boundary.decide(
        Actor.SAHIBEX_MOTHER, Operation.CREATE,
        State.ACTIVE, State.PAUSED,
        mother_approved=True, human_approved=True, authorization_valid=True,
    )
    assert mismatched.allowed is False
    assert mismatched.reason == "operation_does_not_match_lifecycle_transition"


def test_proposal_does_not_change_state_or_grant_authority():
    result = Boundary.decide(
        Actor.SAHIBEX_MOTHER, Operation.PROPOSE,
        State.PROPOSED, State.PROPOSED,
    )
    assert result.allowed is True
    assert result.authority_granted is False
