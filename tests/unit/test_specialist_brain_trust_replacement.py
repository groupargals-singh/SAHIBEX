from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)
from core.brain.verification import BrainTrustStatus


def create_brain() -> SpecialistBrain:
    return SpecialistBrain(
        name="Replacement Test Brain",
        description="6P-27 replacement test brain.",
        specialization="trust replacement",
        capabilities={
            BrainCapability.VERIFY,
        },
        brain_id="brain-replacement-001",
    )


def test_authenticated_trust_replacement() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Original verified evidence.",
        )

        old_record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        new_record = (
            brain.replace_authenticated_trust_record(
                old_record,
                storage_directory=storage,
                new_evidence="Updated verified evidence.",
                reason=(
                    "Evidence refreshed after "
                    "verification review."
                ),
            )
        )

        assert old_record["evidence"] == (
            "Original verified evidence."
        )

        assert new_record["evidence"] == (
            "Updated verified evidence."
        )

        assert old_record["provenance"] != (
            new_record["provenance"]
        )

        assert (
            brain.verify_authenticated_trust_record(
                old_record,
                storage_directory=storage,
            )
            is True
        )

        assert (
            brain.verify_authenticated_trust_record(
                new_record,
                storage_directory=storage,
            )
            is True
        )


def test_replacement_history_is_preserved() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Original evidence.",
        )

        old_record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        brain.replace_authenticated_trust_record(
            old_record,
            storage_directory=storage,
            new_evidence="Replacement evidence.",
            reason="Evidence review completed.",
        )

        replacement_file = (
            storage
            / "brain_trust_replacements.jsonl"
        )

        assert replacement_file.exists()

        lines = replacement_file.read_text(
            encoding="utf-8"
        ).splitlines()

        assert len(lines) == 1


def test_wrong_brain_cannot_replace_evidence() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain_a = create_brain()

        brain_a.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Brain A evidence.",
        )

        record_a = (
            brain_a.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        brain_b = SpecialistBrain(
            name="Other Brain",
            description="Different brain.",
            specialization="other",
            capabilities={
                BrainCapability.VERIFY,
            },
            brain_id="brain-replacement-002",
        )

        brain_b.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Brain B evidence.",
        )

        try:
            brain_b.replace_authenticated_trust_record(
                record_a,
                storage_directory=storage,
                new_evidence="Tampered replacement.",
                reason="Should be rejected.",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Different brain replaced another "
                "brain's evidence."
            )


def test_tampered_old_record_cannot_be_replaced() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Original evidence.",
        )

        old_record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        tampered_record = dict(old_record)

        tampered_record["evidence"] = (
            "Tampered original evidence."
        )

        try:
            brain.replace_authenticated_trust_record(
                tampered_record,
                storage_directory=storage,
                new_evidence="New evidence.",
                reason="Should be rejected.",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Tampered old evidence was accepted."
            )


def test_empty_new_evidence_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Original evidence.",
        )

        old_record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        try:
            brain.replace_authenticated_trust_record(
                old_record,
                storage_directory=storage,
                new_evidence="   ",
                reason="Invalid replacement.",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Empty replacement evidence was accepted."
            )


def test_empty_replacement_reason_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Original evidence.",
        )

        old_record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        try:
            brain.replace_authenticated_trust_record(
                old_record,
                storage_directory=storage,
                new_evidence="New evidence.",
                reason="   ",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Empty replacement reason was accepted."
            )


def run_all_tests() -> None:
    test_authenticated_trust_replacement()
    test_replacement_history_is_preserved()
    test_wrong_brain_cannot_replace_evidence()
    test_tampered_old_record_cannot_be_replaced()
    test_empty_new_evidence_is_rejected()
    test_empty_replacement_reason_is_rejected()

    print(
        "SAHIBEX 6P-27 SPECIALIST BRAIN "
        "TRUST REPLACEMENT TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
