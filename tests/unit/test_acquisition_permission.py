from core.policies.approval import (
    PermissionEngine,
)
from core.research.acquisition_permission import (
    AcquisitionPermissionGate,
)


def check(condition, message):
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main():
    print("SAHIBEX ACQUISITION PERMISSION GATE TEST")

    permission_engine = PermissionEngine()

    gate = AcquisitionPermissionGate(
        permission_engine
    )

    # ---------------------------------------------------------
    # 1. Gate requires the correct PermissionEngine
    # ---------------------------------------------------------

    try:
        AcquisitionPermissionGate(
            permission_engine="invalid"
        )
        raise AssertionError(
            "invalid permission engine should be rejected"
        )
    except TypeError:
        print(
            "[PASS] invalid permission engine rejected"
        )

    # ---------------------------------------------------------
    # 2. Network without confirmation must be blocked
    # ---------------------------------------------------------

    result = gate.check_network_access(
        confirmation=False
    )

    check(
        result.allowed is False,
        "network access blocked without confirmation",
    )

    check(
        result.requires_confirmation is True,
        "network access requires confirmation",
    )

    check(
        result.action == "network_access",
        "network action classified correctly",
    )

    check(
        result.risk == "medium",
        "network risk classified as medium",
    )

    # ---------------------------------------------------------
    # 3. require_network_access() must raise
    # ---------------------------------------------------------

    try:
        gate.require_network_access(
            confirmation=False
        )
        raise AssertionError(
            "network access should be blocked"
        )
    except PermissionError:
        print(
            "[PASS] require_network_access blocks "
            "without confirmation"
        )

    # ---------------------------------------------------------
    # 4. Explicit confirmation must allow network
    # ---------------------------------------------------------

    result = gate.check_network_access(
        confirmation=True
    )

    check(
        result.allowed is True,
        "network access allowed with confirmation",
    )

    check(
        result.requires_confirmation is False,
        "confirmation requirement cleared after approval",
    )

    check(
        result.action == "network_access",
        "approved action remains network_access",
    )

    # ---------------------------------------------------------
    # 5. require_network_access() succeeds
    # ---------------------------------------------------------

    result = gate.require_network_access(
        confirmation=True
    )

    check(
        result.allowed is True,
        "require_network_access succeeds after confirmation",
    )

    # ---------------------------------------------------------
    # 6. Gate does not execute network access
    # ---------------------------------------------------------

    check(
        not hasattr(gate, "request"),
        "permission gate has no network request method",
    )

    check(
        not hasattr(gate, "fetch"),
        "permission gate has no fetch method",
    )

    # ---------------------------------------------------------
    # 7. Permission decision remains auditable
    # ---------------------------------------------------------

    check(
        isinstance(result.reason, str)
        and len(result.reason) > 0,
        "permission decision contains reason",
    )

    print()
    print(
        "SAHIBEX ACQUISITION PERMISSION GATE TEST: PASS"
    )


if __name__ == "__main__":
    main()
