from pathlib import Path
from tempfile import TemporaryDirectory

from security.audit.brain_trust_lifecycle import (
    BrainTrustEvidenceLifecycle,
)
from security.audit.brain_trust_provenance import (
    BrainTrustProvenance,
)


def test_valid_lifecycle_values_are_defined() -> None:
    assert (
        BrainTrustEvidenceLifecycle.ACTIVE.value
        == "active"
    )

    assert (
        BrainTrustEvidenceLifecycle.INVALIDATED.value
        == "invalidated"
    )


def test_active_lifecycle_provenance_verifies() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        provenance = BrainTrustProvenance(storage)

        proof = provenance.sign(
            brain_id="brain-active",
            trust_status="verified",
            evidence="Active evidence.",
            lifecycle="active",
        )

        record = {
            "brain_id": "brain-active",
            "trust_status": "verified",
            "evidence": "Active evidence.",
            "lifecycle": "active",
            "provenance": proof,
        }

        result = provenance.verify(record)

        assert result.verified is True


def test_invalidated_lifecycle_provenance_verifies() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        provenance = BrainTrustProvenance(storage)

        proof = provenance.sign(
            brain_id="brain-invalidated",
            trust_status="verified",
            evidence="Invalidated evidence.",
            lifecycle="invalidated",
        )

        record = {
            "brain_id": "brain-invalidated",
            "trust_status": "verified",
            "evidence": "Invalidated evidence.",
            "lifecycle": "invalidated",
            "provenance": proof,
        }

        result = provenance.verify(record)

        assert result.verified is True


def test_unknown_lifecycle_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        provenance = BrainTrustProvenance(storage)

        proof = provenance.sign(
            brain_id="brain-unknown",
            trust_status="verified",
            evidence="Unknown lifecycle evidence.",
            lifecycle="revoked",
        )

        record = {
            "brain_id": "brain-unknown",
            "trust_status": "verified",
            "evidence": "Unknown lifecycle evidence.",
            "lifecycle": "revoked",
            "provenance": proof,
        }

        result = provenance.verify(record)

        assert result.verified is False


def test_empty_lifecycle_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        provenance = BrainTrustProvenance(storage)

        proof = provenance.sign(
            brain_id="brain-empty",
            trust_status="verified",
            evidence="Empty lifecycle evidence.",
            lifecycle="active",
        )

        record = {
            "brain_id": "brain-empty",
            "trust_status": "verified",
            "evidence": "Empty lifecycle evidence.",
            "lifecycle": "",
            "provenance": proof,
        }

        result = provenance.verify(record)

        assert result.verified is False


def test_lifecycle_tampering_is_detected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        provenance = BrainTrustProvenance(storage)

        proof = provenance.sign(
            brain_id="brain-tamper",
            trust_status="verified",
            evidence="Lifecycle tamper evidence.",
            lifecycle="active",
        )

        record = {
            "brain_id": "brain-tamper",
            "trust_status": "verified",
            "evidence": "Lifecycle tamper evidence.",
            "lifecycle": "active",
            "provenance": proof,
        }

        record["lifecycle"] = "invalidated"

        result = provenance.verify(record)

        assert result.verified is False


def run_all_tests() -> None:
    test_valid_lifecycle_values_are_defined()
    test_active_lifecycle_provenance_verifies()
    test_invalidated_lifecycle_provenance_verifies()
    test_unknown_lifecycle_is_rejected()
    test_empty_lifecycle_is_rejected()
    test_lifecycle_tampering_is_detected()

    print(
        "SAHIBEX 6P-26 LIFECYCLE VALIDATION "
        "BOUNDARY TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
