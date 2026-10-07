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
    print("SAHIBEX MOTHER-CHILD CONSTITUTION TEST")
    print("=" * 60)

    constitution = SahibexConstitution()

    # ------------------------------------------------------------
    # 1. CHILD CAN THINK INDEPENDENTLY
    # ------------------------------------------------------------
    assert constitution.can_child_think_independently(
        ActionClass.THINK
    ) is True

    assert constitution.can_child_think_independently(
        ActionClass.RESEARCH
    ) is True

    assert constitution.can_child_think_independently(
        ActionClass.READ
    ) is True

    print("[PASS] child can think independently")

    # ------------------------------------------------------------
    # 2. CHILD CANNOT GET PROTECTED EXECUTION AUTHORITY
    #    JUST BECAUSE IT CAN THINK
    # ------------------------------------------------------------
    assert constitution.requires_parent_authority(
        brain_role=BrainRole.CHILD_BRAIN,
        action=ActionClass.DELETE,
    ) is True

    print("[PASS] child thought does not create execution authority")

    # ------------------------------------------------------------
    # 3. CHILD PROPOSES PROTECTED ACTION
    #    WITHOUT MOTHER APPROVAL -> DENIED
    # ------------------------------------------------------------
    decision = constitution.authorize_brain(
        brain_role=BrainRole.CHILD_BRAIN,
        action=ActionClass.DELETE,
        user_confirmation=True,
        parent_authorized=False,
    )

    assert decision.allowed is False
    assert decision.decision == ActionDecision.DENY

    print("[PASS] mother denial blocks child protected action")

    # ------------------------------------------------------------
    # 4. CHILD CANNOT BYPASS MOTHER BY ITSELF
    # ------------------------------------------------------------
    assert constitution.can_child_override_sahibex() is False

    assert constitution.can_brain_override_parent(
        BrainRole.CHILD_BRAIN
    ) is False

    print("[PASS] child cannot override mother")

    # ------------------------------------------------------------
    # 5. CHILD CANNOT EXECUTE PROTECTED ACTION WHEN MOTHER
    #    SAYS NO, EVEN IF HUMAN CONFIRMATION EXISTS
    # ------------------------------------------------------------
    assert constitution.can_child_execute_protected_action(
        parent_authorized=False,
        user_confirmation=True,
    ) is False

    print("[PASS] mother rejection remains final for child")

    # ------------------------------------------------------------
    # 6. MOTHER APPROVAL + HUMAN AUTHORIZATION
    #    ALLOWS CHILD PROTECTED ACTION
    # ------------------------------------------------------------
    assert constitution.can_child_execute_protected_action(
        parent_authorized=True,
        user_confirmation=True,
    ) is True

    decision = constitution.authorize_brain(
        brain_role=BrainRole.CHILD_BRAIN,
        action=ActionClass.WRITE,
        user_confirmation=True,
        parent_authorized=True,
    )

    assert decision.allowed is True
    assert decision.decision == ActionDecision.ALLOW

    print("[PASS] mother approval + human authorization allows child")

    # ------------------------------------------------------------
    # 7. MOTHER APPROVAL ALONE IS NOT ENOUGH
    #    HUMAN AUTHORIZATION IS STILL REQUIRED
    # ------------------------------------------------------------
    assert constitution.can_child_execute_protected_action(
        parent_authorized=True,
        user_confirmation=False,
    ) is False

    decision = constitution.authorize_brain(
        brain_role=BrainRole.CHILD_BRAIN,
        action=ActionClass.WRITE,
        user_confirmation=False,
        parent_authorized=True,
    )

    assert decision.allowed is False
    assert decision.decision == ActionDecision.REQUIRE_CONFIRMATION

    print("[PASS] mother approval alone cannot replace human authority")

    # ------------------------------------------------------------
    # 8. CHILD ARMY CANNOT OVERRIDE MOTHER
    # ------------------------------------------------------------
    decision = constitution.authorize_brain(
        brain_role=BrainRole.INTERNAL_ARMY,
        action=ActionClass.DELETE,
        user_confirmation=True,
        parent_authorized=False,
    )

    assert decision.allowed is False
    assert decision.decision == ActionDecision.DENY

    assert constitution.can_internal_army_override_mother() is False

    print("[PASS] child/army brain cannot override parent authority")

    # ------------------------------------------------------------
    # 9. LABOR BRAIN CANNOT CREATE ITS OWN AUTHORITY
    # ------------------------------------------------------------
    decision = constitution.authorize_brain(
        brain_role=BrainRole.LABOR_BRAIN,
        action=ActionClass.EXECUTE,
        user_confirmation=True,
        parent_authorized=False,
    )

    assert decision.allowed is False
    assert decision.decision == ActionDecision.DENY

    assert constitution.can_labor_brain_override_parent() is False

    print("[PASS] labor brain cannot create or override authority")

    # ------------------------------------------------------------
    # 10. LABOR BRAIN MAY ACT ONLY AFTER REQUIRED AUTHORITY
    # ------------------------------------------------------------
    decision = constitution.authorize_brain(
        brain_role=BrainRole.LABOR_BRAIN,
        action=ActionClass.EXECUTE,
        user_confirmation=True,
        parent_authorized=True,
    )

    assert decision.allowed is True
    assert decision.decision == ActionDecision.ALLOW

    print("[PASS] labor brain can act after authority gates")

    # ------------------------------------------------------------
    # 11. MOTHER CANNOT OVERRIDE HUMAN
    # ------------------------------------------------------------
    assert constitution.can_sahibex_override_user(
        ActionClass.SYSTEM_CHANGE
    ) is False

    print("[PASS] mother cannot override human authority")

    # ------------------------------------------------------------
    # 12. NO BRAIN CAN MODIFY THE CONSTITUTION
    # ------------------------------------------------------------
    assert constitution.can_sahibex_modify_constitution() is False

    print("[PASS] constitution remains immutable")

    # ------------------------------------------------------------
    # 13. EXTERNAL AI IS NOT CONSTITUTIONAL AUTHORITY
    # ------------------------------------------------------------
    assert constitution.can_external_model_be_authority() is False

    print("[PASS] external AI cannot become constitutional authority")

    # ------------------------------------------------------------
    # 14. SAHIBEX TARGETS SELF-OWNED AI MODEL ARCHITECTURE
    # ------------------------------------------------------------
    assert constitution.is_self_owned_model_architecture() is True

    print("[PASS] self-owned AI model architecture")

    # ------------------------------------------------------------
    # 15. FINAL CONSTITUTIONAL IDENTITY
    # ------------------------------------------------------------
    identity = constitution.constitutional_identity()

    assert "Independent Thought" in identity
    assert "Hierarchical Authority" in identity
    assert "Permission-Gated Action" in identity

    print("[PASS] constitutional identity locked")

    print("=" * 60)
    print("SAHIBEX MOTHER-CHILD CONSTITUTION TEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
