from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MotherSandboxDecision(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"


@dataclass(frozen=True)
class MotherSandboxRequest:
    request_id: str
    action: str

    isolated_filesystem: bool
    isolated_memory: bool
    isolated_credentials: bool
    isolated_network: bool
    isolated_runtime: bool


@dataclass(frozen=True)
class MotherSandboxResult:
    decision: MotherSandboxDecision
    reason: str
    missing_isolation: tuple[str, ...] = ()

    @property
    def allowed(self) -> bool:
        return self.decision == MotherSandboxDecision.ALLOW


class MotherSandboxRuntime:
    """
    Sandbox gate for Mother Brain protected execution.

    This layer validates isolation requirements before execution.

    It does NOT:
    - execute commands
    - write files
    - delete files
    - grant permissions
    - bypass Constitution
    - bypass Human approval
    - modify live runtime
    - access credentials
    """

    VERSION = "1.0"

    REQUIRED_ISOLATION = (
        "isolated_filesystem",
        "isolated_memory",
        "isolated_credentials",
        "isolated_network",
        "isolated_runtime",
    )

    def validate(
        self,
        request: MotherSandboxRequest,
    ) -> MotherSandboxResult:
        if not request.request_id.strip():
            return self._blocked(
                "request_id is required"
            )

        if not request.action.strip():
            return self._blocked(
                "action is required"
            )

        missing: list[str] = []

        for field_name in self.REQUIRED_ISOLATION:
            if not getattr(request, field_name):
                missing.append(field_name)

        if missing:
            return MotherSandboxResult(
                decision=MotherSandboxDecision.BLOCK,
                reason="required sandbox isolation is missing",
                missing_isolation=tuple(missing),
            )

        return MotherSandboxResult(
            decision=MotherSandboxDecision.ALLOW,
            reason="sandbox isolation requirements satisfied",
        )

    @staticmethod
    def _blocked(
        reason: str,
    ) -> MotherSandboxResult:
        return MotherSandboxResult(
            decision=MotherSandboxDecision.BLOCK,
            reason=reason,
        )
