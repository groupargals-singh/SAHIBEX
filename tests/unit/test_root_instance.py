from __future__ import annotations

from dataclasses import replace

from core.brain.root_identity import SahibexRootIdentity
from core.brain.root_instance import SahibexRootInstanceIdentity
from core.brain.master_brain import MasterBrain


def test_root_instance_identity_exists() -> None:
    identity = SahibexRootInstanceIdentity()

    assert identity.instance_id.startswith(
        "sahibex-instance-"
    )


def test_root_instance_is_bound_to_root_identity() -> None:
    identity = SahibexRootInstanceIdentity()

    assert identity.root_identity.ROOT_ID == "sahibex-root"
    assert identity.root_identity.BRAIN_ID == "sahibex-master-brain"
    assert identity.verify_root_binding() is True


def test_root_instance_integrity_is_valid() -> None:
    identity = SahibexRootInstanceIdentity()

    assert identity.verify_integrity() is True
    assert identity.validate() is True


def test_each_master_instance_gets_unique_instance_id() -> None:
    identity_a = SahibexRootInstanceIdentity()
    identity_b = SahibexRootInstanceIdentity()

    assert identity_a.instance_id != identity_b.instance_id


def test_same_instance_identity_remains_stable() -> None:
    identity = SahibexRootInstanceIdentity()

    original_id = identity.instance_id

    assert identity.instance_id == original_id
    assert identity.instance_id == original_id
    assert identity.validate() is True


def test_root_instance_identity_is_immutable() -> None:
    identity = SahibexRootInstanceIdentity()

    try:
        identity.instance_id = "forged-instance"
    except (AttributeError, TypeError):
        pass
    else:
        raise AssertionError(
            "Root instance identity must be immutable."
        )


def test_root_instance_tampering_is_detectable() -> None:
    identity = SahibexRootInstanceIdentity()

    tampered = replace(identity)

    object.__setattr__(
        tampered,
        "fingerprint",
        "tampered-fingerprint",
    )

    assert tampered.verify_integrity() is False
    assert tampered.validate() is False


def test_root_binding_tampering_is_detectable() -> None:
    identity = SahibexRootInstanceIdentity()

    tampered = replace(identity)

    object.__setattr__(
        tampered,
        "root_binding_fingerprint",
        "tampered-root-binding",
    )

    assert tampered.verify_root_binding() is False
    assert tampered.verify_integrity() is False
    assert tampered.validate() is False


def test_root_identity_tampering_breaks_instance_validation() -> None:
    identity = SahibexRootInstanceIdentity()

    forged_root = SahibexRootIdentity()

    object.__setattr__(
        forged_root,
        "BRAIN_ID",
        "forged-brain",
    )

    try:
        SahibexRootInstanceIdentity(
            root_identity=forged_root,
        )
    except ValueError as exc:
        assert str(exc) == "invalid_root_identity"
    else:
        raise AssertionError(
            "Forged root identity was accepted."
        )


def test_root_instance_does_not_grant_authority() -> None:
    identity = SahibexRootInstanceIdentity()

    assert identity.grants_authority() is False


def test_root_instance_is_not_child_identity() -> None:
    identity = SahibexRootInstanceIdentity()

    assert identity.is_child_identity() is False


def test_root_instance_is_not_execution_identity() -> None:
    identity = SahibexRootInstanceIdentity()

    assert identity.is_execution_identity() is False


def test_master_brain_instances_have_distinct_runtime_identity() -> None:
    brain_a = MasterBrain()
    brain_b = MasterBrain()

    assert (
        brain_a.root_instance_identity.instance_id
        != brain_b.root_instance_identity.instance_id
    )


def test_master_brain_root_instance_is_valid() -> None:
    brain = MasterBrain()

    assert brain.root_instance_identity.validate() is True
    assert (
        brain.root_instance_identity.root_identity.BRAIN_ID
        == "sahibex-master-brain"
    )


if __name__ == "__main__":
    tests = [
        test_root_instance_identity_exists,
        test_root_instance_is_bound_to_root_identity,
        test_root_instance_integrity_is_valid,
        test_each_master_instance_gets_unique_instance_id,
        test_same_instance_identity_remains_stable,
        test_root_instance_identity_is_immutable,
        test_root_instance_tampering_is_detectable,
        test_root_binding_tampering_is_detectable,
        test_root_identity_tampering_breaks_instance_validation,
        test_root_instance_does_not_grant_authority,
        test_root_instance_is_not_child_identity,
        test_root_instance_is_not_execution_identity,
        test_master_brain_instances_have_distinct_runtime_identity,
        test_master_brain_root_instance_is_valid,
    ]

    for test in tests:
        test()

    print(
        "SAHIBEX PHASE 0 #8 ROOT INSTANCE IDENTITY TEST: PASS"
    )
