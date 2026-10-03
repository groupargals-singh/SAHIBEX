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
        name="Persistent Invalidation Brain",
        description="Invalidation persistence test brain.",
        specialization="verification",
        capabilities={
            BrainCapability.THINK,
            BrainCapability.VERIFY,
        },
    )


def test_invalidated_record_survives_persistence() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Persistent original evidence.",
        )

        active_record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        invalidated_record = (
            brain.invalidate_authenticated_trust_record(
                active_record,
                storage_directory=storage,
                reason="Invalidated after persistence review.",
            )
        )

        store = BrainTrustStore(storage)
        store.append(invalidated_record)

        records = store.read_recent()

        assert len(records) == 1
        loaded = records[0]

        assert loaded["brain_id"] == brain.brain_id
        assert loaded["trust_status"] == "verified"
        assert loaded["evidence"] == (
            "Persistent original evidence."
        )
        assert loaded["lifecycle"] == "invalidated"
        assert loaded["reason"] == (
            "Invalidated after persistence review."
        )

        assert (
            brain.verify_authenticated_trust_record(
                loaded,
                storage_directory=storage,
            )
            is True
        )


def test_persisted_invalidated_record_tampering_fails() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Protected evidence.",
        )

        active_record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        invalidated_record = (
            brain.invalidate_authenticated_trust_record(
                active_record,
                storage_directory=storage,
                reason="Security invalidation.",
            )
        )

        store = BrainTrustStore(storage)
        store.append(invalidated_record)

        loaded = store.read_recent()[0]

        tampered = dict(loaded)
        tampered["lifecycle"] = "active"

        assert (
            brain.verify_authenticated_trust_record(
                tampered,
                storage_directory=storage,
            )
            is False
        )


def test_invalidation_reason_is_not_authority() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = make_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Verified evidence.",
        )

        active_record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        invalidated_record = (
            brain.invalidate_authenticated_trust_record(
                active_record,
                storage_directory=storage,
                reason="Administrative lifecycle invalidation.",
            )
        )

        assert invalidated_record["lifecycle"] == (
            "invalidated"
        )

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
    test_invalidated_record_survives_persistence()
    test_persisted_invalidated_record_tampering_fails()
    test_invalidation_reason_is_not_authority()

    print(
        "SAHIBEX 6P-26 INVALIDATION PERSISTENCE "
        "INTEGRITY TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
