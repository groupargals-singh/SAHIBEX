from core.brain.operational_brain import (
    OperationalBrain,
    OperationalBrainResult,
)


def main() -> None:
    brain = OperationalBrain()

    result = brain.process(
        objective="Research AI security",
        intent="RESEARCH",
    )

    assert isinstance(result, OperationalBrainResult)
    assert result.success is True
    assert result.objective == "Research AI security"
    assert result.intent == "research"
    assert result.status == "READY"
    assert result.result_id

    try:
        brain.process(
            objective="",
            intent="research",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Empty objective must be rejected")

    try:
        brain.process(
            objective="Research",
            intent="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Empty intent must be rejected")

    forbidden_methods = (
        "grant_permission",
        "execute_action",
        "override_constitution",
    )

    for method_name in forbidden_methods:
        assert not hasattr(brain, method_name), (
            f"Forbidden method exists: {method_name}"
        )

    assert not hasattr(result, "permission_granted")
    assert not hasattr(result, "execution_result")

    print("SAHIBEX 6O-1 OPERATIONAL BRAIN CONTRACT TEST: PASS")


if __name__ == "__main__":
    main()
