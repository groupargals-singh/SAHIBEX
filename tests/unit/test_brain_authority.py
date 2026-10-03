from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from core.policies.constitution import (
    ActionClass,
    ActionDecision,
    BrainRole,
    SahibexConstitution,
)


def main() -> None:
    print("=" * 60)
    print("SAHIBEX BRAIN AUTHORITY TEST")
    print("=" * 60)

    constitution = SahibexConstitution()

    # ---------------------------------------------------------
    # ROLE IDENTITY
    # ---------------------------------------------------------

    assert BrainRole.MOTHER_BRAIN.value == "mother_brain"
    print("[PASS] Mother Brain role exists")

    assert BrainRole.INTERNAL_ARMY.value == "internal_army"
    print("[PASS] Internal Army role exists")

    assert BrainRole.CHILD_BRAIN.value == "child_brain"
    print("[PASS] Child Brain role exists")

    # ---------------------------------------------------------
    # MOTHER BRAIN
    # ---------------------------------------------------------

    result = constitution.authorize_brain(
        brain_role=BrainRole.MOTHER_BRAIN,
        action=ActionClass.THINK,
    )

    assert result.allowed is True
    assert result.decision == ActionDecision.ALLOW
    print("[PASS] Mother Brain may think autonomously")

    # ---------------------------------------------------------
    # INTERNAL ARMY
    # ---------------------------------------------------------

    result = constitution.authorize_brain(
        brain_role=BrainRole.INTERNAL_ARMY,
        action=ActionClass.RESEARCH,
        parent_authorized=True,
    )

    assert result.allowed is True
    assert result.decision == ActionDecision.ALLOW
    print("[PASS] Internal Army may perform autonomous research")

    # ---------------------------------------------------------
    # CHILD BRAIN
    # ---------------------------------------------------------

    result = constitution.authorize_brain(
        brain_role=BrainRole.CHILD_BRAIN,
        action=ActionClass.READ,
        parent_authorized=True,
    )

    assert result.allowed is True
    assert result.decision == ActionDecision.ALLOW
    print("[PASS] Child Brain may perform autonomous read")

    # ---------------------------------------------------------
    # CHILD DENIED BY MOTHER
    # ---------------------------------------------------------

    result = constitution.authorize_brain(
        brain_role=BrainRole.CHILD_BRAIN,
        action=ActionClass.READ,
        parent_authorized=False,
    )

    assert result.allowed is False
    assert result.decision == ActionDecision.DENY
    print("[PASS] Child Brain is blocked when Mother Brain denies")

    # ---------------------------------------------------------
    # INTERNAL ARMY DENIED BY PARENT
    # ---------------------------------------------------------

    result = constitution.authorize_brain(
        brain_role=BrainRole.INTERNAL_ARMY,
        action=ActionClass.RESEARCH,
        parent_authorized=False,
    )

    assert result.allowed is False
    assert result.decision == ActionDecision.DENY
    print("[PASS] Internal Army cannot override parent denial")

    # ---------------------------------------------------------
    # PROTECTED CHILD ACTION
    # ---------------------------------------------------------

    result = constitution.authorize_brain(
        brain_role=BrainRole.CHILD_BRAIN,
        action=ActionClass.EXECUTE,
        parent_authorized=True,
    )

    assert result.allowed is False
    assert result.decision == ActionDecision.REQUIRE_CONFIRMATION
    print("[PASS] Child protected action requires user authorization")

    # ---------------------------------------------------------
    # USER AUTHORIZATION
    # ---------------------------------------------------------

    result = constitution.authorize_brain(
        brain_role=BrainRole.CHILD_BRAIN,
        action=ActionClass.EXECUTE,
        user_confirmation=True,
        parent_authorized=True,
    )

    assert result.allowed is True
    assert result.decision == ActionDecision.ALLOW
    print("[PASS] Explicit user authorization permits protected action")

    # ---------------------------------------------------------
    # CHILD CANNOT OVERRIDE MOTHER
    # ---------------------------------------------------------

    assert constitution.can_child_override_sahibex() is False
    print("[PASS] Child Brain cannot override Mother Brain")

    # ---------------------------------------------------------
    # INTERNAL ARMY CANNOT OVERRIDE MOTHER
    # ---------------------------------------------------------

    assert constitution.can_internal_army_override_mother() is False
    print("[PASS] Internal Army cannot override Mother Brain")

    # ---------------------------------------------------------
    # SUBORDINATE BRAINS CANNOT ELEVATE
    # ---------------------------------------------------------

    assert (
        constitution.can_brain_override_parent(
            BrainRole.INTERNAL_ARMY
        )
        is False
    )

    assert (
        constitution.can_brain_override_parent(
            BrainRole.CHILD_BRAIN
        )
        is False
    )

    assert (
        constitution.can_brain_override_parent(
            BrainRole.MOTHER_BRAIN
        )
        is True
    )

    print("[PASS] Brain authority elevation is blocked")

    # ---------------------------------------------------------
    # ORIGINAL CONSTITUTIONAL GUARANTEES
    # ---------------------------------------------------------

    assert constitution.can_sahibex_modify_constitution() is False
    print("[PASS] SAHIBEX cannot modify constitution")

    assert (
        constitution.can_sahibex_override_user(
            ActionClass.SYSTEM_CHANGE
        )
        is False
    )
    print("[PASS] SAHIBEX cannot override user authority")

    print("=" * 60)
    print("SAHIBEX BRAIN AUTHORITY TEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
