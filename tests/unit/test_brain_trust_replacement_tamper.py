from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)
from core.brain.verification import BrainTrustStatus
from security.audit.brain_trust_provenance import (
    BrainTrustProvenance,
)
from security.audit.brain_trust_replacement_store import (
    BrainTrustReplacementStore,
)


def create_brain() -> SpecialistBrain:
    return SpecialistBrain(
        name="Tamper Test Brain",
        description="6P-27 tamper and lineage test brain.",
        specialization="trust lineage security",
        capabilities={
            BrainCapability.VERIFY,
        },
        brain_id="brain-tamper-001",
    )


def create_chain(
    storage: Path,
    brain: SpecialistBrain,
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    brain.set_trust_status(
        BrainTrustStatus.VERIFIED,
        evidence="Evidence A",
    )

    record_a = (
        brain.create_authenticated_trust_record(
            storage_directory=storage,
        )
    )

    record_b = (
        brain.replace_authenticated_trust_record(
            record_a,
            storage_directory=storage,
            new_evidence="Evidence B",
            reason="First replacement.",
        )
    )

    record_c = (
        brain.replace_authenticated_trust_record(
            record_b,
            storage_directory=storage,
            new_evidence="Evidence C",
            reason="Second replacement.",
        )
    )

    return record_a, record_b, record_c


def test_tampered_record_a_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain()

        record_a, _, _ = create_chain(
            storage,
            brain,
        )

        tampered = dict(record_a)
        tampered["evidence"] = "Tampered Evidence A"

        assert (
            brain.verify_authenticated_trust_record(
                tampered,
                storage_directory=storage,
            )
            is False
        )


def test_tampered_record_b_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain()

        _, record_b, _ = create_chain(
            storage,
            brain,
        )

        tampered = dict(record_b)
        tampered["evidence"] = "Tampered Evidence B"

        assert (
            brain.verify_authenticated_trust_record(
                tampered,
                storage_directory=storage,
            )
            is False
        )


def test_tampered_record_c_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain()

        _, _, record_c = create_chain(
            storage,
            brain,
        )

        tampered = dict(record_c)
        tampered["trust_status"] = "suspended"

        assert (
            brain.verify_authenticated_trust_record(
                tampered,
                storage_directory=storage,
            )
            is False
        )


def test_tampered_replacement_previous_provenance_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain()

        create_chain(
            storage,
            brain,
        )

        store = BrainTrustReplacementStore(
            storage
        )

        history = store.read_recent()

        assert len(history) == 2

        replacement = history[0]

        provenance = BrainTrustProvenance(
            storage
        )

        assert (
            provenance.verify_replacement(
                brain_id=replacement["brain_id"],
                previous_provenance="forged-previous",
                replacement_provenance=(
                    replacement["replacement_provenance"]
                ),
                reason=replacement["reason"],
                provenance=replacement["provenance"],
            )
            is False
        )


def test_tampered_replacement_proof_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain()

        create_chain(
            storage,
            brain,
        )

        store = BrainTrustReplacementStore(
            storage
        )

        history = store.read_recent()

        assert len(history) == 2

        replacement = history[0]

        provenance = BrainTrustProvenance(
            storage
        )

        assert (
            provenance.verify_replacement(
                brain_id=replacement["brain_id"],
                previous_provenance=(
                    replacement["previous_provenance"]
                ),
                replacement_provenance=(
                    replacement["replacement_provenance"]
                ),
                reason=replacement["reason"],
                provenance="forged-proof",
            )
            is False
        )


def test_direct_a_to_c_lineage_is_not_present() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain()

        record_a, _, record_c = create_chain(
            storage,
            brain,
        )

        store = BrainTrustReplacementStore(
            storage
        )

        history = store.read_recent()

        assert len(history) == 2

        assert not any(
            replacement["previous_provenance"]
            == record_a["provenance"]
            and replacement["replacement_provenance"]
            == record_c["provenance"]
            for replacement in history
        )


def test_valid_chain_remains_intact_after_tamper_attempts() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain()

        record_a, record_b, record_c = create_chain(
            storage,
            brain,
        )

        tampered_a = dict(record_a)
        tampered_a["evidence"] = "Forged A"

        tampered_b = dict(record_b)
        tampered_b["evidence"] = "Forged B"

        tampered_c = dict(record_c)
        tampered_c["evidence"] = "Forged C"

        assert (
            brain.verify_authenticated_trust_record(
                tampered_a,
                storage_directory=storage,
            )
            is False
        )

        assert (
            brain.verify_authenticated_trust_record(
                tampered_b,
                storage_directory=storage,
            )
            is False
        )

        assert (
            brain.verify_authenticated_trust_record(
                tampered_c,
                storage_directory=storage,
            )
            is False
        )

        assert (
            brain.verify_authenticated_trust_record(
                record_a,
                storage_directory=storage,
            )
            is True
        )

        assert (
            brain.verify_authenticated_trust_record(
                record_b,
                storage_directory=storage,
            )
            is True
        )

        assert (
            brain.verify_authenticated_trust_record(
                record_c,
                storage_directory=storage,
            )
            is True
        )


def run_all_tests() -> None:
    test_tampered_record_a_is_rejected()
    test_tampered_record_b_is_rejected()
    test_tampered_record_c_is_rejected()
    test_tampered_replacement_previous_provenance_is_rejected()
    test_tampered_replacement_proof_is_rejected()
    test_direct_a_to_c_lineage_is_not_present()
    test_valid_chain_remains_intact_after_tamper_attempts()

    print(
        "SAHIBEX 6P-27 REPLACEMENT "
        "TAMPER & LINEAGE INTEGRITY TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
