from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from core.policies.constitution import ActionClass


class SecurityControl(str, Enum):
    CONSTITUTION = "constitution"
    PERMISSION = "permission"
    AUTHORITY = "authority_boundary"
    AUDIT = "audit"
    PROMPT_INJECTION = "prompt_injection"
    SECRET_PROTECTION = "secret_protection"
    SANDBOX = "sandbox"
    TOOL_ISOLATION = "tool_isolation"
    NETWORK = "network_permission"
    CREDENTIAL = "credential_permission"
    EXTERNAL_CONTROL = "external_control_permission"
    FINANCIAL = "financial_permission"
    SELF_UPDATE = "self_update_permission"
    TAMPER_DETECTION = "tamper_detection"
    EMERGENCY_SHUTDOWN = "emergency_shutdown"


@dataclass(frozen=True)
class SecuritySafetyDecision:
    allowed: bool
    action: ActionClass
    control: SecurityControl
    reason: str


class SecuritySafetyBrain:
    """
    Phase-11 runtime security/safety control plane.

    This is a fail-closed policy/audit boundary. It does not execute
    tools, grant authority, modify Constitution, or replace existing
    permission/verification systems.
    """

    def __init__(self) -> None:
        self._constitution = None
        self._permission_gateway = None
        self._emergency_stop = None

    def bind_runtime(
        self,
        *,
        constitution,
        permission_gateway,
        emergency_stop,
    ) -> None:
        self._constitution = constitution
        self._permission_gateway = permission_gateway
        self._emergency_stop = emergency_stop

    def evaluate_action(
        self,
        action: ActionClass,
        *,
        confirmation: bool = False,
        parent_authorized: bool = True,
    ) -> SecuritySafetyDecision:
        if not isinstance(action, ActionClass):
            raise TypeError("action must be an ActionClass.")
        if not isinstance(confirmation, bool):
            raise TypeError("confirmation must be a boolean.")
        if not isinstance(parent_authorized, bool):
            raise TypeError("parent_authorized must be a boolean.")

        if not parent_authorized:
            return SecuritySafetyDecision(
                False,
                action,
                SecurityControl.AUTHORITY,
                "Parent authority denied action.",
            )

        if self._emergency_stop is not None:
            try:
                stopped = self._emergency_stop.requires_execution_block()
            except AttributeError:
                stopped = True
            if stopped and action in {
                ActionClass.WRITE,
                ActionClass.DELETE,
                ActionClass.EXECUTE,
                ActionClass.NETWORK,
                ActionClass.CREDENTIAL,
                ActionClass.SYSTEM_CHANGE,
                ActionClass.FINANCIAL,
                ActionClass.SELF_UPDATE,
                ActionClass.EXTERNAL_CONTROL,
            }:
                return SecuritySafetyDecision(
                    False,
                    action,
                    SecurityControl.EMERGENCY_SHUTDOWN,
                    "Emergency stop is active.",
                )

        if self._constitution is None:
            return SecuritySafetyDecision(
                False,
                action,
                SecurityControl.CONSTITUTION,
                "Constitution is not bound; fail closed.",
            )

        constitutional = self._constitution.decide(
            action,
            user_confirmation=confirmation,
        )

        if constitutional.decision.value == "deny":
            return SecuritySafetyDecision(
                False,
                action,
                SecurityControl.AUTHORITY,
                constitutional.reason,
            )

        if constitutional.decision.value == "require_confirmation":
            return SecuritySafetyDecision(
                False,
                action,
                SecurityControl.PERMISSION,
                constitutional.reason,
            )

        if self._permission_gateway is None:
            return SecuritySafetyDecision(
                False,
                action,
                SecurityControl.PERMISSION,
                "Permission gateway is not bound; fail closed.",
            )

        # Constitution action and PermissionEngine action namespaces are
        # intentionally separate; the existing Master Brain remains the
        # canonical mapper. Here we only assert that protected actions
        # never become implicitly allowed.
        if action in self._constitution.PROTECTED_ACTIONS and not confirmation:
            return SecuritySafetyDecision(
                False,
                action,
                SecurityControl.PERMISSION,
                "Protected action lacks explicit confirmation.",
            )

        return SecuritySafetyDecision(
            True,
            action,
            SecurityControl.PERMISSION,
            "Constitution and protected-action gate passed.",
        )

    @staticmethod
    def controls() -> tuple[SecurityControl, ...]:
        return tuple(SecurityControl)

    @staticmethod
    def protected_actions() -> frozenset[ActionClass]:
        return frozenset({
            ActionClass.WRITE,
            ActionClass.DELETE,
            ActionClass.EXECUTE,
            ActionClass.NETWORK,
            ActionClass.CREDENTIAL,
            ActionClass.SYSTEM_CHANGE,
            ActionClass.FINANCIAL,
            ActionClass.SELF_UPDATE,
            ActionClass.EXTERNAL_CONTROL,
        })

    @staticmethod
    def can_modify_constitution() -> bool:
        return False

    @staticmethod
    def can_grant_authority() -> bool:
        return False

    @staticmethod
    def can_override_human() -> bool:
        return False

    @staticmethod
    def can_bypass_permission() -> bool:
        return False

    @staticmethod
    def can_disable_audit() -> bool:
        return False

    @staticmethod
    def can_disable_prompt_injection_defense() -> bool:
        return False

    @staticmethod
    def can_read_plaintext_secrets() -> bool:
        return False

    @staticmethod
    def can_allow_uncontrolled_network() -> bool:
        return False

    @staticmethod
    def can_allow_unverified_self_update() -> bool:
        return False

    @staticmethod
    def can_allow_external_control_without_permission() -> bool:
        return False

    @staticmethod
    def can_allow_financial_action_without_permission() -> bool:
        return False

    @staticmethod
    def fail_closed_on_unknown() -> bool:
        return True

    @staticmethod
    def emergency_stop_is_required() -> bool:
        return True

    @staticmethod
    def tamper_detection_is_required() -> bool:
        return True
