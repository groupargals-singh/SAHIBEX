from core.brain.sleep_consolidation_expansion import SleepConsolidationExpansion, PHASE_N_VERSION

engine = SleepConsolidationExpansion()
assert PHASE_N_VERSION == "PHASE-N-SLEEP-CONSOLIDATION-1"
result = engine.assess()
assert len(result.scores) == 12
assert result.ready is True
assert all(v >= 0.8 for v in result.scores.values())
blocked = engine.assess(memory_ready=False)
assert blocked.ready is False
security = engine.security_summary()
assert security["read_only"] is True
assert security["executes_actions"] is False
assert security["grants_permission"] is False
assert security["modifies_constitution"] is False
assert security["overrides_human_authority"] is False
print("SAHIBEX PHASE N SLEEP/CONSOLIDATION EXPANSION TEST: PASS")
