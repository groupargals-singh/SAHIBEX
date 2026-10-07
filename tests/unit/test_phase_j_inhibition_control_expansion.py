from core.brain.inhibition_control_expansion import (
    PHASE_J_VERSION,
    InhibitionControlExpansion,
)


engine = InhibitionControlExpansion()
assert PHASE_J_VERSION == "PHASE-J-INHIBITION-1"

results = engine.assess()
assert len(results) == 11
assert [item.item_id for item in results] == [f"J-{i:02d}" for i in range(1, 12)]
assert all(not item.blocked for item in results)

blocked = engine.assess(
    impulse=True,
    unsafe=True,
    protected=True,
    high_risk=True,
    conflict=True,
    distracted=True,
    prompt_injection=True,
    permission_granted=False,
    emergency_stop=True,
    human_authorized=False,
    constitution_change=True,
)
assert len(blocked) == 11
assert blocked[1].blocked
assert blocked[2].blocked
assert blocked[3].blocked
assert blocked[4].blocked
assert blocked[5].blocked
assert blocked[6].blocked
assert blocked[7].blocked
assert blocked[8].blocked
assert blocked[9].blocked
assert blocked[10].blocked

approved = engine.assess(protected=True, permission_granted=True)
assert not approved[3].blocked
assert not approved[8].blocked

security = engine.security_summary()
assert security == {
    "read_only": True,
    "executes_actions": False,
    "grants_permission": False,
    "modifies_constitution": False,
    "overrides_human_authority": False,
}

print("SAHIBEX PHASE J INHIBITION CONTROL EXPANSION TEST: PASS")
