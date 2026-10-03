from __future__ import annotations

from core.brain.brain_registry import BrainRegistry
from core.brain.specialist_brain import (
    BrainCapability,
    BrainStatus,
    SpecialistBrain,
)
from core.policies.constitution import BrainRole


def expect_failure(fn, label: str) -> None:
    try:
        fn()
    except (TypeError, ValueError):
        print(f"[PASS] {label}")
        return

    raise AssertionError(f"[FAIL] {label}")


def make_brain(
    name: str,
    role: BrainRole,
    parent_brain_id: str | None = None,
) -> SpecialistBrain:
    return SpecialistBrain(
        name=name,
        description=f"{name} lifecycle integrity test brain",
        specialization=name,
        capabilities={BrainCapability.THINK},
        brain_role=role,
        parent_brain_id=parent_brain_id,
    )


def main() -> None:
    print("=" * 60)
    print("SAHIBEX 6L-4 BRAIN LIFECYCLE & STATE INTEGRITY TEST")
    print("=" * 60)

    registry = BrainRegistry()

    mother = make_brain(
        "SAHIBEX Mother Brain",
        BrainRole.MOTHER_BRAIN,
    )
    registry.register(mother)

    army = make_brain(
        "Research Internal Army",
        BrainRole.INTERNAL_ARMY,
        mother.brain_id,
    )
    registry.register(army)

    child = make_brain(
        "Quantum-Bot Child Brain",
        BrainRole.CHILD_BRAIN,
        mother.brain_id,
    )
    registry.register(child)

    child_army = make_brain(
        "Quantum Analysis Internal Army",
        BrainRole.INTERNAL_ARMY,
        child.brain_id,
    )
    registry.register(child_army)

    # ---------------------------------------------------------
    # Initial lifecycle state
    # ---------------------------------------------------------

    for brain, label in (
        (mother, "Mother Brain"),
        (army, "Internal Army Brain"),
        (child, "Child Brain"),
        (child_army, "Child Internal Army"),
    ):
        assert brain.status == BrainStatus.REGISTERED, (
            f"[FAIL] {label} must initially be REGISTERED"
        )
        print(f"[PASS] {label} starts in REGISTERED state")

    # ---------------------------------------------------------
    # REGISTERED -> READY
    # ---------------------------------------------------------

    for brain, label in (
        (mother, "Mother Brain"),
        (army, "Internal Army Brain"),
        (child, "Child Brain"),
        (child_army, "Child Internal Army"),
    ):
        result = brain.transition_to(BrainStatus.READY)

        assert result == BrainStatus.READY
        assert brain.status == BrainStatus.READY

        print(f"[PASS] {label}: REGISTERED -> READY")

    # ---------------------------------------------------------
    # READY -> ACTIVE
    # ---------------------------------------------------------

    for brain, label in (
        (mother, "Mother Brain"),
        (army, "Internal Army Brain"),
        (child, "Child Brain"),
        (child_army, "Child Internal Army"),
    ):
        result = brain.transition_to(BrainStatus.ACTIVE)

        assert result == BrainStatus.ACTIVE
        assert brain.status == BrainStatus.ACTIVE

        print(f"[PASS] {label}: READY -> ACTIVE")

    # ---------------------------------------------------------
    # ACTIVE -> PAUSED
    # ---------------------------------------------------------

    for brain, label in (
        (mother, "Mother Brain"),
        (army, "Internal Army Brain"),
        (child, "Child Brain"),
        (child_army, "Child Internal Army"),
    ):
        result = brain.transition_to(BrainStatus.PAUSED)

        assert result == BrainStatus.PAUSED
        assert brain.status == BrainStatus.PAUSED

        print(f"[PASS] {label}: ACTIVE -> PAUSED")

    # ---------------------------------------------------------
    # PAUSED -> READY
    # ---------------------------------------------------------

    for brain, label in (
        (mother, "Mother Brain"),
        (army, "Internal Army Brain"),
        (child, "Child Brain"),
        (child_army, "Child Internal Army"),
    ):
        result = brain.transition_to(BrainStatus.READY)

        assert result == BrainStatus.READY
        assert brain.status == BrainStatus.READY

        print(f"[PASS] {label}: PAUSED -> READY")

    # ---------------------------------------------------------
    # READY -> ACTIVE again
    # ---------------------------------------------------------

    for brain, label in (
        (mother, "Mother Brain"),
        (army, "Internal Army Brain"),
        (child, "Child Brain"),
        (child_army, "Child Internal Army"),
    ):
        brain.transition_to(BrainStatus.ACTIVE)

        assert brain.status == BrainStatus.ACTIVE

        print(f"[PASS] {label}: READY -> ACTIVE reactivation")

    # ---------------------------------------------------------
    # ACTIVE -> DISABLED
    # ---------------------------------------------------------

    disabled_brain = make_brain(
        "Disabled Lifecycle Test Brain",
        BrainRole.INTERNAL_ARMY,
        mother.brain_id,
    )
    registry.register(disabled_brain)

    disabled_brain.transition_to(BrainStatus.READY)
    disabled_brain.transition_to(BrainStatus.ACTIVE)
    disabled_brain.transition_to(BrainStatus.DISABLED)

    assert disabled_brain.status == BrainStatus.DISABLED

    print("[PASS] ACTIVE -> DISABLED")

    # ---------------------------------------------------------
    # DISABLED is terminal
    # ---------------------------------------------------------

    expect_failure(
        lambda: disabled_brain.transition_to(BrainStatus.READY),
        "DISABLED -> READY is blocked",
    )

    expect_failure(
        lambda: disabled_brain.transition_to(BrainStatus.ACTIVE),
        "DISABLED -> ACTIVE is blocked",
    )

    expect_failure(
        lambda: disabled_brain.transition_to(BrainStatus.PAUSED),
        "DISABLED -> PAUSED is blocked",
    )

    # ---------------------------------------------------------
    # Invalid initial transitions
    # ---------------------------------------------------------

    invalid_registered = make_brain(
        "Invalid Registered Test Brain",
        BrainRole.INTERNAL_ARMY,
        mother.brain_id,
    )

    expect_failure(
        lambda: invalid_registered.transition_to(BrainStatus.ACTIVE),
        "REGISTERED -> ACTIVE is blocked",
    )

    expect_failure(
        lambda: invalid_registered.transition_to(BrainStatus.PAUSED),
        "REGISTERED -> PAUSED is blocked",
    )

    expect_failure(
        lambda: invalid_registered.transition_to(BrainStatus.DISABLED),
        "REGISTERED -> DISABLED is blocked",
    )

    # ---------------------------------------------------------
    # READY invalid transitions
    # ---------------------------------------------------------

    invalid_ready = make_brain(
        "Invalid Ready Test Brain",
        BrainRole.INTERNAL_ARMY,
        mother.brain_id,
    )
    invalid_ready.transition_to(BrainStatus.READY)

    expect_failure(
        lambda: invalid_ready.transition_to(BrainStatus.PAUSED),
        "READY -> PAUSED is blocked",
    )

    # ---------------------------------------------------------
    # ACTIVE invalid transition
    # ---------------------------------------------------------

    invalid_active = make_brain(
        "Invalid Active Test Brain",
        BrainRole.INTERNAL_ARMY,
        mother.brain_id,
    )
    invalid_active.transition_to(BrainStatus.READY)
    invalid_active.transition_to(BrainStatus.ACTIVE)

    expect_failure(
        lambda: invalid_active.transition_to(BrainStatus.REGISTERED),
        "ACTIVE -> REGISTERED is blocked",
    )

    # ---------------------------------------------------------
    # PAUSED cannot directly become ACTIVE
    # ---------------------------------------------------------

    paused_brain = make_brain(
        "Paused Transition Test Brain",
        BrainRole.INTERNAL_ARMY,
        mother.brain_id,
    )
    paused_brain.transition_to(BrainStatus.READY)
    paused_brain.transition_to(BrainStatus.ACTIVE)
    paused_brain.transition_to(BrainStatus.PAUSED)

    expect_failure(
        lambda: paused_brain.transition_to(BrainStatus.ACTIVE),
        "PAUSED -> ACTIVE direct transition is blocked",
    )

    # ---------------------------------------------------------
    # FAILED lifecycle
    # ---------------------------------------------------------

    failed_brain = make_brain(
        "Failed Lifecycle Test Brain",
        BrainRole.INTERNAL_ARMY,
        mother.brain_id,
    )
    failed_brain.transition_to(BrainStatus.READY)
    failed_brain.transition_to(BrainStatus.FAILED)

    assert failed_brain.status == BrainStatus.FAILED

    print("[PASS] READY -> FAILED")

    expect_failure(
        lambda: failed_brain.transition_to(BrainStatus.ACTIVE),
        "FAILED -> ACTIVE direct transition is blocked",
    )

    failed_brain.transition_to(BrainStatus.READY)

    assert failed_brain.status == BrainStatus.READY

    print("[PASS] FAILED -> READY recovery transition")

    # ---------------------------------------------------------
    # Hierarchy survives lifecycle changes
    # ---------------------------------------------------------

    mother.transition_to(BrainStatus.DISABLED)

    assert registry.get_mother_brain().brain_id == mother.brain_id
    print("[PASS] Mother Brain identity survives lifecycle state change")

    assert registry.get_parent(child.brain_id).brain_id == mother.brain_id
    print("[PASS] Child Brain parent identity survives lifecycle state change")

    assert registry.get_parent(child_army.brain_id).brain_id == child.brain_id
    print("[PASS] Child Internal Army parent identity survives lifecycle state change")

    assert registry.is_descendant(
        child_army.brain_id,
        mother.brain_id,
    )
    print("[PASS] Lifecycle state changes do not destroy hierarchy")

    # ---------------------------------------------------------
    # Registry identity remains separate from lifecycle
    # ---------------------------------------------------------

    assert registry.get(child.brain_id) is child
    assert registry.get(army.brain_id) is army

    print("[PASS] Registry identity remains intact across lifecycle states")

    # ---------------------------------------------------------
    # Final
    # ---------------------------------------------------------

    print("=" * 60)
    print("SAHIBEX 6L-4 BRAIN LIFECYCLE & STATE INTEGRITY TEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
