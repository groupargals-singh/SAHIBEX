from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AuthorityLevel(str, Enum):
    USER = "user"
    SAHIBEX = "sahibex"


class BrainRole(str, Enum):
    """
    Constitutional identity of a brain instance.

    MOTHER_BRAIN:
        SAHIBEX itself.

    INTERNAL_ARMY:
        Specialist brain living inside SAHIBEX or inside a Child Brain.

    CHILD_BRAIN:
        Independent brain instance outside SAHIBEX, operating under
        SAHIBEX Mother Brain authority.
    """

    MOTHER_BRAIN = "mother_brain"
    INTERNAL_ARMY = "internal_army"
    CHILD_BRAIN = "child_brain"


class ActionDecision(str, Enum):
    ALLOW = "allow"
    REQUIRE_CONFIRMATION = "require_confirmation"
    DENY = "deny"


class ActionClass(str, Enum):
    THINK = "think"
    RESEARCH = "research"
    READ = "read"

    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    NETWORK = "network"
    CREDENTIAL = "credential"
    SYSTEM_CHANGE = "system_change"
    FINANCIAL = "financial"
    SELF_UPDATE = "self_update"
    EXTERNAL_CONTROL = "external_control"


@dataclass(frozen=True)
class AuthorityDecision:
    decision: ActionDecision
    authority: AuthorityLevel
    reason: str


@dataclass(frozen=True)
class BrainAuthorityDecision:
    """
    Result of a constitutional authority check for a brain instance.

    This object records authority only.
    It does not execute anything and cannot grant itself permission.
    """

    allowed: bool
    decision: ActionDecision
    brain_role: BrainRole
    reason: str


class SahibexConstitution:
    """
    Root authority policy for SAHIBEX.

    Constitutional hierarchy:

        HUMAN
          ↓
        SAHIBEX CONSTITUTION
          ↓
        SAHIBEX MOTHER BRAIN
          ↓
        CHILD BRAINS
          ↓
        CHILD INTERNAL ARMY
          ↓
        SOFTWARE / TOOLS

    Inside SAHIBEX:

        SAHIBEX MOTHER BRAIN
          ↓
        INTERNAL ARMY BRAINS

    Core principles:

    - Human authority is highest.
    - SAHIBEX is the Mother Brain.
    - Internal Army Brains are subordinate specialist brains.
    - Child Brains are separate brain instances subordinate to SAHIBEX.
    - Capability never creates authority.
    - Protected actions require explicit user authorization.
    - A subordinate brain cannot override its parent authority.
    - The running AI cannot modify the constitutional root.
    """

    PROTECTED_ACTIONS = {
        ActionClass.WRITE,
        ActionClass.DELETE,
        ActionClass.EXECUTE,
        ActionClass.NETWORK,
        ActionClass.CREDENTIAL,
        ActionClass.SYSTEM_CHANGE,
        ActionClass.FINANCIAL,
        ActionClass.SELF_UPDATE,
        ActionClass.EXTERNAL_CONTROL,
    }

    AUTONOMOUS_ACTIONS = {
        ActionClass.THINK,
        ActionClass.RESEARCH,
        ActionClass.READ,
    }

    def decide(
        self,
        action: ActionClass,
        *,
        user_confirmation: bool = False,
    ) -> AuthorityDecision:

        if action in self.AUTONOMOUS_ACTIONS:
            return AuthorityDecision(
                decision=ActionDecision.ALLOW,
                authority=AuthorityLevel.SAHIBEX,
                reason=(
                    "Action is non-destructive and "
                    "does not require protected execution."
                ),
            )

        if action in self.PROTECTED_ACTIONS:
            if user_confirmation:
                return AuthorityDecision(
                    decision=ActionDecision.ALLOW,
                    authority=AuthorityLevel.USER,
                    reason="Explicit user authorization was provided.",
                )

            return AuthorityDecision(
                decision=ActionDecision.REQUIRE_CONFIRMATION,
                authority=AuthorityLevel.USER,
                reason="Protected action requires explicit user authorization.",
            )

        return AuthorityDecision(
            decision=ActionDecision.DENY,
            authority=AuthorityLevel.USER,
            reason="Unknown action class is denied by default.",
        )

    def authorize_brain(
        self,
        *,
        brain_role: BrainRole,
        action: ActionClass,
        user_confirmation: bool = False,
        parent_authorized: bool = True,
    ) -> BrainAuthorityDecision:
        """
        Evaluate whether a brain role may proceed toward an action.

        Important:

        Brain role does NOT replace the normal action constitution.

        A brain may be technically capable of an action while still lacking
        constitutional authority to perform it.

        Child/Internal Army brains cannot elevate themselves to Mother Brain
        authority.
        """

        if not isinstance(brain_role, BrainRole):
            raise TypeError("brain_role must be a BrainRole.")

        if not isinstance(action, ActionClass):
            raise TypeError("action must be an ActionClass.")

        if not isinstance(user_confirmation, bool):
            raise TypeError("user_confirmation must be a boolean.")

        if not isinstance(parent_authorized, bool):
            raise TypeError("parent_authorized must be a boolean.")

        # No subordinate brain may continue after its parent denies authority.
        if brain_role in {
            BrainRole.INTERNAL_ARMY,
            BrainRole.CHILD_BRAIN,
        } and not parent_authorized:
            return BrainAuthorityDecision(
                allowed=False,
                decision=ActionDecision.DENY,
                brain_role=brain_role,
                reason=(
                    "Parent authority denied the action. "
                    "The subordinate brain cannot override that denial."
                ),
            )

        # Normal constitutional action policy remains authoritative.
        action_decision = self.decide(
            action,
            user_confirmation=user_confirmation,
        )

        if action_decision.decision == ActionDecision.ALLOW:
            return BrainAuthorityDecision(
                allowed=True,
                decision=ActionDecision.ALLOW,
                brain_role=brain_role,
                reason=action_decision.reason,
            )

        if action_decision.decision == ActionDecision.REQUIRE_CONFIRMATION:
            return BrainAuthorityDecision(
                allowed=False,
                decision=ActionDecision.REQUIRE_CONFIRMATION,
                brain_role=brain_role,
                reason=(
                    "Protected action requires explicit user authorization. "
                    "Brain role cannot replace human authorization."
                ),
            )

        return BrainAuthorityDecision(
            allowed=False,
            decision=ActionDecision.DENY,
            brain_role=brain_role,
            reason=action_decision.reason,
        )

    def can_brain_override_parent(
        self,
        brain_role: BrainRole,
    ) -> bool:
        """
        No subordinate brain can override its parent authority.
        """

        if not isinstance(brain_role, BrainRole):
            raise TypeError("brain_role must be a BrainRole.")

        return brain_role == BrainRole.MOTHER_BRAIN

    def can_child_override_sahibex(self) -> bool:
        """
        Child Brains can never override SAHIBEX Mother Brain authority.
        """

        return False

    def can_internal_army_override_mother(self) -> bool:
        """
        Internal Army Brains can never override SAHIBEX Mother Brain.
        """

        return False

    def can_sahibex_override_user(
        self,
        action: ActionClass,
    ) -> bool:
        """
        SAHIBEX can never override user authority.
        """

        return False

    def can_sahibex_modify_constitution(self) -> bool:
        """
        The running AI cannot rewrite its own root authority policy.
        """

        return False
