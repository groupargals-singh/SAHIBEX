from core.brain.background_worker_expansion import BackgroundWorkerManager, WorkerLifecycle

def main():
    m=BackgroundWorkerManager(max_workers=2)
    r=m.register("w1", lambda x: x+1, job_id="job1")
    assert r.lifecycle == WorkerLifecycle.READY
    out=m.run("w1", 4); assert out.success and out.output==5
    assert len(m.history("w1")) == 1
    m.pause("w1"); assert not m.run("w1", 1).success
    m.resume("w1"); m.checkpoint("w1", {"cursor": 7, "token": "hidden"})
    assert m.restore_checkpoint("w1") == {"cursor": 7}
    m.stop("w1"); assert not m.run("w1", 1).success
    assert not m.grants_permission() and not m.executes_protected_actions() and not m.can_bypass_authority()
    print("SAHIBEX 6P-8 BACKGROUND WORKERS TEST: PASS")

if __name__ == "__main__": main()
