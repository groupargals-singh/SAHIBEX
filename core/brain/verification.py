from __future__ import annotations

from enum import Enum


class BrainTrustStatus(str, Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    SUSPENDED = "suspended"
