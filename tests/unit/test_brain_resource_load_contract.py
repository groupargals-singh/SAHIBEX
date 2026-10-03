from __future__ import annotations

from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # ---------------------------------------------------------
    # 6L-9 Brain Resource / Load Control Contract
    # ---------------------------------------------------------

    brain = SpecialistBrain(
        name="Research Specialist",
        description="Research specialist brain.",
        specialization="research",
        capabilities={
            BrainCapability.RESEARCH,
        },
    )

    # 1. Brain must expose resource/load state.
    check(
        hasattr(brain, "resource_state"),
        "Brain must expose resource_state.",
    )

    # 2. Resource state must use a controlled contract.
    from core.brain.resource import BrainResourceState

    check(
        isinstance(
            brain.resource_state,
            BrainResourceState,
        ),
        "resource_state must use BrainResourceState.",
    )

    # 3. New brain starts with zero workload.
    check(
        brain.resource_state.active_tasks == 0,
        "New brain must start with zero active tasks.",
    )

    # 4. Capacity must be positive.
    check(
        brain.resource_state.max_concurrent_tasks > 0,
        "Brain task capacity must be positive.",
    )

    # 5. Workload must never become negative.
    negative_rejected = False

    try:
        brain.update_load(active_tasks=-1)
    except ValueError:
        negative_rejected = True

    check(
        negative_rejected,
        "Negative workload must be rejected.",
    )

    # 6. Workload can be increased within capacity.
    brain.update_load(active_tasks=1)

    check(
        brain.resource_state.active_tasks == 1,
        "Active task count must update correctly.",
    )

    # 7. Brain must report whether it can accept more work.
    check(
        brain.can_accept_work() is True,
        "Brain should accept work below capacity.",
    )

    # 8. Workload can reach capacity.
    capacity = brain.resource_state.max_concurrent_tasks

    brain.update_load(active_tasks=capacity)

    check(
        brain.resource_state.active_tasks == capacity,
        "Brain must allow workload up to capacity.",
    )

    # 9. Brain must reject additional work at capacity.
    check(
        brain.can_accept_work() is False,
        "Brain must reject additional work at capacity.",
    )

    # 10. Workload above capacity must be rejected.
    over_capacity_rejected = False

    try:
        brain.update_load(
            active_tasks=capacity + 1
        )
    except ValueError:
        over_capacity_rejected = True

    check(
        over_capacity_rejected,
        "Workload above capacity must be rejected.",
    )

    # 11. Workload can be reduced.
    brain.update_load(active_tasks=0)

    check(
        brain.resource_state.active_tasks == 0,
        "Workload must be reducible.",
    )

    check(
        brain.can_accept_work() is True,
        "Brain should accept work after load decreases.",
    )

    # 12. Resource/load state must not grant permissions.
    resource_fields = set(
        brain.resource_state.__dataclass_fields__
    )

    check(
        "permission" not in resource_fields,
        "Resource state must not contain permission fields.",
    )

    check(
        "authorization" not in resource_fields,
        "Resource state must not contain authorization fields.",
    )

    # 13. Resource/load control must preserve brain identity.
    original_id = brain.brain_id

    brain.update_load(active_tasks=1)

    check(
        brain.brain_id == original_id,
        "Load changes must preserve brain identity.",
    )

    print(
        "SAHIBEX 6L-9 BRAIN RESOURCE / LOAD "
        "CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
