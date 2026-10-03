from __future__ import annotations

import tempfile
from pathlib import Path

from security.audit.brain_trust_provenance import (
    BrainTrustProvenance,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # ---------------------------------------------------------
    # 6P-25 Brain Trust Evidence Identity Integrity
    # ---------------------------------------------------------

    with tempfile.TemporaryDirectory() as temp_dir:
        storage = Path(temp_dir)
        provenance = BrainTrustProvenance(storage)

        # 1. Real brain trust evidence must verify.
        proof = provenance.sign(
            brain_id="brain-A",
            trust_status="verified",
            evidence="verification-evidence-A",
        )

        record = {
            "brain_id": "brain-A",
            "trust_status": "verified",
            "evidence": "verification-evidence-A",
            "provenance": proof,
        }

        result = provenance.verify(record)

        check(
            result.verified is True,
            "Authentic brain trust evidence must verify.",
        )

        check(
            result.brain_id == "brain-A",
            "Verified result must preserve brain identity.",
        )

        # 2. Brain A evidence must not become Brain B evidence.
        tampered_brain = dict(record)
        tampered_brain["brain_id"] = "brain-B"

        result = provenance.verify(tampered_brain)

        check(
            result.verified is False,
            "Brain A evidence must not verify for Brain B.",
        )

        # 3. Trust status tampering must fail.
        tampered_status = dict(record)
        tampered_status["trust_status"] = "suspended"

        result = provenance.verify(tampered_status)

        check(
            result.verified is False,
            "Trust status tampering must be rejected.",
        )

        # 4. Evidence tampering must fail.
        tampered_evidence = dict(record)
        tampered_evidence["evidence"] = (
            "forged-verification-evidence"
        )

        result = provenance.verify(tampered_evidence)

        check(
            result.verified is False,
            "Trust evidence tampering must be rejected.",
        )

        # 5. Missing provenance must fail.
        missing_provenance = dict(record)
        del missing_provenance["provenance"]

        result = provenance.verify(missing_provenance)

        check(
            result.verified is False,
            "Missing provenance must be rejected.",
        )

        # 6. A forged random provenance must fail.
        forged = dict(record)
        forged["provenance"] = "forged-proof"

        result = provenance.verify(forged)

        check(
            result.verified is False,
            "Forged provenance must be rejected.",
        )

        # 7. A new brain must receive a different proof.
        proof_b = provenance.sign(
            brain_id="brain-B",
            trust_status="verified",
            evidence="verification-evidence-B",
        )

        check(
            proof_b != proof,
            "Different brain identities must not share proof.",
        )

        # 8. Trust provenance must not expose permission authority.
        forbidden_names = {
            "permission",
            "authorization",
            "execute",
            "grant_permission",
        }

        public_names = set(
            dir(provenance)
        )

        check(
            forbidden_names.isdisjoint(public_names),
            "Trust provenance must not expose authority APIs.",
        )

    print(
        "SAHIBEX 6P-25 BRAIN TRUST PROVENANCE "
        "INTEGRITY TEST: PASS"
    )


if __name__ == "__main__":
    main()
