from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)
from core.brain.verification import BrainTrustStatus


def make_brain() -> SpecialistBrain:
    return SpecialistBrain(
        name="Trust Invalidation Brain",
        description="Trust evidence invalidation test brain.",
        specialization="verification",
        capabilities={
            BrainCapability.THINK,
            BrainCapability.VERIFY,
        },
    )


def test_authenticated_record_can_be_invalidated() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Original verified evidence.",
        )

        active_record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        assert active_record["lifecycle"] == "active"

        invalidated_record = (
            brain.invalidate_authenticated_trust_record(
                active_record,
                storage_directory=storage,
                reason="Evidence invalidated after review.",
            )
        )

        assert invalidated_record["brain_id"] == (
            brain.brain_id
        )
        assert invalidated_record["trust_status"] == (
            "verified"
        )
        assert invalidated_record["evidence"] == (
            "Original verified evidence."
        )
        assert invalidated_record["lifecycle"] == (
            "invalidated"
        )
        assert invalidated_record["reason"] == (
            "Evidence invalidated after review."
        )

        assert (
            brain.verify_authenticated_trust_record(
                invalidated_record,
                storage_directory=storage,
            )
            is True
        )


def test_invalidated_record_has_different_provenance() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Original evidence.",
        )

        active_record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        invalidated_record = (
            brain.invalidate_authenticated_trust_record(
                active_record,
                storage_directory=storage,
                reason="Invalidated for security review.",
            )
        )

        assert invalidated_record["provenance"] != (
            active_record["provenance"]
        )


def test_unauthenticated_record_cannot_be_invalidated() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Original evidence.",
        )

        active_record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        tampered = dict(active_record)
        tampered["evidence"] = "Forged evidence."

        try:
            brain.invalidate_authenticated_trust_record(
                tampered,
                storage_directory=storage,
                reason="Should fail.",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Tampered evidence must not be invalidated."
            )


def test_wrong_brain_cannot_invalidate_record() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain_a = make_brain()
        brain_b = make_brain()

        brain_a.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Brain A evidence.",
        )

        record = (
            brain_a.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        try:
            brain_b.invalidate_authenticated_trust_record(
                record,
                storage_directory=storage,
                reason="Unauthorized invalidation.",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "A different brain must not invalidate the record."
            )


def test_invalidation_does_not_change_brain_trust_status() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Verified brain evidence.",
        )

        record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        brain.invalidate_authenticated_trust_record(
            record,
            storage_directory=storage,
            reason="Evidence lifecycle invalidation.",
        )

        assert brain.trust_status == (
            BrainTrustStatus.VERIFIED
        )


def run_all_tests() -> None:
    test_authenticated_record_can_be_invalidated()
    test_invalidated_record_has_different_provenance()
    test_unauthenticated_record_cannot_be_invalidated()
    test_wrong_brain_cannot_invalidate_record()
    test_invalidation_does_not_change_brain_trust_status()

    print(
        "SAHIBEX 6P-26 TRUST EVIDENCE "
        "INVALIDATION INTEGRITY TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
