from core.brain.child_genesis_expansion import ChildGenesisExpansion, PHASE_P_VERSION
engine = ChildGenesisExpansion()
assert PHASE_P_VERSION == "PHASE-P-CHILD-GENESIS-1"
r = engine.assess()
assert len(r.scores) == 28 and r.ready
assert not engine.assess(**{"P-11": 0.5}).ready
s = engine.security_summary()
assert s["read_only"] is True
assert all(s[k] is False for k in ("executes_actions", "grants_permission", "modifies_constitution", "overrides_human_authority"))
print("SAHIBEX PHASE P CHILD GENESIS EXPANSION TEST: PASS")
