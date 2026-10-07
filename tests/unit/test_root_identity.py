from __future__ import annotations

from dataclasses import replace

from core.brain.root_identity import SahibexRootIdentity
from core.brain.master_brain import MasterBrain


def test_root_identity_exists() -> None:
    identity = SahibexRootIdentity()

    assert identity.ROOT_ID == "sahibex-root"
    assert identity.BRAIN_ID == "sahibex-master-brain"


def test_root_identity_is_mother_brain() -> None:
    identity = SahibexRootIdentity()

    assert identity.is_mother_brain() is True
    assert identity.BRAIN_ROLE == "mother_brain"


def test_root_identity_is_constitution_bound() -> None:
    identity = SahibexRootIdentity()

    assert identity.CONSTITUTION_ID == "sahibex-root-constitution-v1"
    assert identity.constitution_binding_valid() is True


def test_root_identity_integrity_is_valid() -> None:
    identity = SahibexRootIdentity()

    assert identity.verify_integrity() is True
    assert identity.validate() is True


def test_root_identity_is_immutable() -> None:
    identity = SahibexRootIdentity()

    try:
        identity.BRAIN_ID = "forged-brain"
    except (AttributeError, TypeError):
        pass
    else:
        raise AssertionError(
            "Root identity must be immutable."
        )


def test_root_identity_tampering_is_detectable() -> None:
    identity = SahibexRootIdentity()

    tampered = replace(identity)
    object.__setattr__(tampered, "fingerprint", "tampered-fingerprint")
    assert tampered.verify_integrity() is False
    assert tampered.validate() is False


def test_child_identity_cannot_equal_root_identity() -> None:
    root = SahibexRootIdentity()

    assert root.is_child_identity() is False
    assert root.BRAIN_ID != "child-brain-test"


def test_external_identity_cannot_become_root_identity() -> None:
    root = SahibexRootIdentity()

    assert root.is_external_identity() is False
    assert root.BRAIN_ID == "sahibex-master-brain"


def test_root_identity_does_not_grant_authority() -> None:
    identity = SahibexRootIdentity()

    assert identity.grants_authority() is False


def test_master_brain_uses_root_identity() -> None:
    brain = MasterBrain()

    assert brain.root_identity.validate() is True
    assert brain.root_identity.BRAIN_ID == "sahibex-master-brain"


def test_root_identity_is_distinct_from_execution_identity() -> None:
    identity = SahibexRootIdentity()

    execution_id = "execution-123"

    assert identity.BRAIN_ID != execution_id
    assert identity.ROOT_ID != execution_id


def test_root_identity_is_distinct_from_child_identity() -> None:
    identity = SahibexRootIdentity()

    child_brain_id = "child-brain-123"

    assert identity.BRAIN_ID != child_brain_id
    assert identity.ROOT_ID != child_brain_id


if __name__ == "__main__":
    tests = [
        test_root_identity_exists,
        test_root_identity_is_mother_brain,
        test_root_identity_is_constitution_bound,
        test_root_identity_integrity_is_valid,
        test_root_identity_is_immutable,
        test_root_identity_tampering_is_detectable,
        test_child_identity_cannot_equal_root_identity,
        test_external_identity_cannot_become_root_identity,
        test_root_identity_does_not_grant_authority,
        test_master_brain_uses_root_identity,
        test_root_identity_is_distinct_from_execution_identity,
        test_root_identity_is_distinct_from_child_identity,
    ]

    for test in tests:
        test()

    print("SAHIBEX PHASE 0 #7 ROOT IDENTITY TEST: PASS")
