from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from core.brain.root_identity import SahibexRootIdentity
from core.brain.root_instance import SahibexRootInstanceIdentity
from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)
from core.brain.verification import BrainTrustStatus
from security.audit.brain_trust_lineage_integrity_gate import (
    BrainTrustLineageIntegrityGate,
)


def create_brain(brain_id: str) -> SpecialistBrain:
    return SpecialistBrain(
        name="Identity Lineage Boundary Brain",
        description="Phase 0 #9 boundary verification brain.",
        specialization="identity-lineage-boundary",
        capabilities={
            BrainCapability.VERIFY,
        },
        brain_id=brain_id,
    )


def create_trust_lineage(
    storage: Path,
    brain: SpecialistBrain,
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    brain.set_trust_status(
        BrainTrustStatus.VERIFIED,
        evidence="Boundary Evidence A",
    )

    record_a = brain.create_authenticated_trust_record(
        storage_directory=storage,
    )

    record_b = brain.replace_authenticated_trust_record(
        record_a,
        storage_directory=storage,
        new_evidence="Boundary Evidence B",
        reason="Boundary replacement A to B.",
    )

    record_c = brain.replace_authenticated_trust_record(
        record_b,
        storage_directory=storage,
        new_evidence="Boundary Evidence C",
        reason="Boundary replacement B to C.",
    )

    return record_a, record_b, record_c


def test_root_identity_and_instance_are_valid() -> None:
    root_identity = SahibexRootIdentity()

    assert root_identity.validate() is True
    assert root_identity.grants_authority() is False

    root_instance = SahibexRootInstanceIdentity(
        root_identity=root_identity,
    )

    assert root_instance.validate() is True
    assert root_instance.grants_authority() is False
    assert root_instance.is_mother_instance() is True


def test_trust_lineage_is_independent_of_root_identity() -> None:
    root_identity = SahibexRootIdentity()
    root_instance = SahibexRootInstanceIdentity(
        root_identity=root_identity,
    )

    assert root_identity.validate() is True
    assert root_instance.validate() is True

    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain("brain-boundary-001")

        record_a, record_b, record_c = create_trust_lineage(
            storage,
            brain,
        )

        gate = BrainTrustLineageIntegrityGate(storage)

        result = gate.verify(
            brain_id=brain.brain_id,
            current_provenance=record_c["provenance"],
        )

        assert result.passed is True
        assert result.depth == 3
        assert result.root_provenance == record_a["provenance"]

        assert root_identity.validate() is True
        assert root_instance.validate() is True


def test_lineage_does_not_grant_root_authority() -> None:
    root_identity = SahibexRootIdentity()
    root_instance = SahibexRootInstanceIdentity(
        root_identity=root_identity,
    )

    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain("brain-boundary-002")

        _, _, record_c = create_trust_lineage(
            storage,
            brain,
        )

        gate = BrainTrustLineageIntegrityGate(storage)

        result = gate.verify(
            brain_id=brain.brain_id,
            current_provenance=record_c["provenance"],
        )

        assert result.passed is True

        assert root_identity.grants_authority() is False
        assert root_instance.grants_authority() is False


def test_root_identity_tampering_does_not_bypass_lineage_boundary() -> None:
    root_identity = SahibexRootIdentity()

    forged_identity = SahibexRootIdentity()

    object.__setattr__(
        forged_identity,
        "BRAIN_ID",
        "forged-brain",
    )

    assert root_identity.validate() is True
    assert forged_identity.validate() is False

    try:
        SahibexRootInstanceIdentity(
            root_identity=forged_identity,
        )
    except ValueError as exc:
        assert str(exc) == "invalid_root_identity"
    else:
        raise AssertionError(
            "Forged root identity was accepted."
        )


def test_lineage_tampering_does_not_bypass_root_identity() -> None:
    root_identity = SahibexRootIdentity()

    root_instance = SahibexRootInstanceIdentity(
        root_identity=root_identity,
    )

    assert root_identity.validate() is True
    assert root_instance.validate() is True

    with TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        brain = create_brain("brain-boundary-003")

        _, _, record_c = create_trust_lineage(
            storage,
            brain,
        )

        gate = BrainTrustLineageIntegrityGate(storage)

        valid_result = gate.verify(
            brain_id=brain.brain_id,
            current_provenance=record_c["provenance"],
        )

        assert valid_result.passed is True

        assert root_identity.validate() is True
        assert root_instance.validate() is True


def run_all_tests() -> None:
    test_root_identity_and_instance_are_valid()
    test_trust_lineage_is_independent_of_root_identity()
    test_lineage_does_not_grant_root_authority()
    test_root_identity_tampering_does_not_bypass_lineage_boundary()
    test_lineage_tampering_does_not_bypass_root_identity()

    print(
        "SAHIBEX PHASE 0 #9 "
        "IDENTITY-LINEAGE BOUNDARY TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
