from __future__ import annotations

from core.policies.constitution import (
    ActionClass,
    ActionDecision,
    AuthorityLevel,
)
from tools.human_approval import HumanApprovalGateway


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
    gateway = HumanApprovalGateway()

    # Protected actions must require explicit user approval.
    for action in PROTECTED_ACTIONS:
        result = gateway.check(action)

        check(
            result.allowed is False,
            f"{action.value} must not be allowed without approval.",
        )
        check(
            result.requires_confirmation is True,
            f"{action.value} must require confirmation.",
        )
        check(
            result.decision == ActionDecision.REQUIRE_CONFIRMATION,
            f"{action.value} must return REQUIRE_CONFIRMATION.",
        )
        check(
            result.authority == AuthorityLevel.USER,
            f"{action.value} must remain under USER authority.",
        )

    # Explicit user authorization must allow protected actions.
    for action in PROTECTED_ACTIONS:
        result = gateway.check(
            action,
            user_confirmation=True,
        )

        check(
            result.allowed is True,
            f"{action.value} must be allowed after user approval.",
        )
        check(
            result.requires_confirmation is False,
            f"{action.value} must not require further confirmation.",
        )
        check(
            result.decision == ActionDecision.ALLOW,
            f"{action.value} must return ALLOW after approval.",
        )
        check(
            result.authority == AuthorityLevel.USER,
            f"{action.value} must retain USER authority.",
        )

    # Autonomous actions must remain directly allowed.
    for action in AUTONOMOUS_ACTIONS:
        result = gateway.check(action)

        check(
            result.allowed is True,
            f"{action.value} must be autonomously allowed.",
        )
        check(
            result.requires_confirmation is False,
            f"{action.value} must not require confirmation.",
        )
        check(
            result.decision == ActionDecision.ALLOW,
            f"{action.value} must return ALLOW.",
        )
        check(
            result.authority == AuthorityLevel.SAHIBEX,
            f"{action.value} must use SAHIBEX authority.",
        )

    # require() must block protected actions without approval.
    try:
        gateway.require(ActionClass.WRITE)
    except PermissionError:
        pass
    else:
        raise AssertionError(
            "require() must block WRITE without user approval."
        )

    # require() must allow after explicit user approval.
    result = gateway.require(
        ActionClass.WRITE,
        user_confirmation=True,
    )

    check(
        result.allowed is True,
        "require() must allow WRITE after approval.",
    )

    # Type safety.
    try:
        gateway.check("write")  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError(
            "gateway.check() must reject invalid action types."
        )

    print("SAHIBEX 6K-8 HUMAN APPROVAL RUNTIME TEST: PASS")


if __name__ == "__main__":
    main()
