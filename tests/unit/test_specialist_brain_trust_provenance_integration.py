from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)
from core.brain.verification import BrainTrustStatus


def make_brain(name: str) -> SpecialistBrain:
    return SpecialistBrain(
        name=name,
        description="Trust provenance integration test brain.",
        specialization="verification",
        capabilities={
            BrainCapability.THINK,
            BrainCapability.VERIFY,
        },
    )


def test_authenticated_trust_record_round_trip() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain("Trust Test Brain")

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Verified by controlled integration test.",
        )

        record = brain.create_authenticated_trust_record(
            storage_directory=storage,
        )

        assert record["brain_id"] == brain.brain_id
        assert record["trust_status"] == "verified"
        assert record["evidence"] == (
            "Verified by controlled integration test."
        )
        assert isinstance(record["provenance"], str)
        assert record["provenance"]

        assert brain.verify_authenticated_trust_record(
            record,
            storage_directory=storage,
        ) is True


def test_brain_identity_binding_rejects_other_brain() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain_a = make_brain("Brain A")
        brain_b = make_brain("Brain B")

        brain_a.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Brain A verified evidence.",
        )

        record = brain_a.create_authenticated_trust_record(
            storage_directory=storage,
        )

        assert brain_a.verify_authenticated_trust_record(
            record,
            storage_directory=storage,
        ) is True

        assert brain_b.verify_authenticated_trust_record(
            record,
            storage_directory=storage,
        ) is False


def test_tampered_trust_status_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain("Status Tamper Brain")

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Original verified evidence.",
        )

        record = brain.create_authenticated_trust_record(
            storage_directory=storage,
        )

        tampered = dict(record)
        tampered["trust_status"] = "suspended"

        assert brain.verify_authenticated_trust_record(
            tampered,
            storage_directory=storage,
        ) is False


def test_tampered_evidence_is_rejected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain("Evidence Tamper Brain")

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Original verified evidence.",
        )

        record = brain.create_authenticated_trust_record(
            storage_directory=storage,
        )

        tampered = dict(record)
        tampered["evidence"] = "Forged replacement evidence."

        assert brain.verify_authenticated_trust_record(
            tampered,
            storage_directory=storage,
        ) is False


def test_unverified_brain_cannot_create_authenticated_record() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain("Unverified Brain")

        assert brain.trust_status == BrainTrustStatus.UNVERIFIED

        try:
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "UNVERIFIED brain must not create authenticated trust evidence."
            )


def test_trust_provenance_does_not_grant_authority() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain("Authority Boundary Brain")

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Verified without authority grant.",
        )

        record = brain.create_authenticated_trust_record(
            storage_directory=storage,
        )

        assert brain.verify_authenticated_trust_record(
            record,
            storage_directory=storage,
        ) is True

        public_names = set(dir(brain))

        forbidden = {
            "grant_permission",
            "authorize",
            "execute",
            "change_constitution",
            "override_parent",
        }

        assert not (public_names & forbidden)


def run_all_tests() -> None:
    test_authenticated_trust_record_round_trip()
    test_brain_identity_binding_rejects_other_brain()
    test_tampered_trust_status_is_rejected()
    test_tampered_evidence_is_rejected()
    test_unverified_brain_cannot_create_authenticated_record()
    test_trust_provenance_does_not_grant_authority()

    print(
        "SAHIBEX 6P-25 SPECIALIST BRAIN TRUST PROVENANCE "
        "INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
