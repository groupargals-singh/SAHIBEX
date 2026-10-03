from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)
from core.brain.verification import BrainTrustStatus
from security.audit.brain_trust_store import BrainTrustStore


def make_brain() -> SpecialistBrain:
    return SpecialistBrain(
        name="Lifecycle Store Brain",
        description="Lifecycle-aware trust store test brain.",
        specialization="verification",
        capabilities={
            BrainCapability.THINK,
            BrainCapability.VERIFY,
        },
    )


def test_active_lifecycle_record_can_be_stored() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Active evidence.",
        )

        record = brain.create_authenticated_trust_record(
            storage_directory=storage,
        )

        assert record["lifecycle"] == "active"

        store = BrainTrustStore(storage)
        store.append(record)

        records = store.read_recent()

        assert len(records) == 1
        assert records[0]["lifecycle"] == "active"


def test_invalidated_lifecycle_record_can_be_stored() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Evidence to invalidate.",
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
                reason="Lifecycle invalidation.",
            )
        )

        store = BrainTrustStore(storage)
        store.append(invalidated_record)

        records = store.read_recent()

        assert len(records) == 1
        assert records[0]["lifecycle"] == "invalidated"


def test_unknown_lifecycle_cannot_be_stored() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Unknown lifecycle evidence.",
        )

        record = brain.create_authenticated_trust_record(
            storage_directory=storage,
        )

        record["lifecycle"] = "revoked"

        store = BrainTrustStore(storage)

        try:
            store.append(record)
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Unknown lifecycle must not be stored."
            )


def test_legacy_record_without_lifecycle_remains_compatible() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Legacy evidence.",
        )

        record = brain.create_authenticated_trust_record(
            storage_directory=storage,
        )

        legacy_record = dict(record)
        legacy_record.pop("lifecycle")
        
        # Recreate legacy 6P-25 provenance without lifecycle.
        from security.audit.brain_trust_provenance import (
            BrainTrustProvenance,
        )

        provenance = BrainTrustProvenance(storage)

        legacy_record["provenance"] = provenance.sign(
            brain_id=legacy_record["brain_id"],
            trust_status=legacy_record["trust_status"],
            evidence=legacy_record["evidence"],
        )

        store = BrainTrustStore(storage)
        store.append(legacy_record)

        records = store.read_recent()

        assert len(records) == 1
        assert "lifecycle" not in records[0]


def run_all_tests() -> None:
    test_active_lifecycle_record_can_be_stored()
    test_invalidated_lifecycle_record_can_be_stored()
    test_unknown_lifecycle_cannot_be_stored()
    test_legacy_record_without_lifecycle_remains_compatible()

    print(
        "SAHIBEX 6P-26 TRUST STORE "
        "LIFECYCLE INTEGRITY TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
