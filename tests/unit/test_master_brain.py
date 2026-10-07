from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from core.brain.master_brain import MasterBrain
from core.policies.constitution import ActionDecision


def main() -> None:
    print("=" * 60)
    print("SAHIBEX MASTER BRAIN TEST")
    print("=" * 60)

    brain = MasterBrain()

    result = brain.process(
        "Explain how SAHIBEX works."
    )

    assert result.success is True
    assert result.intent == "explain"
    assert result.plan_created is True
    assert result.task_count == 2

    print("[PASS] general reasoning pipeline")

    result = brain.process(
        "Search the internet for AI security."
    )

    assert result.intent == "search"
    assert result.action == "research"
    assert result.permission_allowed is True
    assert (
        result.authority_decision
        == ActionDecision.ALLOW.value
    )
    assert result.success is False
    assert result.plan_created is False
    assert (
        "required acquisition provider is not registered"
        in result.message
    )

    print("[PASS] research authorization pipeline")

    result = brain.process(
        "Create a Python program."
    )

    assert result.success is True
    assert result.intent == "code"
    assert result.plan_created is True

    print("[PASS] coding planning pipeline")

    result = brain.process(
        "Delete the project files."
    )

    assert result.success is True
    assert result.confirmation_required is True
    assert (
        result.authority_decision
        == ActionDecision.REQUIRE_CONFIRMATION.value
    )
    assert result.permission_allowed is False
    assert result.plan_created is False

    print("[PASS] protected action blocked")

    result = brain.process(
        "Change the system configuration.",
        user_confirmation=True,
    )

    assert result.success is False
    assert result.permission_allowed is False
    assert result.plan_created is False

    print(
        "[PASS] critical action remains blocked"
    )

    result = brain.process("")

    assert result.success is False
    assert result.task_count == 0

    print("[PASS] empty request handling")

    assert (
        brain.constitution
        .can_sahibex_modify_constitution()
        is False
    )

    assert (
        brain.constitution
        .can_sahibex_override_user(
            action=__import__(
                "core.policies.constitution",
                fromlist=["ActionClass"],
            ).ActionClass.SYSTEM_CHANGE
        )
        is False
    )

    print(
        "[PASS] constitution cannot be overridden"
    )

    assert len(brain.context.history) >= 4

    print("[PASS] context integration")

    print("=" * 60)
    print("SAHIBEX MASTER BRAIN TEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
