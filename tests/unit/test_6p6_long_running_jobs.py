from core.agent.long_running_jobs import LongRunningJobManager, LongRunningJobStatus

m = LongRunningJobManager()
j = m.create("job-1", "long running objective", "runtime-1")
assert j.status == LongRunningJobStatus.CREATED.value
m.start("job-1")
m.checkpoint("job-1", {"step": 3, "token": "must-not-transfer"})
cp = m.checkpoint_for("job-1")
assert cp.state == {"step": 3}
m.pause("job-1")
m.resume("job-1")
m.complete("job-1")
assert m.get("job-1").status == LongRunningJobStatus.COMPLETED.value
assert len(m.history("job-1")) >= 5
assert m.grants_permission() is False
assert m.executes_protected_actions() is False
try:
    m.start("job-1")
except RuntimeError:
    pass
else:
    raise AssertionError("terminal job restarted")
print("SAHIBEX 6P-6 LONG-RUNNING JOBS TEST: PASS")
