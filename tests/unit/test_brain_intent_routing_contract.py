from __future__ import annotations

from core.brain.intent_routing import (
    BrainIntentRouter,
    BrainIntentRoutingResult,
)


def main() -> None:
    router = BrainIntentRouter()

    research_result = router.route(
        intent="research",
        brain_id="brain-research",
    )

    assert isinstance(
        research_result,
        BrainIntentRoutingResult,
    )

    assert research_result.success is True
    assert research_result.intent == "research"
    assert research_result.brain_id == "brain-research"
    assert research_result.route_id

    reasoning_result = router.route(
        intent="think",
        brain_id="brain-reasoning",
    )

    assert reasoning_result.success is True
    assert reasoning_result.intent == "think"
    assert reasoning_result.brain_id == "brain-reasoning"
    assert reasoning_result.route_id != research_result.route_id

    try:
        router.route(
            intent="",
            brain_id="brain-test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty intent must be rejected."
        )

    try:
        router.route(
            intent="research",
            brain_id="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty brain ID must be rejected."
        )

    fields = BrainIntentRoutingResult.__dataclass_fields__

    forbidden_fields = {
        "api_key",
        "credential",
        "authorization_token",
        "permission_grant",
    }

    assert forbidden_fields.isdisjoint(fields.keys())

    assert not hasattr(
        BrainIntentRouter,
        "grant_permission",
    )

    assert not hasattr(
        BrainIntentRouter,
        "execute_brain",
    )

    print(
        "SAHIBEX 6N-3 BRAIN INTENT ROUTING CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
