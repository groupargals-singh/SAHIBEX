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
        name="Replacement Chain Brain",
        description="6P-27 replacement chain test brain.",
        specialization="trust lineage",
        capabilities={
            BrainCapability.VERIFY,
        },
        brain_id="brain-chain-001",
    )


def test_three_stage_replacement_chain() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain()

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
                reason="First evidence review.",
            )
        )

        record_c = (
            brain.replace_authenticated_trust_record(
                record_b,
                storage_directory=storage,
                new_evidence="Evidence C",
                reason="Second evidence review.",
            )
        )

        assert record_a["evidence"] == "Evidence A"
        assert record_b["evidence"] == "Evidence B"
        assert record_c["evidence"] == "Evidence C"

        assert (
            record_a["provenance"]
            != record_b["provenance"]
        )

        assert (
            record_b["provenance"]
            != record_c["provenance"]
        )

        assert (
            record_a["provenance"]
            != record_c["provenance"]
        )


def test_all_chain_records_remain_authenticated() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain()

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


def test_replacement_history_contains_two_links() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain()

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

        brain.replace_authenticated_trust_record(
            record_b,
            storage_directory=storage,
            new_evidence="Evidence C",
            reason="Second replacement.",
        )

        store = BrainTrustReplacementStore(
            storage
        )

        history = store.read_recent()

        assert len(history) == 2

        assert (
            history[0]["previous_provenance"]
            == record_a["provenance"]
        )

        assert (
            history[0]["replacement_provenance"]
            == record_b["provenance"]
        )

        assert (
            history[1]["previous_provenance"]
            == record_b["provenance"]
        )

        assert (
            history[1]["replacement_provenance"]
            == record_c_provenance(
                storage=storage,
                brain_id=brain.brain_id,
            )
        )


def record_c_provenance(
    *,
    storage: Path,
    brain_id: str,
) -> str:
    store = BrainTrustReplacementStore(
        storage
    )

    history = store.read_recent()

    if not history:
        raise AssertionError(
            "Replacement history is empty."
        )

    last = history[-1]

    assert last["brain_id"] == brain_id

    return last["replacement_provenance"]


def test_replacement_proofs_are_authenticated() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain()

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

        brain.replace_authenticated_trust_record(
            record_b,
            storage_directory=storage,
            new_evidence="Evidence C",
            reason="Second replacement.",
        )

        store = BrainTrustReplacementStore(
            storage
        )

        history = store.read_recent()

        provenance = BrainTrustProvenance(
            storage
        )

        for replacement in history:
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
                    provenance=replacement["provenance"],
                )
                is True
            )


def run_all_tests() -> None:
    test_three_stage_replacement_chain()
    test_all_chain_records_remain_authenticated()
    test_replacement_history_contains_two_links()
    test_replacement_proofs_are_authenticated()

    print(
        "SAHIBEX 6P-27 REPLACEMENT CHAIN "
        "INTEGRITY TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
