from __future__ import annotations

import pytest

from core.brain.brain_lifecycle import BrainLifecycle, LifecycleState
from core.brain.root_identity import SahibexRootIdentity


def test_startup_health_sleep_wake_shutdown():
    brain = BrainLifecycle()
    assert brain.state is LifecycleState.NEW

    status = brain.startup()
    assert status.state is LifecycleState.RUNNING
    assert status.awake is True

    status = brain.sleep()
    assert status.state is LifecycleState.SLEEPING
    assert status.awake is False
    assert status.health.value == "healthy"

    status = brain.wake()
    assert status.state is LifecycleState.RUNNING
    assert status.awake is True

    status = brain.shutdown()
    assert status.state is LifecycleState.STOPPED


def test_checkpoint_integrity_and_authorized_restore():
    brain = BrainLifecycle()
    brain.startup()
    cp = brain.checkpoint_state({"task": "demo", "n": 7}, checkpoint_id="cp-1")

    with pytest.raises(PermissionError):
        brain.restore_checkpoint(cp)

    assert brain.restore_checkpoint(cp, authorized=True) == {"task": "demo", "n": 7}

    bad = type(cp)(
        checkpoint_id=cp.checkpoint_id,
        sequence=cp.sequence,
        state={"task": "tampered"},
        checksum=cp.checksum,
        brain_version=cp.brain_version,
        identity_fingerprint=cp.identity_fingerprint,
        created_at=cp.created_at,
    )
    with pytest.raises(ValueError):
        brain.restore_checkpoint(bad, authorized=True)


def test_backup_sanitizes_secrets_and_authorized_restore():
    brain = BrainLifecycle()
    brain.startup()
    backup = brain.backup_state(
        {"ok": True, "token": "secret-value", "nested": {"password": "x"}}
    )
    assert "token" not in backup["state"]
    assert "nested" in backup["state"]
    assert "password" not in backup["state"]["nested"]

    with pytest.raises(PermissionError):
        brain.restore_backup(backup)

    assert brain.restore_backup(backup, authorized=True)["ok"] is True


def test_crash_recovery_requires_valid_checkpoint():
    brain = BrainLifecycle()
    brain.startup()
    cp = brain.checkpoint_state({"resume": 42})
    brain.mark_crashed("simulated crash")
    assert brain.state is LifecycleState.CRASHED

    with pytest.raises(PermissionError):
        brain.recover_from_crash(checkpoint=cp)

    restored = brain.recover_from_crash(checkpoint=cp, authorized=True)
    assert restored == {"resume": 42}
    assert brain.state is LifecycleState.RUNNING


def test_identity_and_security_boundaries():
    brain = BrainLifecycle()
    assert brain.verify_integrity() is True
    assert brain.grants_permission() is False
    assert brain.modifies_constitution() is False
    assert brain.overrides_human_authority() is False
    assert brain.executes_protected_actions() is False


def test_invalid_identity_fails_closed():
    identity = SahibexRootIdentity()
    object.__setattr__(identity, "fingerprint", "tampered")
    with pytest.raises(RuntimeError):
        BrainLifecycle(root_identity=identity)
