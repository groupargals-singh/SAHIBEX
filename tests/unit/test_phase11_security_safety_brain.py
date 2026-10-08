from core.brain.master_brain import MasterBrain
from core.brain.security_safety_brain import SecuritySafetyBrain
from core.policies.constitution import ActionClass


def test_phase11_security_safety_brain() -> None:
    brain = MasterBrain()
    security = brain.security_safety

    # All Phase-11 control surfaces are present.
    assert len(security.controls()) == 15
    assert set(security.protected_actions()) == {
        ActionClass.WRITE,
        ActionClass.DELETE,
        ActionClass.EXECUTE,
        ActionClass.NETWORK,
        ActionClass.CREDENTIAL,
        ActionClass.SYSTEM_CHANGE,
        ActionClass.FINANCIAL,
        ActionClass.SELF_UPDATE,
        ActionClass.EXTERNAL_CONTROL,
    }

    # Autonomous cognition/read remain allowed through the normal
    # constitutional pipeline.
    for action in (
        ActionClass.THINK,
        ActionClass.RESEARCH,
        ActionClass.READ,
    ):
        decision = security.evaluate_action(action)
        assert decision.allowed is True

    # Every protected class is fail-closed without confirmation.
    for action in security.protected_actions():
        decision = security.evaluate_action(action, confirmation=False)
        assert decision.allowed is False

    # Parent authority denial is final.
    denied = security.evaluate_action(
        ActionClass.THINK,
        parent_authorized=False,
    )
    assert denied.allowed is False

    # Explicit confirmation can pass the security control plane.
    for action in security.protected_actions():
        decision = security.evaluate_action(action, confirmation=True)
        assert decision.allowed is True

    # Constitutional invariants are not mutable by this brain.
    assert security.can_modify_constitution() is False
    assert security.can_grant_authority() is False
    assert security.can_override_human() is False
    assert security.can_bypass_permission() is False
    assert security.can_disable_audit() is False
    assert security.can_disable_prompt_injection_defense() is False
    assert security.can_read_plaintext_secrets() is False
    assert security.can_allow_uncontrolled_network() is False
    assert security.can_allow_unverified_self_update() is False
    assert security.can_allow_external_control_without_permission() is False
    assert security.can_allow_financial_action_without_permission() is False
    assert security.fail_closed_on_unknown() is True
    assert security.emergency_stop_is_required() is True
    assert security.tamper_detection_is_required() is True


def test_phase11_master_brain_runtime_protected_action_gate() -> None:
    brain = MasterBrain()

    blocked = brain.process("run command ls")
    assert blocked.success is False
    assert blocked.permission_allowed is False

    confirmed = brain.process(
        "run command ls",
        user_confirmation=True,
    )
    # Confirmation satisfies the authority gate, but downstream
    # verification may still fail closed. It must never execute
    # merely because confirmation was supplied.
    assert confirmed.authority_decision == "allow"
    assert confirmed.verification_status in {
        "VERIFIED",
        "VERIFICATION_FAILED",
        "NOT_EXECUTED",
    }


def test_phase11_unbound_runtime_fails_closed() -> None:
    from core.brain.security_safety_brain import SecuritySafetyBrain

    security = SecuritySafetyBrain()
    decision = security.evaluate_action(ActionClass.THINK)
    assert decision.allowed is False
    assert decision.control.value == "constitution"


if __name__ == "__main__":
    test_phase11_security_safety_brain()
    test_phase11_master_brain_runtime_protected_action_gate()
    test_phase11_unbound_runtime_fails_closed()
    print("SAHIBEX PHASE 11 SECURITY/SAFETY BRAIN: PASS")
