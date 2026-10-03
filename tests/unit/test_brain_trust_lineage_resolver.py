from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)
from core.brain.verification import BrainTrustStatus
from security.audit.brain_trust_lineage_resolver import (
    BrainTrustLineageResolver,
)


def create_brain() -> SpecialistBrain:
    return SpecialistBrain(
        name="Lineage Resolver Brain",
        description="6P-28 lineage resolver test brain.",
        specialization="trust lineage",
        capabilities={
            BrainCapability.VERIFY,
        },
        brain_id="brain-lineage-resolver-001",
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


def test_resolver_reconstructs_a_b_c_chain() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain()

        record_a, record_b, record_c = create_chain(
            storage,
            brain,
        )

        resolver = BrainTrustLineageResolver(
            storage
        )

        result = resolver.resolve(
            brain_id=brain.brain_id,
            current_provenance=record_c["provenance"],
        )

        assert result.brain_id == brain.brain_id

        assert (
            result.current_provenance
            == record_c["provenance"]
        )

        assert result.lineage == (
            record_c["provenance"],
            record_b["provenance"],
            record_a["provenance"],
        )

        assert (
            result.root_provenance
            == record_a["provenance"]
        )

        assert result.depth == 3


def test_root_evidence_has_depth_one() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain()

        record_a, _, _ = create_chain(
            storage,
            brain,
        )

        resolver = BrainTrustLineageResolver(
            storage
        )

        result = resolver.resolve(
            brain_id=brain.brain_id,
            current_provenance=record_a["provenance"],
        )

        assert result.lineage == (
            record_a["provenance"],
        )

        assert result.root_provenance == (
            record_a["provenance"]
        )

        assert result.depth == 1


def test_middle_evidence_resolves_to_root() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain()

        record_a, record_b, _ = create_chain(
            storage,
            brain,
        )

        resolver = BrainTrustLineageResolver(
            storage
        )

        result = resolver.resolve(
            brain_id=brain.brain_id,
            current_provenance=record_b["provenance"],
        )

        assert result.lineage == (
            record_b["provenance"],
            record_a["provenance"],
        )

        assert (
            result.root_provenance
            == record_a["provenance"]
        )

        assert result.depth == 2


def test_unknown_current_provenance_is_single_node() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        resolver = BrainTrustLineageResolver(
            storage
        )

        result = resolver.resolve(
            brain_id="brain-lineage-resolver-001",
            current_provenance="unknown-proof",
        )

        assert result.lineage == (
            "unknown-proof",
        )

        assert result.root_provenance == (
            "unknown-proof"
        )

        assert result.depth == 1


def test_wrong_brain_cannot_resolve_another_brain_chain() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain()

        _, _, record_c = create_chain(
            storage,
            brain,
        )

        resolver = BrainTrustLineageResolver(
            storage
        )

        result = resolver.resolve(
            brain_id="different-brain",
            current_provenance=record_c["provenance"],
        )

        assert result.lineage == (
            record_c["provenance"],
        )


def test_invalid_current_arguments_are_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        resolver = BrainTrustLineageResolver(
            storage
        )

        try:
            resolver.resolve(
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
            resolver.resolve(
                brain_id="brain",
                current_provenance="   ",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Empty current provenance was accepted."
            )


def run_all_tests() -> None:
    test_resolver_reconstructs_a_b_c_chain()
    test_root_evidence_has_depth_one()
    test_middle_evidence_resolves_to_root()
    test_unknown_current_provenance_is_single_node()
    test_wrong_brain_cannot_resolve_another_brain_chain()
    test_invalid_current_arguments_are_rejected()

    print(
        "SAHIBEX 6P-28 LINEAGE "
        "RESOLVER TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
