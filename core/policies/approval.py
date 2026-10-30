from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(str, Enum):
    RESPOND = "respond"
    RESEARCH = "research"
    CREATE = "create"
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
    RUN_COMMAND = "run_command"
    NETWORK_ACCESS = "network_access"
    CREDENTIAL_USE = "credential_use"
    SYSTEM_CHANGE = "system_change"
    FINANCIAL_ACTION = "financial_action"


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    requires_confirmation: bool
    risk: RiskLevel
    reason: str


class PermissionEngine:
    """
    Central safety gate for SAHIBEX.

    Important:
    This layer decides what an action is allowed to do.
    It does not execute the action.
    """

    RISK_MAP = {
        ActionType.RESPOND: RiskLevel.LOW,
        ActionType.RESEARCH: RiskLevel.LOW,
        ActionType.CREATE: RiskLevel.LOW,
        ActionType.READ_FILE: RiskLevel.LOW,

        ActionType.WRITE_FILE: RiskLevel.MEDIUM,
        ActionType.NETWORK_ACCESS: RiskLevel.MEDIUM,

        ActionType.DELETE_FILE: RiskLevel.HIGH,
        ActionType.RUN_COMMAND: RiskLevel.HIGH,
        ActionType.CREDENTIAL_USE: RiskLevel.HIGH,

        ActionType.SYSTEM_CHANGE: RiskLevel.CRITICAL,
        ActionType.FINANCIAL_ACTION: RiskLevel.CRITICAL,
    }

    def check(
        self,
        action: ActionType,
        confirmation: bool = False,
    ) -> PermissionDecision:
        if not isinstance(action, ActionType):
            raise TypeError("action must be an ActionType.")
        if not isinstance(confirmation, bool):
            raise TypeError("confirmation must be a boolean.")

        risk = self.RISK_MAP[action]

        if action in {
            ActionType.RESPOND,
            ActionType.RESEARCH,
            ActionType.CREATE,
            ActionType.READ_FILE,
        }:
            return PermissionDecision(
                allowed=True,
                requires_confirmation=False,
                risk=risk,
                reason="Low-risk action is allowed.",
            )

        if action in {
            ActionType.WRITE_FILE,
            ActionType.NETWORK_ACCESS,
        }:
            if confirmation:
                return PermissionDecision(
                    allowed=True,
                    requires_confirmation=False,
                    risk=risk,
                    reason="User confirmation received.",
                )

            return PermissionDecision(
                allowed=False,
                requires_confirmation=True,
                risk=risk,
                reason="User confirmation is required.",
            )

        if action in {
            ActionType.DELETE_FILE,
            ActionType.RUN_COMMAND,
            ActionType.CREDENTIAL_USE,
        }:
            if confirmation:
                return PermissionDecision(
                    allowed=True,
                    requires_confirmation=False,
                    risk=risk,
                    reason="Explicit user confirmation received.",
                )

            return PermissionDecision(
                allowed=False,
                requires_confirmation=True,
                risk=risk,
                reason="High-risk action requires explicit confirmation.",
            )

        return PermissionDecision(
            allowed=False,
            requires_confirmation=True,
            risk=RiskLevel.CRITICAL,
            reason="Critical action is blocked by default.",
        )
