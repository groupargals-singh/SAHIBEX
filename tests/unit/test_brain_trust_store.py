from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)
from core.brain.verification import BrainTrustStatus
from security.audit.brain_trust_store import BrainTrustStore


def make_brain() -> SpecialistBrain:
    return SpecialistBrain(
        name="Persistent Trust Brain",
        description="Persistence integrity test brain.",
        specialization="verification",
        capabilities={
            BrainCapability.THINK,
            BrainCapability.VERIFY,
        },
    )


def test_authenticated_trust_record_survives_readback() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Persistent verification evidence.",
        )

        record = brain.create_authenticated_trust_record(
            storage_directory=storage,
        )

        store = BrainTrustStore(storage)
        store.append(record)

        records = store.read_recent()

        assert len(records) == 1
        assert records[0] == record

        assert (
            brain.verify_authenticated_trust_record(
                records[0],
                storage_directory=storage,
            )
            is True
        )


def test_multiple_trust_states_are_preserved() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain()
        store = BrainTrustStore(storage)

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Verified state evidence.",
        )

        verified_record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        store.append(verified_record)

        brain.set_trust_status(
            BrainTrustStatus.SUSPENDED,
            evidence="Suspended state evidence.",
        )

        suspended_record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        store.append(suspended_record)

        records = store.read_recent()

        assert len(records) == 2

        assert records[0]["trust_status"] == "verified"
        assert records[1]["trust_status"] == "suspended"

        assert (
            brain.verify_authenticated_trust_record(
                records[0],
                storage_directory=storage,
            )
            is True
        )

        assert (
            brain.verify_authenticated_trust_record(
                records[1],
                storage_directory=storage,
            )
            is True
        )


def test_persisted_tampering_is_detected() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Original persistent evidence.",
        )

        record = brain.create_authenticated_trust_record(
            storage_directory=storage,
        )

        store = BrainTrustStore(storage)
        store.append(record)

        records = store.read_recent()

        tampered = dict(records[0])
        tampered["evidence"] = "Forged persistent evidence."

        assert (
            brain.verify_authenticated_trust_record(
                tampered,
                storage_directory=storage,
            )
            is False
        )


def test_store_does_not_expose_authority_controls() -> None:
    with TemporaryDirectory() as temp_dir:
        store = BrainTrustStore(Path(temp_dir))

        public_names = set(dir(store))

        forbidden = {
            "grant_permission",
            "authorize",
            "execute",
            "change_constitution",
            "override_parent",
        }

        assert not (public_names & forbidden)


def run_all_tests() -> None:
    test_authenticated_trust_record_survives_readback()
    test_multiple_trust_states_are_preserved()
    test_persisted_tampering_is_detected()
    test_store_does_not_expose_authority_controls()

    print(
        "SAHIBEX 6P-25 TRUST STORE PERSISTENCE "
        "INTEGRITY TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
