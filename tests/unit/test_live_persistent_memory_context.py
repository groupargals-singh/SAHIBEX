from __future__ import annotations

from core.brain.master_brain import MasterBrain


def main() -> None:
    first = MasterBrain()
    first.memory_brain.remember(
        content="User preference: the private project codename is ORBITAL_FALCON.",
        memory_type="user_context",
        source="test",
        importance=0.9,
        confidence=1.0,
        tags=["preference", "project", "codename"],
    )

    second = MasterBrain()
    retrieved = second.memory_brain.retrieve(
        "What is my project codename?"
    )
    assert retrieved
    assert any(
        "ORBITAL_FALCON" in item.content
        for item in retrieved
    )

    result = second.mother_operational.process_approved_request(
        objective="What is my project codename?",
        intent="general_request",
    )
    # A narrow, high-confidence user-context recall should be answered
    # directly from persistent memory without relying on the mock model.
    assert result.success is True
    assert result.verification_status == "MEMORY_RECALLED"
    assert "ORBITAL_FALCON" in result.response

    print("SAHIBEX LIVE PERSISTENT MEMORY CONTEXT TEST: PASS")


if __name__ == "__main__":
    main()
