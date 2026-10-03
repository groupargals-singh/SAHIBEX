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
from security.audit.brain_trust_replacement_store import (
    BrainTrustReplacementStore,
)


def create_brain(
    brain_id: str = "brain-lineage-attack-001",
) -> SpecialistBrain:
    return SpecialistBrain(
        name="Lineage Attack Brain",
        description="6P-28 lineage attack test brain.",
        specialization="lineage security",
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


def test_forged_replacement_proof_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain()

        _, _, record_c = create_chain(
            storage,
            brain,
        )

        store = BrainTrustReplacementStore(
            storage
        )

        history = store.read_recent()

        assert len(history) == 2

        history[-1]["provenance"] = "forged-proof"

        store.file_path.write_text(
            "\n".join(
                __import__("json").dumps(
                    item,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                for item in history
            )
            + "\n",
            encoding="utf-8",
        )

        resolver = BrainTrustLineageResolver(
            storage
        )

        try:
            resolver.resolve(
                brain_id=brain.brain_id,
                current_provenance=record_c["provenance"],
            )
        except ValueError as exc:
            assert (
                "Unauthenticated replacement"
                in str(exc)
            )
        else:
            raise AssertionError(
                "Forged replacement proof was accepted."
            )


def test_missing_previous_provenance_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain()

        _, _, record_c = create_chain(
            storage,
            brain,
        )

        store = BrainTrustReplacementStore(
            storage
        )

        history = store.read_recent()

        assert len(history) == 2

        history[-1]["previous_provenance"] = ""

        store.file_path.write_text(
            "\n".join(
                __import__("json").dumps(
                    item,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                for item in history
            )
            + "\n",
            encoding="utf-8",
        )

        resolver = BrainTrustLineageResolver(
            storage
        )

        try:
            resolver.resolve(
                brain_id=brain.brain_id,
                current_provenance=record_c["provenance"],
            )
        except ValueError as exc:
            assert (
                "previous provenance is missing"
                in str(exc)
            )
        else:
            raise AssertionError(
                "Missing predecessor was accepted."
            )


def test_modified_previous_provenance_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain()

        _, _, record_c = create_chain(
            storage,
            brain,
        )

        store = BrainTrustReplacementStore(
            storage
        )

        history = store.read_recent()

        assert len(history) == 2

        history[-1]["previous_provenance"] = (
            "forged-previous"
        )

        store.file_path.write_text(
            "\n".join(
                __import__("json").dumps(
                    item,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                for item in history
            )
            + "\n",
            encoding="utf-8",
        )

        resolver = BrainTrustLineageResolver(
            storage
        )

        try:
            resolver.resolve(
                brain_id=brain.brain_id,
                current_provenance=record_c["provenance"],
            )
        except ValueError as exc:
            assert (
                "Unauthenticated replacement"
                in str(exc)
            )
        else:
            raise AssertionError(
                "Modified predecessor was accepted."
            )


def test_duplicate_replacement_target_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain()

        _, _, record_c = create_chain(
            storage,
            brain,
        )

        store = BrainTrustReplacementStore(
            storage
        )

        history = store.read_recent()

        assert len(history) == 2

        duplicate = dict(history[0])

        duplicate["replacement_provenance"] = (
            history[1]["replacement_provenance"]
        )

        history.append(duplicate)

        store.file_path.write_text(
            "\n".join(
                __import__("json").dumps(
                    item,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                for item in history
            )
            + "\n",
            encoding="utf-8",
        )

        resolver = BrainTrustLineageResolver(
            storage
        )

        try:
            resolver.resolve(
                brain_id=brain.brain_id,
                current_provenance=record_c["provenance"],
            )
        except ValueError as exc:
            assert (
                "Ambiguous lineage"
                in str(exc)
            )
        else:
            raise AssertionError(
                "Duplicate replacement target was accepted."
            )


def test_cyclic_lineage_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain()

        record_a, record_b, record_c = create_chain(
            storage,
            brain,
        )

        store = BrainTrustReplacementStore(
            storage
        )

        history = store.read_recent()

        assert len(history) == 2

        # Create a cycle at the storage layer.
        # The proof is intentionally not valid after this
        # mutation, so the resolver must reject it.
        history[0]["previous_provenance"] = (
            record_c["provenance"]
        )

        store.file_path.write_text(
            "\n".join(
                __import__("json").dumps(
                    item,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                for item in history
            )
            + "\n",
            encoding="utf-8",
        )

        resolver = BrainTrustLineageResolver(
            storage
        )

        try:
            resolver.resolve(
                brain_id=brain.brain_id,
                current_provenance=record_c["provenance"],
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Cyclic or forged lineage was accepted."
            )


def test_other_brain_history_is_not_followed() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain_a = create_brain(
            "brain-lineage-attack-A"
        )

        brain_b = create_brain(
            "brain-lineage-attack-B"
        )

        _, _, record_a_c = create_chain(
            storage,
            brain_a,
        )

        _, _, record_b_c = create_chain(
            storage,
            brain_b,
        )

        resolver = BrainTrustLineageResolver(
            storage
        )

        result = resolver.resolve(
            brain_id=brain_a.brain_id,
            current_provenance=record_b_c["provenance"],
        )

        assert result.lineage == (
            record_b_c["provenance"],
        )

        result_a = resolver.resolve(
            brain_id=brain_a.brain_id,
            current_provenance=record_a_c["provenance"],
        )

        assert len(result_a.lineage) == 3


def test_missing_reason_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain()

        _, _, record_c = create_chain(
            storage,
            brain,
        )

        store = BrainTrustReplacementStore(
            storage
        )

        history = store.read_recent()

        assert len(history) == 2

        history[-1]["reason"] = ""

        store.file_path.write_text(
            "\n".join(
                __import__("json").dumps(
                    item,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                for item in history
            )
            + "\n",
            encoding="utf-8",
        )

        resolver = BrainTrustLineageResolver(
            storage
        )

        try:
            resolver.resolve(
                brain_id=brain.brain_id,
                current_provenance=record_c["provenance"],
            )
        except ValueError as exc:
            assert (
                "reason is missing"
                in str(exc)
            )
        else:
            raise AssertionError(
                "Missing replacement reason was accepted."
            )


def run_all_tests() -> None:
    test_forged_replacement_proof_is_rejected()
    test_missing_previous_provenance_is_rejected()
    test_modified_previous_provenance_is_rejected()
    test_duplicate_replacement_target_is_rejected()
    test_cyclic_lineage_is_rejected()
    test_other_brain_history_is_not_followed()
    test_missing_reason_is_rejected()

    print(
        "SAHIBEX 6P-28 LINEAGE "
        "ATTACK DETECTION TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
