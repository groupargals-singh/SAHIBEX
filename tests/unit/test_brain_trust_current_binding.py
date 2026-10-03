from security.audit.brain_trust_current_binding import (
    BrainTrustCurrentBinding,
)


def test_valid_binding() -> None:
    binding = BrainTrustCurrentBinding(
        brain_id="brain-001",
        current_provenance="proof-C",
        root_provenance="proof-A",
        depth=3,
    )

    assert binding.brain_id == "brain-001"
    assert binding.current_provenance == "proof-C"
    assert binding.root_provenance == "proof-A"
    assert binding.depth == 3
    assert binding.is_root_current is False


def test_root_current_binding() -> None:
    binding = BrainTrustCurrentBinding(
        brain_id="brain-001",
        current_provenance="proof-A",
        root_provenance="proof-A",
        depth=1,
    )

    assert binding.is_root_current is True


def test_empty_brain_id_rejected() -> None:
    try:
        BrainTrustCurrentBinding(
            brain_id="",
            current_provenance="proof-A",
            root_provenance="proof-A",
            depth=1,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty brain_id was accepted."
        )


def test_empty_current_provenance_rejected() -> None:
    try:
        BrainTrustCurrentBinding(
            brain_id="brain-001",
            current_provenance="",
            root_provenance="proof-A",
            depth=1,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty current_provenance was accepted."
        )


def test_empty_root_provenance_rejected() -> None:
    try:
        BrainTrustCurrentBinding(
            brain_id="brain-001",
            current_provenance="proof-A",
            root_provenance="",
            depth=1,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty root_provenance was accepted."
        )


def test_zero_depth_rejected() -> None:
    try:
        BrainTrustCurrentBinding(
            brain_id="brain-001",
            current_provenance="proof-A",
            root_provenance="proof-A",
            depth=0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Zero depth was accepted."
        )


def test_boolean_depth_rejected() -> None:
    try:
        BrainTrustCurrentBinding(
            brain_id="brain-001",
            current_provenance="proof-A",
            root_provenance="proof-A",
            depth=True,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Boolean depth was accepted."
        )


def test_canonical_payload_is_deterministic() -> None:
    binding = BrainTrustCurrentBinding(
        brain_id="brain-001",
        current_provenance="proof-C",
        root_provenance="proof-A",
        depth=3,
    )

    expected = (
        b"brain-001\n"
        b"proof-C\n"
        b"proof-A\n"
        b"3"
    )

    assert binding.canonical_payload() == expected


def run_all_tests() -> None:
    test_valid_binding()
    test_root_current_binding()
    test_empty_brain_id_rejected()
    test_empty_current_provenance_rejected()
    test_empty_root_provenance_rejected()
    test_zero_depth_rejected()
    test_boolean_depth_rejected()
    test_canonical_payload_is_deterministic()

    print(
        "SAHIBEX 6P-29 CURRENT TRUST "
        "BINDING CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
