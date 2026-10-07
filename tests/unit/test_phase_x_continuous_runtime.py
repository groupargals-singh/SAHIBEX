from core.brain.continuous_runtime import ContinuousRuntime, RuntimeCheckpointStore
from core.brain.background_worker_orchestrator import BackgroundWorkerOrchestrator, WorkerStatus
from core.brain.runtime_continuity import RuntimeContinuityBridge

r=ContinuousRuntime('x1'); r.start(); r.update_state(task='research',step=2); cp=r.checkpoint(); store=RuntimeCheckpointStore(); store.save(cp); r.interrupt(); r.restore(store.load('x1')); assert r.status.value=='paused' and r.state()['step']==2
w=BackgroundWorkerOrchestrator(); w.register('w1',lambda x: x+1); out=w.run('w1',2); assert out.success and out.output==3 and w.status('w1')==WorkerStatus.IDLE
bridge=RuntimeContinuityBridge(); env=bridge.export('x1',cp.sequence,{'task':'research','token':'SECRET'},'phone','pc'); assert 'token' not in env.state and not bridge.transfers_authority() and not bridge.transfers_credentials()
assert not r.grants_permission() and not r.executes_protected_actions() and not w.can_bypass_authority()
print('SAHIBEX PHASE X CONTINUOUS RUNTIME TEST: PASS')
