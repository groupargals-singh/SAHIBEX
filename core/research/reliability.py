from __future__ import annotations

from typing import Any, Mapping


RELIABILITY_CONTRACT_VERSION = "6G-1"

DEFAULT_RELIABILITY = 0.0

RELIABILITY_SOURCE_KEY = "reliability_source"
RELIABILITY_METHOD_KEY = "reliability_method"
RELIABILITY_VERSION_KEY = "reliability_version"

DEFAULT_RELIABILITY_SOURCE = "provider"
DEFAULT_RELIABILITY_METHOD = "provider_declared_default"


def normalize_reliability(value: Any) -> float:
    """
    Normalize a reliability value into the canonical [0.0, 1.0] range.

    Invalid values safely become 0.0.
    """
    try:
        reliability = float(value)
    except (TypeError, ValueError):
        return DEFAULT_RELIABILITY

    if reliability < 0.0:
        return 0.0

    if reliability > 1.0:
        return 1.0

    return reliability


def apply_reliability_contract(
    metadata: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """
    Apply the 6G-1 Source Reliability Contract to source metadata.

    Existing metadata is preserved.

    Required canonical field:
        reliability

    Standard provenance fields:
        reliability_source
        reliability_method
        reliability_version
    """
    normalized = dict(metadata or {})

    normalized["reliability"] = normalize_reliability(
        normalized.get("reliability", DEFAULT_RELIABILITY)
    )

    normalized.setdefault(
        RELIABILITY_SOURCE_KEY,
        DEFAULT_RELIABILITY_SOURCE,
    )

    normalized.setdefault(
        RELIABILITY_METHOD_KEY,
        DEFAULT_RELIABILITY_METHOD,
    )

    normalized.setdefault(
        RELIABILITY_VERSION_KEY,
        RELIABILITY_CONTRACT_VERSION,
    )

    return normalized
