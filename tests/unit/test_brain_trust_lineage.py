from security.audit.brain_trust_lineage import (
    BrainTrustEvidenceLineage,
)


def test_root_lineage_contract() -> None:
    lineage = BrainTrustEvidenceLineage(
        brain_id="brain-lineage-001",
        previous_provenance=None,
        current_provenance="provenance-a",
    )

    assert lineage.is_root is True
    assert lineage.is_replacement is False

    assert lineage.brain_id == "brain-lineage-001"
    assert lineage.previous_provenance is None
    assert lineage.current_provenance == "provenance-a"


def test_replacement_lineage_contract() -> None:
    lineage = BrainTrustEvidenceLineage(
        brain_id="brain-lineage-001",
        previous_provenance="provenance-a",
        current_provenance="provenance-b",
    )

    assert lineage.is_root is False
    assert lineage.is_replacement is True

    assert (
        lineage.previous_provenance
        == "provenance-a"
    )

    assert (
        lineage.current_provenance
        == "provenance-b"
    )


def test_empty_brain_id_rejected() -> None:
    try:
        BrainTrustEvidenceLineage(
            brain_id="   ",
            previous_provenance=None,
            current_provenance="provenance-a",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty brain_id was accepted."
        )


def test_empty_current_provenance_rejected() -> None:
    try:
        BrainTrustEvidenceLineage(
            brain_id="brain-lineage-001",
            previous_provenance=None,
            current_provenance="   ",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty current provenance was accepted."
        )


def test_empty_previous_provenance_rejected() -> None:
    try:
        BrainTrustEvidenceLineage(
            brain_id="brain-lineage-001",
            previous_provenance="   ",
            current_provenance="provenance-b",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty previous provenance was accepted."
        )


def test_same_previous_and_current_rejected() -> None:
    try:
        BrainTrustEvidenceLineage(
            brain_id="brain-lineage-001",
            previous_provenance="same-proof",
            current_provenance="same-proof",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Identical lineage provenance was accepted."
        )


def test_canonical_payload_is_deterministic() -> None:
    lineage_a = BrainTrustEvidenceLineage(
        brain_id="brain-lineage-001",
        previous_provenance="provenance-a",
        current_provenance="provenance-b",
    )

    lineage_b = BrainTrustEvidenceLineage(
        brain_id="brain-lineage-001",
        previous_provenance="provenance-a",
        current_provenance="provenance-b",
    )

    assert (
        lineage_a.canonical_payload()
        == lineage_b.canonical_payload()
    )


def test_canonical_payload_changes_when_lineage_changes() -> None:
    lineage_a = BrainTrustEvidenceLineage(
        brain_id="brain-lineage-001",
        previous_provenance="provenance-a",
        current_provenance="provenance-b",
    )

    lineage_b = BrainTrustEvidenceLineage(
        brain_id="brain-lineage-001",
        previous_provenance="provenance-x",
        current_provenance="provenance-b",
    )

    assert (
        lineage_a.canonical_payload()
        != lineage_b.canonical_payload()
    )


def run_all_tests() -> None:
    test_root_lineage_contract()
    test_replacement_lineage_contract()
    test_empty_brain_id_rejected()
    test_empty_current_provenance_rejected()
    test_empty_previous_provenance_rejected()
    test_same_previous_and_current_rejected()
    test_canonical_payload_is_deterministic()
    test_canonical_payload_changes_when_lineage_changes()

    print(
        "SAHIBEX 6P-28 TRUST EVIDENCE "
        "LINEAGE CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
