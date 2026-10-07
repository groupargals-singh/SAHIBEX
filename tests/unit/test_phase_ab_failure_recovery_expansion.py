from core.brain.failure_recovery_expansion import FailureRecoveryEngine

def main():
 e=FailureRecoveryEngine(); r=e.detect("f1","tool","executor","high","tool failed")
 assert e.classify(r)==("tool","high") and e.contain(r)
 assert e.can_retry(r,0,2) and not e.can_retry(r,2,2)
 assert e.recover(r,verified=True)
 assert not e.recover(r,verified=False)
 assert e.rollback(authorized=True,verified=True)
 assert not e.rollback(authorized=False,verified=True)
 assert e.resume(checkpoint_available=True,verified=True)
 assert not e.resume(checkpoint_available=False,verified=True)
 assert not e.grants_permission() and not e.executes_protected_actions()
 print("SAHIBEX PHASE AB FAILURE/RECOVERY EXPANSION TEST: PASS")
if __name__=="__main__": main()
