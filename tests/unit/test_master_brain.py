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

    # Use the curated local-fact path so this deterministic script
    # validates planning without relying on the mock provider echoing prompts.
    result = brain.process(
        "Why does the sky appear blue?"
    )

    assert result.success is True
    assert result.intent == "explain"
    assert result.verification_status == "STRUCTURALLY_VALID"
    assert result.plan_created is False
    assert result.task_count == 0

    print("[PASS] curated factual response path")

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
    # Routine public research now uses the user's standing, narrowly scoped
    # search/learn consent. The default test environment has no live search
    # backend, so acquisition must fail closed for that independent reason.
    assert result.success is False
    assert result.plan_created is True
    assert result.confirmation_required is False
    assert "confirmation" not in result.message.lower()
    assert result.verification_status == "NOT_EXECUTED"

    print("[PASS] standing research consent + fail-closed provider boundary")

    result = brain.process(
        "Create a Python program."
    )

    # Planning may succeed even when the mock provider's echoed code answer
    # is correctly rejected by the operational answer-quality gate.
    assert result.intent == "code"
    assert result.plan_created is True

    print("[PASS] coding planning pipeline")

    result = brain.process(
        "Delete the project files."
    )

    assert result.success is False
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
