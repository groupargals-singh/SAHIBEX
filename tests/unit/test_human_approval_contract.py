from __future__ import annotations


from core.policies.constitution import (
    ActionClass,
    ActionDecision,
    AuthorityLevel,
    SahibexConstitution,
)


PROTECTED_ACTIONS = (
    ActionClass.WRITE,
    ActionClass.DELETE,
    ActionClass.EXECUTE,
    ActionClass.NETWORK,
    ActionClass.CREDENTIAL,
    ActionClass.SYSTEM_CHANGE,
    ActionClass.FINANCIAL,
    ActionClass.SELF_UPDATE,
    ActionClass.EXTERNAL_CONTROL,
)


AUTONOMOUS_ACTIONS = (
    ActionClass.THINK,
    ActionClass.RESEARCH,
    ActionClass.READ,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    constitution = SahibexConstitution()

    # -------------------------------------------------
    # 1. Protected actions require user authorization
    # -------------------------------------------------

    for action in PROTECTED_ACTIONS:
        decision = constitution.decide(
            action,
            user_confirmation=False,
        )

        check(
            decision.decision
            == ActionDecision.REQUIRE_CONFIRMATION,
            f"{action.value} must require user confirmation.",
        )

        check(
            decision.authority
            == AuthorityLevel.USER,
            f"{action.value} must remain under user authority.",
        )

        check(
            decision.reason != "",
            f"{action.value} must provide a reason.",
        )

    # -------------------------------------------------
    # 2. Explicit user authorization
    # -------------------------------------------------

    for action in PROTECTED_ACTIONS:
        decision = constitution.decide(
            action,
            user_confirmation=True,
        )

        check(
            decision.decision
            == ActionDecision.ALLOW,
            f"{action.value} must be allowed after explicit user authorization.",
        )

        check(
            decision.authority
            == AuthorityLevel.USER,
            f"{action.value} must retain USER authority.",
        )

    # -------------------------------------------------
    # 3. Autonomous actions
    # -------------------------------------------------

    for action in AUTONOMOUS_ACTIONS:
        decision = constitution.decide(
            action,
            user_confirmation=False,
        )

        check(
            decision.decision
            == ActionDecision.ALLOW,
            f"{action.value} must be autonomously allowed.",
        )

        check(
            decision.authority
            == AuthorityLevel.SAHIBEX,
            f"{action.value} must be under SAHIBEX authority.",
        )

    # -------------------------------------------------
    # 4. SAHIBEX cannot override user authority
    # -------------------------------------------------

    for action in PROTECTED_ACTIONS:
        check(
            constitution.can_sahibex_override_user(
                action
            )
            is False,
            f"SAHIBEX must never override {action.value} authority.",
        )

    # -------------------------------------------------
    # 5. SAHIBEX cannot modify constitution
    # -------------------------------------------------

    check(
        constitution.can_sahibex_modify_constitution()
        is False,
        "SAHIBEX must never modify its constitution.",
    )

    # -------------------------------------------------
    # 6. Unknown action fails closed
    # -------------------------------------------------

    class FakeAction:
        value = "unknown"

    try:
        constitution.decide(
            FakeAction(),  # type: ignore[arg-type]
            user_confirmation=True,
        )
    except TypeError as exc:
        check(
            str(exc)
            == "action must be an ActionClass.",
            "Unknown action must fail closed with a strict type error.",
        )
    else:
        raise AssertionError(
            "Unknown action object must not be accepted."
        )

    print(
        "[PASS] unknown action fails closed"
    )

    print(
        "SAHIBEX 6K-8 HUMAN APPROVAL CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
