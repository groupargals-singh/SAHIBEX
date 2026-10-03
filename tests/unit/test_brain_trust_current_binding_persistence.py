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
from security.audit.brain_trust_replacement_store import (
    BrainTrustReplacementStore,
)


def create_brain(
    brain_id: str,
) -> SpecialistBrain:
    return SpecialistBrain(
        name="6P-29 Persistence Brain",
        description="Persistent current binding test.",
        specialization="current binding persistence",
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


def test_current_binding_survives_new_resolver() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain(
            "brain-persistence-001"
        )

        _, _, record_c = create_chain(
            storage,
            brain,
        )

        resolver_one = BrainTrustCurrentBindingResolver(
            storage
        )

        binding_one = resolver_one.resolve_current(
            brain.brain_id
        )

        resolver_two = BrainTrustCurrentBindingResolver(
            storage
        )

        binding_two = resolver_two.resolve_current(
            brain.brain_id
        )

        assert (
            binding_one.current_provenance
            == record_c["provenance"]
        )

        assert (
            binding_two.current_provenance
            == record_c["provenance"]
        )

        assert (
            binding_one.current_provenance
            == binding_two.current_provenance
        )

        assert binding_one.root_provenance == (
            binding_two.root_provenance
        )

        assert binding_one.depth == binding_two.depth


def test_tampered_replacement_history_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain(
            "brain-persistence-tamper"
        )

        create_chain(
            storage,
            brain,
        )

        replacement_store = BrainTrustReplacementStore(
            storage
        )

        records = replacement_store.read_recent(
            limit=1000000
        )

        assert records

        records[0]["replacement_provenance"] = (
            "tampered-current-provenance"
        )

        replacement_file = (
            storage
            / BrainTrustReplacementStore.FILE_NAME
        )

        replacement_file.write_text(
            "\n".join(
                __import__("json").dumps(record)
                for record in records
            )
            + "\n",
            encoding="utf-8",
        )

        resolver = BrainTrustCurrentBindingResolver(
            storage
        )

        try:
            resolver.resolve_current(
                brain.brain_id
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Tampered replacement history was accepted."
            )


def test_cross_brain_history_does_not_become_current() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain_a = create_brain(
            "brain-persistence-A"
        )

        brain_b = create_brain(
            "brain-persistence-B"
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
                "Cross-brain persistent evidence was accepted."
            )


def test_missing_history_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        resolver = BrainTrustCurrentBindingResolver(
            storage
        )

        try:
            resolver.resolve_current(
                "brain-with-no-history"
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Missing trust history was accepted."
            )


def run_all_tests() -> None:
    test_current_binding_survives_new_resolver()
    test_tampered_replacement_history_is_rejected()
    test_cross_brain_history_does_not_become_current()
    test_missing_history_is_rejected()

    print(
        "SAHIBEX 6P-29 PERSISTENT CURRENT BINDING "
        "INTEGRITY TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
