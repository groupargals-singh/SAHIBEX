from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)
from core.brain.verification import BrainTrustStatus
from security.audit.brain_trust_current_binding_resolver import (
    BrainTrustCurrentBindingResolver,
)


def create_brain(
    brain_id: str,
) -> SpecialistBrain:
    return SpecialistBrain(
        name="6P-29 Currentness Brain",
        description="Current trust evidence integrity test.",
        specialization="trust currentness",
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


def test_latest_evidence_is_current() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain(
            "brain-currentness-001"
        )

        _, _, record_c = create_chain(
            storage,
            brain,
        )

        resolver = BrainTrustCurrentBindingResolver(
            storage
        )

        binding = resolver.resolve_current(
            brain.brain_id
        )

        assert (
            binding.current_provenance
            == record_c["provenance"]
        )

        assert binding.depth == 3
        assert binding.is_root_current is False


def test_stale_root_is_not_current() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain(
            "brain-currentness-root"
        )

        record_a, _, _ = create_chain(
            storage,
            brain,
        )

        resolver = BrainTrustCurrentBindingResolver(
            storage
        )

        current = resolver.resolve_current(
            brain.brain_id
        )

        assert (
            current.current_provenance
            != record_a["provenance"]
        )


def test_stale_middle_evidence_is_not_current() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain(
            "brain-currentness-middle"
        )

        _, record_b, record_c = create_chain(
            storage,
            brain,
        )

        resolver = BrainTrustCurrentBindingResolver(
            storage
        )

        current = resolver.resolve_current(
            brain.brain_id
        )

        assert (
            current.current_provenance
            != record_b["provenance"]
        )

        assert (
            current.current_provenance
            == record_c["provenance"]
        )


def test_cross_brain_currentness_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain_a = create_brain(
            "brain-currentness-A"
        )

        brain_b = create_brain(
            "brain-currentness-B"
        )

        _, _, record_c = create_chain(
            storage,
            brain_a,
        )

        resolver = BrainTrustCurrentBindingResolver(
            storage
        )

        try:
            resolver.resolve(
                brain_id=brain_b.brain_id,
                current_provenance=record_c[
                    "provenance"
                ],
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Cross-brain evidence was accepted."
            )


def test_empty_brain_id_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        resolver = BrainTrustCurrentBindingResolver(
            storage
        )

        try:
            resolver.resolve_current("")
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Empty brain_id was accepted."
            )


def run_all_tests() -> None:
    test_latest_evidence_is_current()
    test_stale_root_is_not_current()
    test_stale_middle_evidence_is_not_current()
    test_cross_brain_currentness_is_rejected()
    test_empty_brain_id_is_rejected()

    print(
        "SAHIBEX 6P-29 CURRENTNESS INTEGRITY TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
