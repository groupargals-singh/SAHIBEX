from __future__ import annotations

from core.brain.orchestration import (
    BrainOrchestration,
    BrainOrchestrationResult,
)


def main() -> None:
    orchestration = BrainOrchestration()

    result = orchestration.create_plan(
        brain_ids=[
            "brain-research",
            "brain-verify",
        ],
        objective="Research and verify an AI security topic.",
    )

    assert isinstance(result, BrainOrchestrationResult)

    assert result.success is True
    assert result.brain_ids == [
        "brain-research",
        "brain-verify",
    ]
    assert result.objective == (
        "Research and verify an AI security topic."
    )
    assert result.plan_id

    second_result = orchestration.create_plan(
        brain_ids=["brain-reasoning"],
        objective="Analyze the collected evidence.",
    )

    assert second_result.success is True
    assert second_result.brain_ids == ["brain-reasoning"]
    assert second_result.plan_id != result.plan_id

    try:
        orchestration.create_plan(
            brain_ids=[],
            objective="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty brain_ids must be rejected."
        )

    try:
        orchestration.create_plan(
            brain_ids=["brain-test"],
            objective="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty objective must be rejected."
        )

    try:
        orchestration.create_plan(
            brain_ids=[""],
            objective="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty brain ID must be rejected."
        )

    fields = BrainOrchestrationResult.__dataclass_fields__

    forbidden_fields = {
        "api_key",
        "credential",
        "authorization_token",
        "permission_grant",
    }

    assert forbidden_fields.isdisjoint(fields.keys())

    assert not hasattr(
        BrainOrchestration,
        "grant_permission",
    )

    assert not hasattr(
        BrainOrchestration,
        "execute_brain",
    )

    print(
        "SAHIBEX 6N-2 BRAIN ORCHESTRATION CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
