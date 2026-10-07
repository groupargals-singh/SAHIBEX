from core.brain.computational_state_expansion import ComputationalStateExpansion, PHASE_O_VERSION
engine = ComputationalStateExpansion()
assert PHASE_O_VERSION == "PHASE-O-COMPUTATIONAL-STATE-1"
r = engine.assess()
assert len(r.scores) == 10 and r.ready
assert not engine.assess(task=False).ready
s = engine.security_summary()
assert all(s[k] is False for k in ("executes_actions", "grants_permission", "modifies_constitution", "overrides_human_authority"))
assert s["read_only"] is True
print("SAHIBEX PHASE O COMPUTATIONAL STATE EXPANSION TEST: PASS")
