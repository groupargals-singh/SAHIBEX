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
        name="6P-29 Binding Resolver Brain",
        description="Current trust binding resolver test.",
        specialization="trust binding",
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


def test_current_binding_resolves() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain(
            "brain-binding-001"
        )

        record_a, _, record_c = create_chain(
            storage,
            brain,
        )

        resolver = (
            BrainTrustCurrentBindingResolver(
                storage
            )
        )

        binding = resolver.resolve(
            brain_id=brain.brain_id,
            current_provenance=(
                record_c["provenance"]
            ),
        )

        assert (
            binding.brain_id
            == brain.brain_id
        )

        assert (
            binding.current_provenance
            == record_c["provenance"]
        )

        assert (
            binding.root_provenance
            == record_a["provenance"]
        )

        assert binding.depth == 3
        assert binding.is_root_current is False


def test_root_binding_resolves() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain(
            "brain-binding-root"
        )

        record_a, _, _ = create_chain(
            storage,
            brain,
        )

        resolver = (
            BrainTrustCurrentBindingResolver(
                storage
            )
        )

        binding = resolver.resolve(
            brain_id=brain.brain_id,
            current_provenance=(
                record_a["provenance"]
            ),
        )

        assert (
            binding.current_provenance
            == record_a["provenance"]
        )

        assert (
            binding.root_provenance
            == record_a["provenance"]
        )

        assert binding.depth == 1
        assert binding.is_root_current is True


def test_wrong_brain_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain_a = create_brain(
            "brain-binding-A"
        )

        brain_b = create_brain(
            "brain-binding-B"
        )

        _, _, record_c = create_chain(
            storage,
            brain_a,
        )

        resolver = (
            BrainTrustCurrentBindingResolver(
                storage
            )
        )

        try:
            resolver.resolve(
                brain_id=brain_b.brain_id,
                current_provenance=(
                    record_c["provenance"]
                ),
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Cross-brain binding was accepted."
            )


def test_tampered_current_proof_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain(
            "brain-binding-tamper"
        )

        create_chain(
            storage,
            brain,
        )

        resolver = (
            BrainTrustCurrentBindingResolver(
                storage
            )
        )

        try:
            resolver.resolve(
                brain_id=brain.brain_id,
                current_provenance="tampered-proof",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Tampered current proof was accepted."
            )


def test_invalid_arguments_are_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        resolver = (
            BrainTrustCurrentBindingResolver(
                storage
            )
        )

        try:
            resolver.resolve(
                brain_id="",
                current_provenance="proof",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Empty brain_id was accepted."
            )

        try:
            resolver.resolve(
                brain_id="brain",
                current_provenance="",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Empty current provenance was accepted."
            )


def run_all_tests() -> None:
    test_current_binding_resolves()
    test_root_binding_resolves()
    test_wrong_brain_is_rejected()
    test_tampered_current_proof_is_rejected()
    test_invalid_arguments_are_rejected()

    print(
        "SAHIBEX 6P-29 CURRENT TRUST "
        "BINDING RESOLVER TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
