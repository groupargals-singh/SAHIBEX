from pathlib import Path
from tempfile import TemporaryDirectory

from security.audit.brain_trust_provenance import (
    BrainTrustProvenance,
)


def test_replacement_provenance_round_trip() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        provenance = BrainTrustProvenance(storage)

        proof = provenance.sign_replacement(
            brain_id="brain-001",
            previous_provenance="old-proof",
            replacement_provenance="new-proof",
            reason="Evidence replacement after review.",
        )

        assert (
            provenance.verify_replacement(
                brain_id="brain-001",
                previous_provenance="old-proof",
                replacement_provenance="new-proof",
                reason="Evidence replacement after review.",
                provenance=proof,
            )
            is True
        )


def test_tampered_previous_provenance_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        provenance = BrainTrustProvenance(storage)

        proof = provenance.sign_replacement(
            brain_id="brain-001",
            previous_provenance="old-proof",
            replacement_provenance="new-proof",
            reason="Evidence replacement.",
        )

        assert (
            provenance.verify_replacement(
                brain_id="brain-001",
                previous_provenance="forged-old-proof",
                replacement_provenance="new-proof",
                reason="Evidence replacement.",
                provenance=proof,
            )
            is False
        )


def test_tampered_replacement_provenance_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        provenance = BrainTrustProvenance(storage)

        proof = provenance.sign_replacement(
            brain_id="brain-001",
            previous_provenance="old-proof",
            replacement_provenance="new-proof",
            reason="Evidence replacement.",
        )

        assert (
            provenance.verify_replacement(
                brain_id="brain-001",
                previous_provenance="old-proof",
                replacement_provenance="forged-new-proof",
                reason="Evidence replacement.",
                provenance=proof,
            )
            is False
        )


def test_tampered_reason_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        provenance = BrainTrustProvenance(storage)

        proof = provenance.sign_replacement(
            brain_id="brain-001",
            previous_provenance="old-proof",
            replacement_provenance="new-proof",
            reason="Evidence replacement.",
        )

        assert (
            provenance.verify_replacement(
                brain_id="brain-001",
                previous_provenance="old-proof",
                replacement_provenance="new-proof",
                reason="Forged reason.",
                provenance=proof,
            )
            is False
        )


def test_wrong_brain_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        provenance = BrainTrustProvenance(storage)

        proof = provenance.sign_replacement(
            brain_id="brain-001",
            previous_provenance="old-proof",
            replacement_provenance="new-proof",
            reason="Evidence replacement.",
        )

        assert (
            provenance.verify_replacement(
                brain_id="brain-002",
                previous_provenance="old-proof",
                replacement_provenance="new-proof",
                reason="Evidence replacement.",
                provenance=proof,
            )
            is False
        )


def run_all_tests() -> None:
    test_replacement_provenance_round_trip()
    test_tampered_previous_provenance_is_rejected()
    test_tampered_replacement_provenance_is_rejected()
    test_tampered_reason_is_rejected()
    test_wrong_brain_is_rejected()

    print(
        "SAHIBEX 6P-27 REPLACEMENT "
        "PROVENANCE INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
