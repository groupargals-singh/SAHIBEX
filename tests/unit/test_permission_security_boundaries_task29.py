from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.policies.approval import ActionType, PermissionEngine
from tools.executor import SafeToolExecutor
from tools.permission_gateway import ToolPermissionGateway
from tools.registry import ToolRegistry


def _registry(*, read_only: bool, protected_action: ActionType | None) -> tuple[ToolRegistry, list[dict[str, object]]]:
    registry = ToolRegistry()
    calls: list[dict[str, object]] = []

    def handler(**kwargs: object) -> dict[str, object]:
        calls.append(dict(kwargs))
        return {"executed": True}

    registry.register(
        name="protected_test_tool",
        description="Test-only protected tool.",
        handler=handler,
        read_only=read_only,
        requires_confirmation=not read_only,
        protected_action=protected_action,
    )
    return registry, calls


def test_permission_engine_rejects_non_boolean_confirmation() -> None:
    engine = PermissionEngine()
    for invalid in ("false", 1, None):
        try:
            engine.check(ActionType.WRITE_FILE, confirmation=invalid)  # type: ignore[arg-type]
        except TypeError:
            pass
        else:
            raise AssertionError(f"accepted invalid confirmation: {invalid!r}")


def test_tool_gateway_rejects_non_boolean_confirmation() -> None:
    registry, _ = _registry(read_only=False, protected_action=ActionType.WRITE_FILE)
    gateway = ToolPermissionGateway(PermissionEngine(), registry)
    for invalid in ("false", 1, None):
        try:
            gateway.check("protected_test_tool", confirmation=invalid)  # type: ignore[arg-type]
        except TypeError:
            pass
        else:
            raise AssertionError(f"accepted invalid confirmation: {invalid!r}")


def test_caller_cannot_forge_permission_boolean_on_unbound_executor() -> None:
    registry, calls = _registry(read_only=False, protected_action=ActionType.WRITE_FILE)
    result = SafeToolExecutor(registry).execute(
        "protected_test_tool", _permission_granted=True
    )
    assert not result.success
    assert "no canonical permission gateway" in (result.error or "")
    assert calls == []


def test_executor_rechecks_gateway_and_only_injects_grant_after_approval() -> None:
    registry, calls = _registry(read_only=False, protected_action=ActionType.WRITE_FILE)
    gateway = ToolPermissionGateway(PermissionEngine(), registry)
    executor = SafeToolExecutor(registry, permission_gateway=gateway)

    denied = executor.execute("protected_test_tool", _permission_granted=True)
    assert not denied.success
    assert calls == []

    allowed = executor.execute(
        "protected_test_tool",
        _permission_granted=False,
        _confirmation_provided=True,
    )
    assert allowed.success
    assert len(calls) == 1
    assert calls[0]["_permission_granted"] is True
    assert calls[0]["_confirmation_provided"] is True


def test_read_only_tool_with_protected_action_metadata_fails_closed() -> None:
    registry, calls = _registry(read_only=True, protected_action=ActionType.DELETE_FILE)
    gateway = ToolPermissionGateway(PermissionEngine(), registry)
    executor = SafeToolExecutor(registry, permission_gateway=gateway)

    try:
        gateway.check("protected_test_tool")
    except PermissionError:
        pass
    else:
        raise AssertionError("conflicting metadata was treated as a read-only action")

    result = executor.execute("protected_test_tool")
    assert not result.success
    assert "conflicting read-only/protected-action metadata" in (result.error or "")
    assert calls == []
