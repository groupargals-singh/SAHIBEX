# P5 — Commander Brain and Worker Brain Data-Flow Audit
Date: 2026-10-17
Workspace: `~/SAHIBEX`
Status: **AUDIT COMPLETE; ACCEPTANCE NOT PASSED**

## Scope and PASS gate
Commander divides work, workers return results, child identity survives restart, memory remains isolated, multi-step task acceptance goes through the real Main Brain entry point, and authority/permission boundaries remain intact.

## Verified facts
- `MasterBrain` constructs `SpecialistChildBrainManager()` without a persistent registry argument (`core/brain/master_brain.py`).
- `SpecialistChildBrainManager` stores live child records in process-local `self._records`; `get()` and `list_children()` read only that dictionary. The child memory is constructed as `ChildMemoryRuntime(...)` with in-process dictionaries.
- `ChildInstanceRegistry` independently supports SQLite identity/lifecycle/trust persistence, hash-chain integrity, and restore via a new registry instance. It is not wired into `SpecialistChildBrainManager` or the Main Brain's default runtime.
- `ChildWorkerCoordinator` holds tasks in a process-local dictionary and is not a durable task queue.
- `ResearchLearningCommander.dispatch()` records Army and Labour assignment events but invokes a single supplied callable (`worker()`); it does not itself invoke two independent worker handlers or aggregate worker results.
- `InternalBrainTeam` handlers are registered in MainBrain, but these are in-process handlers and not independently deployed child-brain processes. Its dispatch contract correctly requires explicit authorization and request verification, and says handler output still needs task-appropriate verification.
- Existing child registry, memory boundary/runtime, coordinator, race, specialist child, department commander, Main Brain architecture, restart-recovery, end-to-end, and permission-boundary tests passed together: **37 passed in 5.89s**.

## Findings
1. **BLOCKER — persistent deployment is not wired into MainBrain.** Identity persistence exists as a separate component but the live child manager doesn't use it.
2. **BLOCKER — child memory is not durable across restart.** Memory is in dictionaries; namespace isolation is represented, but durable isolated memory restore is not implemented.
3. **BLOCKER — worker coordination isn't durable.** Task assignments live in memory only.
4. **BLOCKER — real commander-to-two-workers acceptance is missing.** Current commander traces Army/Labour assignment but calls only one injected worker callback. Existing tests cover trace/status contracts, not actual dual-worker result collection through a real Main Brain request.
5. **Security status — component boundary checks PASS, end-to-end deployment boundary is NOT YET PROVEN.** Existing checks prohibit child self-authorization, authority grants, Mother override and Constitution modification; protected execution remains with the Mother permission pipeline.

## Changes made
No runtime source code was changed during this audit. This is intentional: wiring persistence into lifecycle transitions without an atomic restore/rollback plan could create identity, trust, or authority inconsistencies. The test results are not being misrepresented as a full P5 PASS.

## Required implementation before P5 can pass
- Wire a durable child registry into the deployed Main Brain runtime with explicit lifecycle transitions and integrity verification.
- Persist child-owned memory in a child-scoped namespace; keep credentials isolated from ordinary memory and never persist secrets as plaintext.
- Restore child identity after restart in a safe non-executing state; require fresh verification/authorization before dispatch resumes. Runtime handlers must be explicitly rebound and never inferred from persisted identity alone.
- Add durable worker-task state or explicitly constrain it to restart-lost ephemeral tasks.
- Add a real multi-step acceptance test: Mother receives a task, assigns distinct Army and Labour work, collects both outputs, verifies evidence/results, rejects inconsistent or missing worker output, and confirms no worker can self-authorize protected actions.
- Run focused regressions and full suite after implementation.

## Verdict
**P5 / Main Brain data-flow item 24: BLOCKED (not PASS).** Component tests pass, but the specified deployment and multi-step acceptance gate does not yet pass.

## Update after partial implementation — 2026-10-17
A durable-memory primitive has now been added in `core/brain/child_memory_runtime.py` (opt-in SQLite storage for ordinary JSON-serializable values) and tested by `tests/unit/test_child_memory_persistence.py`. It verifies restart recovery and child/namespace isolation; credential memory remains non-persistent rather than being stored in plaintext.
Focused verification after this change: 38 passed in 6.66s; compileall and diff-check passed. Full regression is running.
This does not close P5: the primitive is not wired into the default Main Brain manager, persistent child identity is not integrated, and actual dual-worker orchestration remains unimplemented. Final verdict remains BLOCKED until those gates pass.

## Implementation update — 2026-10-17

The P5 blockers were addressed with a restart-safe, fail-closed integration:

- ChildInstanceRegistry.list_children() now enumerates integrity-checked persisted child identities.
- SpecialistChildBrainManager accepts an identity database path, persists birth/lifecycle/trust events through the hash-chain registry, and uses a separate SQLite file for ordinary child memory. Credentials remain memory-only and are not written to the ordinary-memory database.
- Restore rehydrates identity and child-scoped memory but deliberately forces runtime state to PAUSED and trust to UNVERIFIED. No callable handler is restored. Dispatch is blocked until fresh approval/verification and explicit handler re-registration.
- MasterBrain accepts SAHIBEX_CHILD_REGISTRY_DB and SAHIBEX_CHILD_MEMORY_DB. scripts/start_sahibex_live.sh now supplies safe defaults under data/runtime/ while allowing an operator override.
- ResearchLearningCommander.dispatch_workers() executes two distinct Army/Labour callbacks, collects both outputs and requires an explicit joint verifier. Missing or conflicting outputs become UNVERIFIED, not success. MasterBrain.dispatch_worker_team() exposes this internal orchestration path without giving workers constitutional/tool authority.
- Task traces and coordinator assignments remain request-scoped and in-memory; interrupted tasks are not resumed after process restart. This is intentionally fail-closed, not durable queue recovery.

Focused P5 verification after these changes: 48 passed in 16.48s across specialist lifecycle, child-memory persistence, child registry integrity, commander/dual-worker execution, worker coordinator/race, Main Brain, restart-recovery and permission-boundary tests. Compile checks passed. Full regression is running; final status will be recorded after its actual result and git diff --check.


## Final P5 acceptance result — 2026-10-17

### Verified implementation
- The live-start script wires the Main Brain to durable child identity and memory databases using environment-configurable paths.
- Startup verifies the persistent child registry hash chain before restoring any child. Tampered identity state fails closed.
- Child identity and ordinary child-owned memory survive a new manager/Main Brain runtime. Restore forces PAUSED + UNVERIFIED, does not restore handlers, and blocks dispatch until fresh approval/verification and explicit handler rebinding.
- A routing defect was found and fixed: SpecialistChildBrainManager now dispatches to the requested target child ID instead of letting the general selector choose another child with the same specialization. This prevents Army/Labour work from accidentally reaching the same handler.
- MainBrain.dispatch_worker_team() now takes two distinct registered child IDs, requires Mother and human approval, invokes the actual child handlers with role-specific subtask prompts, and passes both outputs to a joint verifier. Missing or inconsistent output remains UNVERIFIED. The worker boundary does not grant constitutional or protected-tool authority.
- Task traces and coordinator assignments remain ephemeral/in-memory. An interrupted task is not resumed automatically after restart. Child identity/memory persist; executable handlers do not.

### Final verification evidence
- Full repository regression: **1928 passed in 165.23s**, exit code 0.
- Final focused P5 regression: **39 passed in 4.21s**, exit code 0.
- Python compileall: PASS.
- git diff --check: PASS.
- Live environment wiring probe: PASS.
- Restart identity + memory restore + fail-closed trust probe: PASS.
- Tampered child registry rejection test: PASS.
- Real MainBrain -> two registered child handlers -> joint verification test: PASS.
- Approval gate and Mother-only protected authority boundary tests: PASS.

### Verdict
**P5 / Master checklist item 24: PASS (managed in-process child runtime).** The requested acceptance gate passed. This does not claim separate operating-system processes or independent model instances: the Army and Labour children are distinct registered child identities/handlers in the same Main Brain process. Restarted children intentionally require handler rebinding and fresh verification; pending tasks are not automatically resumed.
