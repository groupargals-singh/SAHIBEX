from core.brain.audit_provenance_expansion import AuditProvenanceEngine

def main():
    e=AuditProvenanceEngine()
    payload={"decision":"allow","model":"test","tool":"read_file"}
    r=e.record("aa-1","root","decision",payload,{"evidence_ids":["ev-1"]})
    assert r.actor_id=="root" and r.event_type=="decision" and r.timestamp
    assert e.verify(r,payload)
    assert not e.tamper_detected(r,payload)
    assert e.tamper_detected(r,{"decision":"deny"})
    assert e.evidence_chain(r)==("ev-1",)
    assert e.authority_flags(r)=={"grants_permission":False,"is_authority":False}
    assert len(e.records())==1
    print("SAHIBEX PHASE AA AUDIT/PROVENANCE EXPANSION TEST: PASS")

if __name__=="__main__": main()
