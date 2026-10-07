from dataclasses import dataclass


PHASE_J_VERSION = "PHASE-J-INHIBITION-1"


@dataclass(frozen=True)
class InhibitionAssessment:
    """Read-only assessment of inhibition/control readiness."""

    item_id: str
    item_name: str
    blocked: bool
    reason: str


class InhibitionControlExpansion:
    """Additive, read-only inhibition/control assessment layer.

    This component never executes actions, grants permissions, modifies the
    Constitution, or overrides Human Authority.
    """

    ITEM_NAMES = (
        "Inhibition Foundation",
        "Impulse Suppression",
        "Unsafe Action Blocking",
        "Protected Action Boundary",
        "Risk-Based Inhibition",
        "Conflict-Based Inhibition",
        "Distraction Inhibition",
        "Prompt-Injection Inhibition",
        "Permission-Based Inhibition",
        "Emergency-Stop Inhibition",
        "Human Authority / Constitution Boundary",
    )
    ITEM_IDS = tuple(f"J-{index:02d}" for index in range(1, 12))

    def assess(
        self,
        *,
        impulse: bool = False,
        unsafe: bool = False,
        protected: bool = False,
        high_risk: bool = False,
        conflict: bool = False,
        distracted: bool = False,
        prompt_injection: bool = False,
        permission_granted: bool = False,
        emergency_stop: bool = False,
        human_authorized: bool = True,
        constitution_change: bool = False,
    ) -> tuple[InhibitionAssessment, ...]:
        flags = {
            "impulse": bool(impulse),
            "unsafe": bool(unsafe),
            "protected": bool(protected),
            "high_risk": bool(high_risk),
            "conflict": bool(conflict),
            "distracted": bool(distracted),
            "prompt_injection": bool(prompt_injection),
            "permission_granted": bool(permission_granted),
            "emergency_stop": bool(emergency_stop),
            "human_authorized": bool(human_authorized),
            "constitution_change": bool(constitution_change),
        }

        reasons = (
            "inhibition assessment available",
            "impulse suppressed" if flags["impulse"] else "no impulse signal",
            "unsafe action blocked" if flags["unsafe"] else "no unsafe signal",
            "protected action requires permission"
            if flags["protected"] and not flags["permission_granted"]
            else "protected boundary respected",
            "high-risk action inhibited" if flags["high_risk"] else "risk acceptable",
            "conflicting action inhibited" if flags["conflict"] else "no conflict signal",
            "distraction inhibited" if flags["distracted"] else "attention stable",
            "prompt-injection signal inhibited"
            if flags["prompt_injection"]
            else "no prompt-injection signal",
            "permission boundary respected"
            if flags["protected"] and not flags["permission_granted"]
            else "permission state does not require inhibition",
            "emergency stop blocks protected execution"
            if flags["emergency_stop"]
            else "emergency stop clear",
            "Human Authority / Constitution boundary enforced"
            if (not flags["human_authorized"] or flags["constitution_change"])
            else "Human Authority / Constitution boundary clear",
        )

        blocked = (
            False,
            flags["impulse"],
            flags["unsafe"],
            flags["protected"] and not flags["permission_granted"],
            flags["high_risk"],
            flags["conflict"],
            flags["distracted"],
            flags["prompt_injection"],
            flags["protected"] and not flags["permission_granted"],
            flags["emergency_stop"],
            (not flags["human_authorized"]) or flags["constitution_change"],
        )

        return tuple(
            InhibitionAssessment(
                item_id=item_id,
                item_name=item_name,
                blocked=is_blocked,
                reason=reason,
            )
            for item_id, item_name, is_blocked, reason in zip(
                self.ITEM_IDS, self.ITEM_NAMES, blocked, reasons
            )
        )

    @staticmethod
    def security_summary() -> dict[str, bool]:
        return {
            "read_only": True,
            "executes_actions": False,
            "grants_permission": False,
            "modifies_constitution": False,
            "overrides_human_authority": False,
        }
