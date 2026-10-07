from datetime import datetime, timezone

from core.research.decision_memory import (
    DECISION_MEMORY_VERSION,
    DecisionMemory,
    DecisionMemoryStore,
)


def make_decision(
    decision_id: str,
    decision: str,
    selected_option: str,
    success_score: float,
    importance: float = 0.5,
    confidence: float = 0.5,
    tags=None,
    decided_at=None,
):
    options = [
        "option_a",
        "option_b",
        "option_c",
    ]

    return DecisionMemory(
        decision_id=decision_id,
        decision=decision,
        context="SAHIBEX decision test context",
        options=options,
        selected_option=selected_option,
        decision_basis="test reasoning and evidence",
        expected_outcome="expected successful result",
        actual_outcome="actual observed result",
        lesson="test lesson learned",
        source="unit_test",
        confidence=confidence,
        importance=importance,
        success_score=success_score,
        provenance={
            "test": True,
            "source": "unit_test",
        },
        tags=tags or [],
        decided_at=decided_at or datetime.now(timezone.utc),
    )


def main():
    # ---------------------------------------------------------
    # 1. Decision object contract
    # ---------------------------------------------------------
    decision_1 = make_decision(
        "decision-1",
        "choose option a",
        "option_a",
        success_score=0.90,
        importance=0.80,
        confidence=0.95,
        tags=["coding", "success"],
    )

    assert decision_1.decision_id == "decision-1"
    assert decision_1.decision == "choose option a"
    assert decision_1.context
    assert decision_1.options == ["option_a", "option_b", "option_c"]
    assert decision_1.selected_option == "option_a"
    assert decision_1.decision_basis
    assert decision_1.expected_outcome
    assert decision_1.actual_outcome
    assert decision_1.lesson
    assert decision_1.source == "unit_test"
    assert decision_1.confidence == 0.95
    assert decision_1.importance == 0.80
    assert decision_1.success_score == 0.90
    assert decision_1.provenance["test"] is True
    assert "coding" in decision_1.tags

    # Immutable object
    try:
        decision_1.decision = "modified"
        raise AssertionError("DecisionMemory must be immutable")
    except (AttributeError, TypeError):
        pass

    # ---------------------------------------------------------
    # 2. Store
    # ---------------------------------------------------------
    store = DecisionMemoryStore(capacity=3)

    store.store(decision_1)

    decision_2 = make_decision(
        "decision-2",
        "choose option b",
        "option_b",
        success_score=0.60,
        importance=0.50,
        confidence=0.70,
        tags=["research"],
    )

    decision_3 = make_decision(
        "decision-3",
        "choose option c",
        "option_c",
        success_score=0.30,
        importance=0.40,
        confidence=0.60,
        tags=["failure"],
    )

    store.store(decision_2)
    store.store(decision_3)

    assert store.count() == 3
    assert store.contains("decision-1")
    assert store.contains("decision-2")
    assert store.contains("decision-3")

    # ---------------------------------------------------------
    # 3. Get
    # ---------------------------------------------------------
    assert store.get("decision-1") is decision_1
    assert store.get("missing") is None

    # ---------------------------------------------------------
    # 4. Duplicate protection
    # ---------------------------------------------------------
    try:
        store.store(decision_1)
        raise AssertionError("Duplicate decision ID must be rejected")
    except ValueError:
        pass

    # ---------------------------------------------------------
    # 5. Success retrieval
    # ---------------------------------------------------------
    successful = store.by_success(0.70)

    assert len(successful) == 1
    assert successful[0].decision_id == "decision-1"

    all_success = store.by_success(0.0)

    assert len(all_success) == 3
    assert all_success[0].decision_id == "decision-1"

    # ---------------------------------------------------------
    # 6. Tag retrieval
    # ---------------------------------------------------------
    coding = store.by_tag("CODING")

    assert len(coding) == 1
    assert coding[0].decision_id == "decision-1"

    research = store.by_tag("research")

    assert len(research) == 1
    assert research[0].decision_id == "decision-2"

    # ---------------------------------------------------------
    # 7. Search
    # ---------------------------------------------------------
    result = store.search("option b")

    assert len(result) == 1
    assert result[0].decision_id == "decision-2"

    result = store.search("lesson learned")

    assert len(result) == 3

    result = store.search("nonexistent-query")

    assert result == ()

    # Empty search
    assert store.search("") == ()

    # ---------------------------------------------------------
    # 8. Lessons
    # ---------------------------------------------------------
    lessons = store.lessons()

    assert len(lessons) == 3
    assert all(isinstance(item, str) for item in lessons)

    # ---------------------------------------------------------
    # 9. Selected option retrieval
    # ---------------------------------------------------------
    selected = store.selected_options()

    assert len(selected) == 3
    assert "option_a" in selected
    assert "option_b" in selected
    assert "option_c" in selected

    # ---------------------------------------------------------
    # 10. Recent
    # ---------------------------------------------------------
    recent = store.recent(2)

    assert len(recent) == 2

    recent_zero = store.recent(0)

    assert recent_zero == ()

    # ---------------------------------------------------------
    # 11. All
    # ---------------------------------------------------------
    all_decisions = store.all()

    assert len(all_decisions) == 3
    assert all(
        isinstance(item, DecisionMemory)
        for item in all_decisions
    )

    # ---------------------------------------------------------
    # 12. Summary
    # ---------------------------------------------------------
    summary = store.summary()

    assert summary["version"] == DECISION_MEMORY_VERSION
    assert summary["capacity"] == 3
    assert summary["decision_count"] == 3
    assert summary["immutable_decision_objects"] is True
    assert summary["preserves_options"] is True
    assert summary["preserves_selected_option"] is True
    assert summary["preserves_decision_basis"] is True
    assert summary["preserves_expected_outcome"] is True
    assert summary["preserves_actual_outcome"] is True
    assert summary["preserves_lesson"] is True
    assert summary["preserves_provenance"] is True
    assert summary["supports_success_retrieval"] is True
    assert summary["supports_decision_search"] is True
    assert summary["supports_lesson_retrieval"] is True
    assert summary["supports_selected_option_retrieval"] is True

    # Security boundary
    assert summary["execution_authority"] is False
    assert summary["grants_permission"] is False
    assert summary["executes_actions"] is False
    assert summary["modifies_constitution"] is False

    # ---------------------------------------------------------
    # 13. Capacity eviction
    # ---------------------------------------------------------
    eviction_store = DecisionMemoryStore(capacity=2)

    old_time = datetime(
        2020,
        1,
        1,
        tzinfo=timezone.utc,
    )

    old_1 = make_decision(
        "old-1",
        "old decision one",
        "option_a",
        success_score=0.50,
        decided_at=old_time,
    )

    old_2 = make_decision(
        "old-2",
        "old decision two",
        "option_b",
        success_score=0.50,
        decided_at=old_time,
    )

    new_1 = make_decision(
        "new-1",
        "new decision",
        "option_c",
        success_score=0.80,
        decided_at=datetime(
            2021,
            1,
            1,
            tzinfo=timezone.utc,
        ),
    )

    eviction_store.store(old_1)
    eviction_store.store(old_2)
    eviction_store.store(new_1)

    assert eviction_store.count() == 2
    assert not eviction_store.contains("old-1")
    assert eviction_store.contains("old-2")
    assert eviction_store.contains("new-1")

    # ---------------------------------------------------------
    # 14. Remove
    # ---------------------------------------------------------
    removed = eviction_store.remove("old-2")

    assert removed is old_2
    assert eviction_store.get("old-2") is None
    assert eviction_store.count() == 1

    # Missing remove
    assert eviction_store.remove("missing") is None

    # ---------------------------------------------------------
    # 15. Clear
    # ---------------------------------------------------------
    eviction_store.clear()

    assert eviction_store.count() == 0
    assert eviction_store.all() == ()

    # ---------------------------------------------------------
    # 16. Invalid success threshold
    # ---------------------------------------------------------
    try:
        store.by_success(1.5)
        raise AssertionError("Invalid success threshold must fail")
    except ValueError:
        pass

    # ---------------------------------------------------------
    # 17. Invalid recent limit
    # ---------------------------------------------------------
    try:
        store.recent(-1)
        raise AssertionError("Negative recent limit must fail")
    except ValueError:
        pass

    # ---------------------------------------------------------
    # 18. Type safety
    # ---------------------------------------------------------
    try:
        store.store("not-a-decision")
        raise AssertionError("Invalid decision object must fail")
    except TypeError:
        pass

    print("SAHIBEX PHASE 2 #51 DECISION MEMORY TEST: PASS")


if __name__ == "__main__":
    main()
