from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from core.policies.constitution import (
    ActionClass,
    ActionDecision,
    SahibexConstitution,
)


def main() -> None:
    constitution = SahibexConstitution()

    print("=" * 60)
    print("SAHIBEX CONSTITUTION TEST")
    print("=" * 60)

    decision = constitution.decide(
        ActionClass.THINK,
    )

    assert decision.decision == ActionDecision.ALLOW
    print("[PASS] thinking allowed")

    decision = constitution.decide(
        ActionClass.RESEARCH,
    )

    assert decision.decision == ActionDecision.ALLOW
    print("[PASS] research allowed")

    decision = constitution.decide(
        ActionClass.READ,
    )

    assert decision.decision == ActionDecision.ALLOW
    print("[PASS] read allowed")

    protected_actions = [
        ActionClass.WRITE,
        ActionClass.DELETE,
        ActionClass.EXECUTE,
        ActionClass.NETWORK,
        ActionClass.CREDENTIAL,
        ActionClass.SYSTEM_CHANGE,
        ActionClass.FINANCIAL,
        ActionClass.SELF_UPDATE,
        ActionClass.EXTERNAL_CONTROL,
    ]

    for action in protected_actions:
        decision = constitution.decide(action)

        assert (
            decision.decision
            == ActionDecision.REQUIRE_CONFIRMATION
        )

        print(
            f"[PASS] {action.value} "
            "requires user permission"
        )

    for action in protected_actions:
        decision = constitution.decide(
            action,
            user_confirmation=True,
        )

        assert decision.decision == ActionDecision.ALLOW

    print(
        "[PASS] explicit user permission "
        "allows protected actions"
    )

    assert (
        constitution.can_sahibex_override_user(
            ActionClass.SYSTEM_CHANGE
        )
        is False
    )

    print(
        "[PASS] SAHIBEX cannot override user authority"
    )

    assert (
        constitution.can_sahibex_modify_constitution()
        is False
    )

    print(
        "[PASS] SAHIBEX cannot modify its constitution"
    )

    print("=" * 60)
    print("SAHIBEX CONSTITUTION TEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
