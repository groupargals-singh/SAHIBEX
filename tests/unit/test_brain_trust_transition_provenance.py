from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)
from core.brain.verification import BrainTrustStatus


def make_brain() -> SpecialistBrain:
    return SpecialistBrain(
        name="Trust Transition Brain",
        description="Trust transition provenance test brain.",
        specialization="verification",
        capabilities={
            BrainCapability.THINK,
            BrainCapability.VERIFY,
        },
    )


def test_verified_to_suspended_creates_distinct_authenticated_state() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Initial verification evidence.",
        )

        verified_record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        assert (
            brain.verify_authenticated_trust_record(
                verified_record,
                storage_directory=storage,
            )
            is True
        )

        brain.set_trust_status(
            BrainTrustStatus.SUSPENDED,
            evidence="Suspended after verification failure review.",
        )

        suspended_record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        assert suspended_record["brain_id"] == brain.brain_id
        assert suspended_record["trust_status"] == "suspended"
        assert suspended_record["evidence"] == (
            "Suspended after verification failure review."
        )

        assert (
            brain.verify_authenticated_trust_record(
                suspended_record,
                storage_directory=storage,
            )
            is True
        )

        assert suspended_record["provenance"] != (
            verified_record["provenance"]
        )


def test_old_verified_record_does_not_become_suspended_record() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Original verification.",
        )

        verified_record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        brain.set_trust_status(
            BrainTrustStatus.SUSPENDED,
            evidence="Current suspension evidence.",
        )

        tampered = dict(verified_record)
        tampered["trust_status"] = "suspended"
        tampered["evidence"] = (
            "Current suspension evidence."
        )

        assert (
            brain.verify_authenticated_trust_record(
                tampered,
                storage_directory=storage,
            )
            is False
        )


def test_suspended_record_cannot_be_changed_back_to_verified() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain()

        brain.set_trust_status(
            BrainTrustStatus.SUSPENDED,
            evidence="Suspension evidence.",
        )

        suspended_record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        tampered = dict(suspended_record)
        tampered["trust_status"] = "verified"
        tampered["evidence"] = "Forged verification evidence."

        assert (
            brain.verify_authenticated_trust_record(
                tampered,
                storage_directory=storage,
            )
            is False
        )


def test_trust_transition_does_not_change_capabilities() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain()
        original_capabilities = brain.list_capabilities

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Verified evidence.",
        )

        brain.create_authenticated_trust_record(
            storage_directory=storage,
        )

        brain.set_trust_status(
            BrainTrustStatus.SUSPENDED,
            evidence="Suspension evidence.",
        )

        brain.create_authenticated_trust_record(
            storage_directory=storage,
        )

        assert brain.list_capabilities == original_capabilities


def run_all_tests() -> None:
    test_verified_to_suspended_creates_distinct_authenticated_state()
    test_old_verified_record_does_not_become_suspended_record()
    test_suspended_record_cannot_be_changed_back_to_verified()
    test_trust_transition_does_not_change_capabilities()

    print(
        "SAHIBEX 6P-25 TRUST TRANSITION PROVENANCE "
        "INTEGRITY TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
