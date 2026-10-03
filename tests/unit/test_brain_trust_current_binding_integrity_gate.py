from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)
from core.brain.verification import BrainTrustStatus
from security.audit.brain_trust_current_binding_integrity_gate import (
    BrainTrustCurrentBindingIntegrityGate,
)


def create_brain(
    brain_id: str,
) -> SpecialistBrain:
    return SpecialistBrain(
        name="6P-29 Final Gate Brain",
        description="Final current binding integrity test.",
        specialization="current binding integrity",
        capabilities={
            BrainCapability.VERIFY,
        },
        brain_id=brain_id,
    )


def create_chain(
    storage: Path,
    brain: SpecialistBrain,
) -> tuple[
    dict[str, str],
    dict[str, str],
    dict[str, str],
]:
    brain.set_trust_status(
        BrainTrustStatus.VERIFIED,
        evidence="Evidence A",
    )

    record_a = brain.create_authenticated_trust_record(
        storage_directory=storage,
    )

    record_b = brain.replace_authenticated_trust_record(
        record_a,
        storage_directory=storage,
        new_evidence="Evidence B",
        reason="Replacement A to B.",
    )

    record_c = brain.replace_authenticated_trust_record(
        record_b,
        storage_directory=storage,
        new_evidence="Evidence C",
        reason="Replacement B to C.",
    )

    return record_a, record_b, record_c


def test_final_gate_accepts_authenticated_current() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain(
            "brain-final-gate-001"
        )

        _, _, record_c = create_chain(
            storage,
            brain,
        )

        gate = BrainTrustCurrentBindingIntegrityGate(
            storage
        )

        binding = gate.verify(
            brain.brain_id
        )

        assert (
            binding.brain_id
            == brain.brain_id
        )

        assert (
            binding.current_provenance
            == record_c["provenance"]
        )

        assert binding.depth == 3
        assert binding.is_root_current is False


def test_final_gate_rejects_empty_brain() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        gate = BrainTrustCurrentBindingIntegrityGate(
            storage
        )

        try:
            gate.verify("")
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Empty brain_id was accepted."
            )


def test_final_gate_rejects_unknown_brain() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain(
            "brain-final-gate-known"
        )

        create_chain(
            storage,
            brain,
        )

        gate = BrainTrustCurrentBindingIntegrityGate(
            storage
        )

        try:
            gate.verify(
                "brain-final-gate-unknown"
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Unknown brain was accepted."
            )


def test_final_gate_preserves_root_integrity() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain(
            "brain-final-gate-root"
        )

        record_a, _, _ = create_chain(
            storage,
            brain,
        )

        gate = BrainTrustCurrentBindingIntegrityGate(
            storage
        )

        binding = gate.resolver.resolve(
            brain_id=brain.brain_id,
            current_provenance=record_a[
                "provenance"
            ],
        )

        assert (
            binding.current_provenance
            == record_a["provenance"]
        )

        assert binding.is_root_current is True


def run_all_tests() -> None:
    test_final_gate_accepts_authenticated_current()
    test_final_gate_rejects_empty_brain()
    test_final_gate_rejects_unknown_brain()
    test_final_gate_preserves_root_integrity()

    print(
        "SAHIBEX 6P-29 FINAL CURRENT BINDING "
        "INTEGRITY GATE TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
