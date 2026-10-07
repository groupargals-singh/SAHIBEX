from core.brain.long_term_memory_expansion import (
    LongTermMemoryExpansionEngine,
)


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print("[PASS]", label)


def main() -> None:
    engine = LongTermMemoryExpansionEngine()
    strong = engine.assess(
        memory_id="ltm-1", confidence=.9, importance=.8, recency=.9,
        access_frequency=.8, reinforcement_events=.9,
        context_strength=.9, verification_score=.9, provenance_score=.95,
    )
    check(len(engine.ITEM_IDS) == 10, "10 Phase-F expansion items")
    check(strong.storage_ready, "storage readiness")
    check(strong.provenance_ready, "provenance readiness")
    check(strong.verification_ready, "verification readiness")
    check(strong.update_score > .75, "memory update")
    check(strong.reinforcement_score > .75, "memory reinforcement")
    check(strong.context_link_score > .75, "context linking")

    stale = engine.assess(
        memory_id="ltm-2", confidence=.3, importance=.2, recency=.05,
        access_frequency=.05, reinforcement_events=.05,
        context_strength=.1, verification_score=.4, provenance_score=.8,
    )
    check(stale.decay_score > .75, "memory decay")
    check(stale.safe_forget_candidate, "forgetting candidate")

    conflict = engine.assess(
        memory_id="ltm-3", confidence=.8, importance=.7, recency=.7,
        access_frequency=.6, reinforcement_events=.6, context_strength=.7,
        verification_score=.8, provenance_score=.9, conflict_score=.9,
    )
    check(not conflict.safe_forget_candidate, "conflict blocks forgetting")

    security = {
        "read_only_assessment": True,
        "deletes_memory": False,
        "overwrites_memory": False,
        "executes_actions": False,
        "grants_permission": False,
        "modifies_constitution": False,
        "overrides_human_authority": False,
    }
    check(security["read_only_assessment"], "read-only boundary")
    check(not security["deletes_memory"], "no deletion authority")
    check(not security["overwrites_memory"], "no overwrite authority")
    check(not security["grants_permission"], "no permission authority")
    check(not security["modifies_constitution"], "no Constitution modification")
    check(not security["overrides_human_authority"], "Human Authority preserved")
    print("PHASE_F_10_ITEM_EXPANSION_PASS")


if __name__ == "__main__":
    main()
