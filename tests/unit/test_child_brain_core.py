from core.brain.child_brain_core import (
    ChildBrainCore,
    ChildCognitiveAction,
    ChildCoreDecision,
)


def main() -> None:
    core = ChildBrainCore()

    result = core.evaluate(ChildCognitiveAction.THINK)
    assert result.allowed is True
    assert result.decision == ChildCoreDecision.ALLOW_COGNITION

    result = core.evaluate(ChildCognitiveAction.RESEARCH)
    assert result.allowed is True

    result = core.evaluate(ChildCognitiveAction.PLAN)
    assert result.allowed is True

    result = core.evaluate(
        ChildCognitiveAction.EXECUTE,
        mother_approved=False,
    )
    assert result.allowed is False
    assert result.decision == ChildCoreDecision.REQUIRE_MOTHER_AUTHORITY

    result = core.evaluate(
        ChildCognitiveAction.EXECUTE,
        mother_approved=True,
    )
    assert result.allowed is True

    result = core.evaluate(
        ChildCognitiveAction.FINANCIAL,
        human_approved=False,
    )
    assert result.allowed is False
    assert result.decision == ChildCoreDecision.REQUIRE_HUMAN_AUTHORITY

    result = core.evaluate(
        ChildCognitiveAction.FINANCIAL,
        human_approved=True,
    )
    assert result.allowed is True

    assert core.can_think_independently()
    assert core.can_research_independently()
    assert core.can_analyze_independently()
    assert core.can_learn_independently()
    assert core.can_plan_independently()
    assert core.can_propose_independently()

    assert core.protected_action_requires_mother()
    assert core.sensitive_action_requires_human()

    assert not core.can_self_authorize()
    assert not core.can_grant_authority()
    assert not core.can_override_mother()
    assert not core.can_override_human()
    assert not core.executes_actions()
    assert not core.modifies_soul()
    assert not core.modifies_constitution()

    print("SAHIBEX CHILD BRAIN CORE TEST: PASS")


if __name__ == "__main__":
    main()
