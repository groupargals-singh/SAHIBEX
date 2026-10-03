from __future__ import annotations

from core.research.reliability import (
    DEFAULT_RELIABILITY,
    RELIABILITY_CONTRACT_VERSION,
    apply_reliability_contract,
    normalize_reliability,
)


def main() -> None:
    assert normalize_reliability(0.5) == 0.5
    print("[PASS] normal reliability preserved")

    assert normalize_reliability(1.5) == 1.0
    print("[PASS] upper bound normalized")

    assert normalize_reliability(-0.5) == 0.0
    print("[PASS] lower bound normalized")

    assert normalize_reliability("invalid") == DEFAULT_RELIABILITY
    print("[PASS] invalid reliability protected")

    metadata = apply_reliability_contract(
        {
            "provider": "test-provider",
            "reliability": 0.9,
        }
    )

    assert metadata["provider"] == "test-provider"
    assert metadata["reliability"] == 0.9
    assert metadata["reliability_source"] == "provider"
    assert (
        metadata["reliability_method"]
        == "provider_declared_default"
    )
    assert (
        metadata["reliability_version"]
        == RELIABILITY_CONTRACT_VERSION
    )
    print("[PASS] reliability provenance contract")

    existing = apply_reliability_contract(
        {
            "reliability": 0.8,
            "reliability_source": "manual",
            "reliability_method": "human_review",
            "reliability_version": "custom-1",
        }
    )

    assert existing["reliability"] == 0.8
    assert existing["reliability_source"] == "manual"
    assert existing["reliability_method"] == "human_review"
    assert existing["reliability_version"] == "custom-1"
    print("[PASS] existing provenance preserved")

    print("SAHIBEX SOURCE RELIABILITY CONTRACT TEST: PASS")


if __name__ == "__main__":
    main()
