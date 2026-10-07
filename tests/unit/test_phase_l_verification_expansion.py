from core.brain.verification_expansion import PHASE_L_VERSION, VerificationExpansion

engine = VerificationExpansion()
assert PHASE_L_VERSION == "PHASE-L-VERIFICATION-1"

results = engine.assess()
assert len(results) == 14
assert [x.item_id for x in results] == [f"L-{i:02d}" for i in range(1, 15)]
assert all(x.passed for x in results)

failed = engine.assess(
    result_available=False,
    fact_checked=False,
    source_checked=False,
    evidence_available=False,
    confidence_available=False,
    conflict_checked=False,
    conflict_resolved=False,
    multi_source_checked=False,
    consistency_checked=False,
    execution_verified=False,
    trust_integrated=False,
    failure_handled=False,
    provenance_available=False,
)
assert failed[0].passed
assert all(not x.passed for x in failed[1:])

security = engine.security_summary()
assert security["read_only"] is True
assert security["executes_actions"] is False
assert security["grants_permission"] is False
assert security["modifies_constitution"] is False
assert security["overrides_human_authority"] is False

print("SAHIBEX PHASE L VERIFICATION EXPANSION TEST: PASS")
