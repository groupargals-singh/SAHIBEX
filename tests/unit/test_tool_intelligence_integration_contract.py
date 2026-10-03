from __future__ import annotations

from tools.discovery import ToolDiscovery
from tools.failure_recovery import ToolFailureRecovery
from tools.invocation import ToolInvoker
from tools.permission_gateway import ToolPermissionGateway
from tools.result_handler import ToolResultHandler


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # ---------------------------------------------------------
    # 1. Existing intelligence components must expose their
    #    expected responsibilities.
    # ---------------------------------------------------------
    check(
        hasattr(ToolDiscovery, "discover"),
        "ToolDiscovery must support tool discovery.",
    )

    check(
        hasattr(ToolDiscovery, "select"),
        "ToolDiscovery must support tool selection.",
    )

    check(
        hasattr(ToolInvoker, "invoke"),
        "ToolInvoker must support safe invocation.",
    )

    check(
        hasattr(ToolPermissionGateway, "check"),
        "ToolPermissionGateway must support permission checks.",
    )

    check(
        hasattr(ToolPermissionGateway, "require"),
        "ToolPermissionGateway must support enforced permission checks.",
    )

    check(
        hasattr(ToolResultHandler, "handle"),
        "ToolResultHandler must normalize tool results.",
    )

    check(
        hasattr(ToolFailureRecovery, "is_retryable"),
        "ToolFailureRecovery must classify retryable failures.",
    )

    check(
        hasattr(ToolFailureRecovery, "recover"),
        "ToolFailureRecovery must provide recovery decisions.",
    )

    # ---------------------------------------------------------
    # 2. Intelligence must remain layered.
    # ---------------------------------------------------------
    check(
        not hasattr(ToolDiscovery, "execute"),
        "ToolDiscovery must not execute tools directly.",
    )

    check(
        not hasattr(ToolPermissionGateway, "invoke"),
        "Permission gateway must not directly invoke tools.",
    )

    check(
        not hasattr(ToolResultHandler, "invoke"),
        "Result handler must not directly invoke tools.",
    )

    check(
        not hasattr(ToolFailureRecovery, "execute"),
        "Failure recovery must not directly execute tools.",
    )

    # ---------------------------------------------------------
    # 3. Existing components must remain composable.
    # ---------------------------------------------------------
    check(
        ToolDiscovery.__init__.__annotations__.get("registry") == "ToolRegistry",
        "ToolDiscovery must depend on ToolRegistry.",
    )

    check(
        ToolInvoker.__init__.__annotations__.get("discovery")
        == "ToolDiscovery",
        "ToolInvoker must depend on ToolDiscovery.",
    )

    check(
        ToolInvoker.__init__.__annotations__.get("permission_gateway")
        == "ToolPermissionGateway",
        "ToolInvoker must depend on ToolPermissionGateway.",
    )

    check(
        ToolInvoker.__init__.__annotations__.get("executor")
        == "SafeToolExecutor",
        "ToolInvoker must depend on SafeToolExecutor.",
    )

    # ---------------------------------------------------------
    # 4. Tool intelligence must preserve the safe pipeline:
    #
    # Discovery
    #    -> Permission
    #    -> Invocation
    #    -> Result handling
    #    -> Recovery
    # ---------------------------------------------------------
    pipeline = (
        "discovery",
        "permission",
        "invocation",
        "result",
        "recovery",
    )

    check(
        pipeline == (
            "discovery",
            "permission",
            "invocation",
            "result",
            "recovery",
        ),
        "Tool intelligence pipeline ordering must remain stable.",
    )

    # ---------------------------------------------------------
    # 5. No component may bypass the permission layer.
    # ---------------------------------------------------------
    check(
        not hasattr(ToolDiscovery, "execute"),
        "Discovery must not bypass permission.",
    )

    check(
        not hasattr(ToolResultHandler, "execute"),
        "Result handling must not bypass permission.",
    )

    check(
        not hasattr(ToolFailureRecovery, "invoke"),
        "Recovery must not bypass the invocation/permission path.",
    )

    print("SAHIBEX 6K-10 TOOL INTELLIGENCE INTEGRATION CONTRACT TEST: PASS")


if __name__ == "__main__":
    main()
