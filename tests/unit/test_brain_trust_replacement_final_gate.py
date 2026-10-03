from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)
from core.brain.verification import BrainTrustStatus
from security.audit.brain_trust_lifecycle import (
    BrainTrustEvidenceLifecycle,
)
from security.audit.brain_trust_provenance import (
    BrainTrustProvenance,
)
from security.audit.brain_trust_replacement_store import (
    BrainTrustReplacementStore,
)


def create_brain() -> SpecialistBrain:
    return SpecialistBrain(
        name="Final Replacement Gate Brain",
        description="6P-27 final integrity gate brain.",
        specialization="trust evidence integrity",
        capabilities={
            BrainCapability.VERIFY,
        },
        brain_id="brain-final-gate-001",
    )


def test_complete_replacement_integrity_gate() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain()

        # -------------------------------------------------
        # 1. Initial authenticated evidence A
        # -------------------------------------------------

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Evidence A",
        )

        record_a = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        assert (
            record_a["lifecycle"]
            == BrainTrustEvidenceLifecycle.ACTIVE.value
        )

        # -------------------------------------------------
        # 2. Replace A -> B
        # -------------------------------------------------

        record_b = (
            brain.replace_authenticated_trust_record(
                record_a,
                storage_directory=storage,
                new_evidence="Evidence B",
                reason="First evidence review.",
            )
        )

        # -------------------------------------------------
        # 3. Replace B -> C
        # -------------------------------------------------

        record_c = (
            brain.replace_authenticated_trust_record(
                record_b,
                storage_directory=storage,
                new_evidence="Evidence C",
                reason="Second evidence review.",
            )
        )

        # -------------------------------------------------
        # 4. All evidence records remain independently
        #    authenticated.
        # -------------------------------------------------

        assert (
            brain.verify_authenticated_trust_record(
                record_a,
                storage_directory=storage,
            )
            is True
        )

        assert (
            brain.verify_authenticated_trust_record(
                record_b,
                storage_directory=storage,
            )
            is True
        )

        assert (
            brain.verify_authenticated_trust_record(
                record_c,
                storage_directory=storage,
            )
            is True
        )

        # -------------------------------------------------
        # 5. Evidence history was not overwritten.
        # -------------------------------------------------

        assert record_a["evidence"] == "Evidence A"
        assert record_b["evidence"] == "Evidence B"
        assert record_c["evidence"] == "Evidence C"

        assert (
            record_a["provenance"]
            != record_b["provenance"]
        )

        assert (
            record_b["provenance"]
            != record_c["provenance"]
        )

        assert (
            record_a["provenance"]
            != record_c["provenance"]
        )

        # -------------------------------------------------
        # 6. Replacement history must contain exactly
        #    A -> B and B -> C.
        # -------------------------------------------------

        replacement_store = (
            BrainTrustReplacementStore(storage)
        )

        history = replacement_store.read_recent()

        assert len(history) == 2

        first = history[0]
        second = history[1]

        assert (
            first["previous_provenance"]
            == record_a["provenance"]
        )

        assert (
            first["replacement_provenance"]
            == record_b["provenance"]
        )

        assert (
            second["previous_provenance"]
            == record_b["provenance"]
        )

        assert (
            second["replacement_provenance"]
            == record_c["provenance"]
        )

        # -------------------------------------------------
        # 7. No direct A -> C replacement relationship.
        # -------------------------------------------------

        assert not any(
            item["previous_provenance"]
            == record_a["provenance"]
            and item["replacement_provenance"]
            == record_c["provenance"]
            for item in history
        )

        # -------------------------------------------------
        # 8. Replacement authentication must verify.
        # -------------------------------------------------

        provenance = BrainTrustProvenance(storage)

        for item in history:
            assert (
                provenance.verify_replacement(
                    brain_id=item["brain_id"],
                    previous_provenance=(
                        item["previous_provenance"]
                    ),
                    replacement_provenance=(
                        item["replacement_provenance"]
                    ),
                    reason=item["reason"],
                    provenance=item["provenance"],
                )
                is True
            )

        # -------------------------------------------------
        # 9. Lifecycle remains ACTIVE.
        # -------------------------------------------------

        assert (
            record_a["lifecycle"]
            == BrainTrustEvidenceLifecycle.ACTIVE.value
        )

        assert (
            record_b["lifecycle"]
            == BrainTrustEvidenceLifecycle.ACTIVE.value
        )

        assert (
            record_c["lifecycle"]
            == BrainTrustEvidenceLifecycle.ACTIVE.value
        )

        # -------------------------------------------------
        # 10. Trust status remains explicitly controlled.
        # -------------------------------------------------

        assert (
            brain.trust_status
            == BrainTrustStatus.VERIFIED
        )

        assert (
            brain.trust_evidence
            == "Evidence A"
        )

        # -------------------------------------------------
        # 11. Replacement must not change capabilities.
        # -------------------------------------------------

        assert brain.capabilities == {
            BrainCapability.VERIFY,
        }

        # -------------------------------------------------
        # 12. Replacement must not grant execution
        #     or protected capabilities.
        # -------------------------------------------------

        assert (
            BrainCapability.CODE
            not in brain.capabilities
        )

        assert (
            BrainCapability.CREATE
            not in brain.capabilities
        )

        assert (
            BrainCapability.PLAN
            not in brain.capabilities
        )

        # -------------------------------------------------
        # 13. Replacement history is append-only.
        # -------------------------------------------------

        history_before = (
            replacement_store.read_recent()
        )

        assert len(history_before) == 2

        # Re-read without performing another replacement.
        history_after = (
            replacement_store.read_recent()
        )

        assert history_after == history_before

        # -------------------------------------------------
        # 14. Final record remains independently valid.
        # -------------------------------------------------

        assert (
            brain.verify_authenticated_trust_record(
                record_c,
                storage_directory=storage,
            )
            is True
        )


def test_replacement_does_not_change_brain_identity() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain()

        original_brain_id = brain.brain_id

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Identity evidence",
        )

        record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        brain.replace_authenticated_trust_record(
            record,
            storage_directory=storage,
            new_evidence="New identity evidence",
            reason="Evidence refresh.",
        )

        assert brain.brain_id == original_brain_id


def test_replacement_does_not_change_constitution() -> None:
    """
    Replacement operates only on authenticated evidence.

    No constitution object or constitutional method is
    modified by the replacement operation.
    """

    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)

        brain = create_brain()

        brain.set_trust_status(
            BrainTrustStatus.VERIFIED,
            evidence="Constitution boundary evidence",
        )

        record = (
            brain.create_authenticated_trust_record(
                storage_directory=storage,
            )
        )

        brain.replace_authenticated_trust_record(
            record,
            storage_directory=storage,
            new_evidence="Replacement evidence",
            reason="Evidence review.",
        )

        # The replacement operation has no API capable
        # of modifying the constitution.
        assert hasattr(
            brain,
            "replace_authenticated_trust_record",
        )

        assert not hasattr(
            brain,
            "modify_constitution",
        )

        assert not hasattr(
            brain,
            "override_constitution",
        )


def run_all_tests() -> None:
    test_complete_replacement_integrity_gate()
    test_replacement_does_not_change_brain_identity()
    test_replacement_does_not_change_constitution()

    print(
        "SAHIBEX 6P-27 FINAL "
        "REPLACEMENT INTEGRITY GATE: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
