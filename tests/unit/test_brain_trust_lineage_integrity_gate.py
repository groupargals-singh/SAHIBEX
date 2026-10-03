from pathlib import Path
from tempfile import TemporaryDirectory
import json

from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)
from core.brain.verification import BrainTrustStatus
from security.audit.brain_trust_lineage_integrity_gate import (
    BrainTrustLineageIntegrityGate,
)
from security.audit.brain_trust_replacement_store import (
    BrainTrustReplacementStore,
)


def create_brain(
    brain_id: str,
) -> SpecialistBrain:
    return SpecialistBrain(
        name="6P-28 Integrity Gate Brain",
        description="Final lineage integrity gate test.",
        specialization="lineage integrity",
        capabilities={
            BrainCapability.VERIFY,
        },
        brain_id=brain_id,
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
            reason="Replacement A to B.",
        )
    )

    record_c = (
        brain.replace_authenticated_trust_record(
            record_b,
            storage_directory=storage,
            new_evidence="Evidence C",
            reason="Replacement B to C.",
        )
    )

    return record_a, record_b, record_c


def test_final_gate_passes() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain(
            "brain-gate-001"
        )

        _, _, record_c = create_chain(
            storage,
            brain,
        )

        gate = BrainTrustLineageIntegrityGate(
            storage
        )

        result = gate.verify(
            brain_id=brain.brain_id,
            current_provenance=(
                record_c["provenance"]
            ),
        )

        assert result.passed is True
        assert result.brain_id == brain.brain_id
        assert (
            result.current_provenance
            == record_c["provenance"]
        )
        assert result.depth == 3


def test_root_and_current_are_correct() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain(
            "brain-gate-root"
        )

        record_a, _, record_c = create_chain(
            storage,
            brain,
        )

        gate = BrainTrustLineageIntegrityGate(
            storage
        )

        result = gate.verify(
            brain_id=brain.brain_id,
            current_provenance=(
                record_c["provenance"]
            ),
        )

        assert result.passed is True
        assert (
            result.root_provenance
            == record_a["provenance"]
        )
        assert result.depth == 3


def test_tampered_persistent_record_fails() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain(
            "brain-gate-tamper"
        )

        _, _, record_c = create_chain(
            storage,
            brain,
        )

        store = BrainTrustReplacementStore(
            storage
        )

        history = store.read_recent()

        assert len(history) == 2

        history[1]["reason"] = (
            "Tampered replacement reason."
        )

        store.file_path.write_text(
            "\n".join(
                json.dumps(
                    item,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                for item in history
            )
            + "\n",
            encoding="utf-8",
        )

        gate = BrainTrustLineageIntegrityGate(
            storage
        )

        result = gate.verify(
            brain_id=brain.brain_id,
            current_provenance=(
                record_c["provenance"]
            ),
        )

        assert result.passed is False
        assert (
            "Persistent lineage verification failed"
            in result.reason
        )


def test_wrong_brain_cannot_pass() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain_a = create_brain(
            "brain-gate-A"
        )

        brain_b = create_brain(
            "brain-gate-B"
        )

        _, _, record_c = create_chain(
            storage,
            brain_a,
        )

        gate = BrainTrustLineageIntegrityGate(
            storage
        )

        result = gate.verify(
            brain_id=brain_b.brain_id,
            current_provenance=(
                record_c["provenance"]
            ),
        )

        assert result.passed is False


def test_unknown_current_provenance_isolated() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain(
            "brain-gate-unknown"
        )

        create_chain(
            storage,
            brain,
        )

        gate = BrainTrustLineageIntegrityGate(
            storage
        )

        result = gate.verify(
            brain_id=brain.brain_id,
            current_provenance="unknown-proof",
        )

        assert result.passed is True
        assert result.depth == 1
        assert (
            result.root_provenance
            == "unknown-proof"
        )


def test_invalid_arguments_are_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        gate = BrainTrustLineageIntegrityGate(
            storage
        )

        try:
            gate.verify(
                brain_id="   ",
                current_provenance="proof",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Empty brain_id was accepted."
            )

        try:
            gate.verify(
                brain_id="brain",
                current_provenance="   ",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Empty current_provenance was accepted."
            )


def run_all_tests() -> None:
    test_final_gate_passes()
    test_root_and_current_are_correct()
    test_tampered_persistent_record_fails()
    test_wrong_brain_cannot_pass()
    test_unknown_current_provenance_isolated()
    test_invalid_arguments_are_rejected()

    print(
        "SAHIBEX 6P-28 FINAL LINEAGE "
        "INTEGRITY GATE: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
