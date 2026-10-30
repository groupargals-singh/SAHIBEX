"""Fail-closed invocation smoke coverage for every registered internal role.

This proves that each handler can be dispatched with empty diagnostic input and
returns a structured result without an uncaught exception. It does NOT prove
valid-input behavior, external integrations, or production-grade capability.
"""
from core.brain.master_brain import MasterBrain


def test_every_registered_internal_role_handles_empty_diagnostic_input():
    brain = MasterBrain()
    roles = brain.internal_brain_team.roles()
    assert len(roles) == 61
    role_ids = [role.role_id for role in roles]
    assert len(set(role_ids)) == len(role_ids)

    for role_id in role_ids:
        dispatch = brain.dispatch_internal_brain(
            role_id,
            "diagnostic empty-input invocation smoke",
            {},
            authorization_passed=True,
            verification_passed=True,
        )
        assert dispatch is not None, role_id
        assert isinstance(dispatch.accepted, bool), role_id
        assert isinstance(dispatch.result, dict), role_id
        assert dispatch.result, role_id


def test_every_internal_role_fails_closed_without_authorization():
    brain = MasterBrain()
    for role in brain.internal_brain_team.roles():
        dispatch = brain.dispatch_internal_brain(
            role.role_id,
            "unauthorized diagnostic invocation",
            {},
            authorization_passed=False,
            verification_passed=True,
        )
        assert dispatch.accepted is False, role.role_id
        assert dispatch.result is None, role.role_id
        assert "authorization" in dispatch.reason.lower(), role.role_id


def test_every_internal_role_fails_closed_without_request_verification():
    brain = MasterBrain()
    for role in brain.internal_brain_team.roles():
        dispatch = brain.dispatch_internal_brain(
            role.role_id,
            "unverified diagnostic invocation",
            {},
            authorization_passed=True,
            verification_passed=False,
        )
        assert dispatch.accepted is False, role.role_id
        assert dispatch.result is None, role.role_id
        assert "verification" in dispatch.reason.lower(), role.role_id
