import hashlib
import hmac
from security.audit.brain_trust_replacement import (
    BrainTrustEvidenceReplacement,
)


def create_proof(
    replacement: BrainTrustEvidenceReplacement,
    key: bytes,
) -> str:
    return hmac.new(
        key,
        replacement.canonical_payload(),
        hashlib.sha256,
    ).hexdigest()


def test_replacement_payload_is_deterministic() -> None:
    replacement_a = BrainTrustEvidenceReplacement(
        brain_id="brain-001",
        previous_provenance="old-proof",
        replacement_provenance="new-proof",
        reason="Evidence replacement.",
    )

    replacement_b = BrainTrustEvidenceReplacement(
        brain_id="brain-001",
        previous_provenance="old-proof",
        replacement_provenance="new-proof",
        reason="Evidence replacement.",
    )

    assert (
        replacement_a.canonical_payload()
        == replacement_b.canonical_payload()
    )


def test_replacement_proof_is_deterministic() -> None:
    key = b"replacement-test-key-32-bytes-long!!"

    replacement = BrainTrustEvidenceReplacement(
        brain_id="brain-001",
        previous_provenance="old-proof",
        replacement_provenance="new-proof",
        reason="Evidence replacement.",
    )

    proof_a = create_proof(replacement, key)
    proof_b = create_proof(replacement, key)

    assert proof_a == proof_b


def test_tampered_previous_provenance_changes_proof() -> None:
    key = b"replacement-test-key-32-bytes-long!!"

    original = BrainTrustEvidenceReplacement(
        brain_id="brain-001",
        previous_provenance="old-proof",
        replacement_provenance="new-proof",
        reason="Evidence replacement.",
    )

    tampered = BrainTrustEvidenceReplacement(
        brain_id="brain-001",
        previous_provenance="forged-old-proof",
        replacement_provenance="new-proof",
        reason="Evidence replacement.",
    )

    assert create_proof(original, key) != (
        create_proof(tampered, key)
    )


def test_tampered_replacement_provenance_changes_proof() -> None:
    key = b"replacement-test-key-32-bytes-long!!"

    original = BrainTrustEvidenceReplacement(
        brain_id="brain-001",
        previous_provenance="old-proof",
        replacement_provenance="new-proof",
        reason="Evidence replacement.",
    )

    tampered = BrainTrustEvidenceReplacement(
        brain_id="brain-001",
        previous_provenance="old-proof",
        replacement_provenance="forged-new-proof",
        reason="Evidence replacement.",
    )

    assert create_proof(original, key) != (
        create_proof(tampered, key)
    )


def test_tampered_reason_changes_proof() -> None:
    key = b"replacement-test-key-32-bytes-long!!"

    original = BrainTrustEvidenceReplacement(
        brain_id="brain-001",
        previous_provenance="old-proof",
        replacement_provenance="new-proof",
        reason="Evidence replacement.",
    )

    tampered = BrainTrustEvidenceReplacement(
        brain_id="brain-001",
        previous_provenance="old-proof",
        replacement_provenance="new-proof",
        reason="Forged replacement reason.",
    )

    assert create_proof(original, key) != (
        create_proof(tampered, key)
    )


def run_all_tests() -> None:
    test_replacement_payload_is_deterministic()
    test_replacement_proof_is_deterministic()
    test_tampered_previous_provenance_changes_proof()
    test_tampered_replacement_provenance_changes_proof()
    test_tampered_reason_changes_proof()

    print(
        "SAHIBEX 6P-27 REPLACEMENT "
        "AUTHENTICATION CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
