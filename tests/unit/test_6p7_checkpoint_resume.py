from core.agent.checkpoint_resume import CheckpointResumeStore

s = CheckpointResumeStore()
r = s.save("job-7", "runtime-7", 4, {"step": 4, "token": "SECRET", "task": "research"})
assert r.state == {"step": 4, "task": "research"}
assert s.verify(r)
assert s.resume_state("job-7", runtime_id="runtime-7") == r.state
assert not s.validate_resume(r, job_id="other", runtime_id="runtime-7")

snapshot = s.export_snapshot()
s2 = CheckpointResumeStore()
s2.import_snapshot(snapshot)
assert s2.resume_state("job-7", runtime_id="runtime-7")["step"] == 4

bad = dict(snapshot[0])
bad["state"] = {"step": 999}
try:
    CheckpointResumeStore().import_snapshot([bad])
except ValueError:
    pass
else:
    raise AssertionError("corrupted checkpoint accepted")

bad_identity = s.load("job-7")
try:
    s.resume_state("job-7", runtime_id="runtime-other")
except ValueError:
    pass
else:
    raise AssertionError("wrong runtime resumed checkpoint")

assert s.grants_permission() is False
assert s.executes_protected_actions() is False
print("SAHIBEX 6P-7 CHECKPOINT & RESUME TEST: PASS")
