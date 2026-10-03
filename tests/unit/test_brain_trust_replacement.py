from security.audit.brain_trust_replacement import (
    BrainTrustEvidenceReplacement,
)


def test_valid_replacement_contract() -> None:
    replacement = BrainTrustEvidenceReplacement(
        brain_id="brain-001",
        previous_provenance="old-proof",
        replacement_provenance="new-proof",
        reason="Evidence replaced after verification.",
    )

    assert replacement.brain_id == "brain-001"
    assert replacement.previous_provenance == "old-proof"
    assert replacement.replacement_provenance == "new-proof"
    assert replacement.reason == (
        "Evidence replaced after verification."
    )


def test_empty_brain_id_is_rejected() -> None:
    try:
        BrainTrustEvidenceReplacement(
            brain_id="",
            previous_provenance="old-proof",
            replacement_provenance="new-proof",
            reason="Replacement reason.",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty brain_id must be rejected."
        )


def test_empty_previous_provenance_is_rejected() -> None:
    try:
        BrainTrustEvidenceReplacement(
            brain_id="brain-001",
            previous_provenance="",
            replacement_provenance="new-proof",
            reason="Replacement reason.",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty previous provenance must be rejected."
        )


def test_empty_replacement_provenance_is_rejected() -> None:
    try:
        BrainTrustEvidenceReplacement(
            brain_id="brain-001",
            previous_provenance="old-proof",
            replacement_provenance="",
            reason="Replacement reason.",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty replacement provenance must be rejected."
        )


def test_empty_reason_is_rejected() -> None:
    try:
        BrainTrustEvidenceReplacement(
            brain_id="brain-001",
            previous_provenance="old-proof",
            replacement_provenance="new-proof",
            reason="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty replacement reason must be rejected."
        )


def test_same_provenance_is_rejected() -> None:
    try:
        BrainTrustEvidenceReplacement(
            brain_id="brain-001",
            previous_provenance="same-proof",
            replacement_provenance="same-proof",
            reason="Replacement reason.",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Replacement must use different provenance."
        )


def run_all_tests() -> None:
    test_valid_replacement_contract()
    test_empty_brain_id_is_rejected()
    test_empty_previous_provenance_is_rejected()
    test_empty_replacement_provenance_is_rejected()
    test_empty_reason_is_rejected()
    test_same_provenance_is_rejected()

    print(
        "SAHIBEX 6P-27 TRUST EVIDENCE "
        "REPLACEMENT CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
