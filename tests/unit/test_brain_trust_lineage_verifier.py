from pathlib import Path
from tempfile import TemporaryDirectory
import json

from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)
from core.brain.verification import BrainTrustStatus
from security.audit.brain_trust_lineage_resolver import (
    BrainTrustLineageResolver,
)
from security.audit.brain_trust_lineage_verifier import (
    BrainTrustLineageVerifier,
)
from security.audit.brain_trust_replacement_store import (
    BrainTrustReplacementStore,
)


def create_brain(
    brain_id: str = "brain-persistent-001",
) -> SpecialistBrain:
    return SpecialistBrain(
        name="Persistent Lineage Brain",
        description="6P-28 persistent lineage test brain.",
        specialization="persistent lineage",
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


def test_persistent_chain_verifies() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain()

        _, _, record_c = create_chain(
            storage,
            brain,
        )

        verifier = BrainTrustLineageVerifier(
            storage
        )

        result = verifier.verify(
            brain_id=brain.brain_id
        )

        assert result.verified is True
        assert result.brain_id == brain.brain_id
        assert result.record_count == 2

        resolver = BrainTrustLineageResolver(
            storage
        )

        resolved = resolver.resolve(
            brain_id=brain.brain_id,
            current_provenance=record_c["provenance"],
        )

        assert resolved.depth == 3


def test_empty_history_is_valid() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        verifier = BrainTrustLineageVerifier(
            storage
        )

        result = verifier.verify(
            brain_id="brain-without-history"
        )

        assert result.verified is True
        assert result.record_count == 0


def test_tampered_persistent_proof_fails() -> None:
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

        history[0]["provenance"] = "tampered-proof"

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

        verifier = BrainTrustLineageVerifier(
            storage
        )

        result = verifier.verify(
            brain_id=brain.brain_id
        )

        assert result.verified is False
        assert (
            result.reason
            == "Replacement authentication failed."
        )


def test_tampered_previous_provenance_fails() -> None:
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

        history[1]["previous_provenance"] = (
            "tampered-previous"
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

        verifier = BrainTrustLineageVerifier(
            storage
        )

        result = verifier.verify(
            brain_id=brain.brain_id
        )

        assert result.verified is False


def test_wrong_brain_history_is_not_counted() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain_a = create_brain(
            "brain-persistent-A"
        )

        brain_b = create_brain(
            "brain-persistent-B"
        )

        create_chain(
            storage,
            brain_a,
        )

        create_chain(
            storage,
            brain_b,
        )

        verifier = BrainTrustLineageVerifier(
            storage
        )

        result_a = verifier.verify(
            brain_id=brain_a.brain_id
        )

        result_b = verifier.verify(
            brain_id=brain_b.brain_id
        )

        assert result_a.verified is True
        assert result_b.verified is True

        assert result_a.record_count == 2
        assert result_b.record_count == 2


def test_missing_reason_fails() -> None:
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

        history[1]["reason"] = ""

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

        verifier = BrainTrustLineageVerifier(
            storage
        )

        result = verifier.verify(
            brain_id=brain.brain_id
        )

        assert result.verified is False
        assert (
            result.reason
            == "Missing replacement reason."
        )


def test_invalid_brain_id_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        verifier = BrainTrustLineageVerifier(
            storage
        )

        try:
            verifier.verify(
                brain_id="   "
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Empty brain_id was accepted."
            )


def run_all_tests() -> None:
    test_persistent_chain_verifies()
    test_empty_history_is_valid()
    test_tampered_persistent_proof_fails()
    test_tampered_previous_provenance_fails()
    test_wrong_brain_history_is_not_counted()
    test_missing_reason_fails()
    test_invalid_brain_id_is_rejected()

    print(
        "SAHIBEX 6P-28 PERSISTENT "
        "LINEAGE VERIFICATION TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
