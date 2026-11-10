# SAHIBEX Brain Connection Registry
Date: 2026-11-01
Status: STATIC SOURCE REGISTRY — physical/runtime acceptance kept separate
Source of truth: existing E01–E19 audit plus this additive unresolved-edge register.

## Rules
- VERIFIED IN SOURCE means a source call/data relationship was found; it is not physical-device acceptance.
- RUNTIME VERIFIED requires a live path and observed outcome.
- NOT VERIFIED means no production call site or full transitive path was established in the bounded audit; it is not automatically a defect.
- PARTIAL means a bounded software path exists but required acceptance remains.
- Do not invent edges from architecture diagrams. Dashed/target edges remain proposed until source and runtime evidence exist.

## A. Primary request-path edges
The authoritative edge-by-edge source evidence is maintained in `docs/architecture/SAHIBEX_EDGE_BY_EDGE_CALL_PATH_AUDIT_2026-10-24.md`. Reuse its IDs; do not repeat the same static scan without a code change or reopen condition.

| Edge IDs | Connection | Current status | Limitation |
|---|---|---|---|
| E01–E03 | User/CLI → MasterBrain → fast paths and intent/action/risk classification | VERIFIED IN SOURCE | Fast paths may bypass later route stages |
| E04–E05 | Authority/permission/verification → allow or block | VERIFIED IN SOURCE | Verification is not execution |
| E06 | Memory/Knowledge retrieval → MotherDecisionContext | VERIFIED IN SOURCE | Query-scoped retrieval; not every answer route is identical |
| E07–E08 | MasterBrain → reasoning → orchestration/planning internal handlers | VERIFIED IN SOURCE | Internal handlers, not independent LLM processes |
| E09–E10 | MasterBrain → ToolBrain for protected/read operations | VERIFIED IN SOURCE | ToolBrain retains its own execution and permission boundaries |
| E11–E12 | MasterBrain → research/learning → verified result gates | VERIFIED IN SOURCE | Verified evidence and persistence flags required |
| E13 | MasterBrain → operational/coding route | VERIFIED IN SOURCE | Generated text is not automatically fact-verified |
| E14 | Worker team → registered child handlers | VERIFIED WITH GATES | Mother + human approval and joint verification required |
| E15–E16 | Branch result → response/context recording | VERIFIED IN SOURCE | Recording does not make every statement trusted knowledge |
| E17 | Companion microphone → ASR → MainBrain → audible TTS | NOT PHYSICALLY VERIFIED | P6 remains PARTIAL |
| E18 | Camera/image → semantic vision → grounded answer | PARTIAL / NOT E2E | OCR exists; semantic vision route/accuracy acceptance absent |
| E19 | Accessibility Companion → UI tree/actions/Emergency Stop | SOURCE PRESENT; PHYSICAL ACCEPTANCE PENDING | P8 remains PARTIAL/BLOCKED |

## B. Cross-cutting composition and control edges

| ID | From → To | Evidence / source anchor | Status and boundary |
|---|---|---|---|
| C01 | MasterBrain → ConfidenceVerificationBrain | `core/brain/master_brain.py`, `core/brain/confidence_verification_brain.py`; integration status report 2026-10-31 | COMPOSED; bounded ambiguity/trust gates PASS, broad multilingual calibration PARTIAL |
| C02 | MasterBrain → ThreeBrainCouncil | `core/brain/master_brain.py`, `core/brain/three_brain_council.py` | COMPOSED and invoked as advisory metadata; Council cannot grant authority or prove truth |
| C03 | MasterBrain → MemoryBrain / KnowledgeBrain / ResearchLearningBrain / ToolBrain / AutonomousWorkBrain / CognitiveNeuralArchitecture | MasterBrain constructor and existing source wiring checkpoint in adoption register | COMPOSED; branch-specific acceptance still applies |
| C04 | MasterBrain → InternalBrainTeam role handlers | AST checkpoint recorded in adoption register | 61 unique role IDs, zero duplicate IDs; production call sites found for reasoning, orchestration, research, learning and coding; registration alone does not prove automatic invocation |
| C05 | ResearchLearningCommander → Army/Labour worker dispatch | ResearchLearningBrain / worker dispatch checkpoint in adoption register | APPROVAL-GATED: Mother + human approval, distinct registered child IDs and joint verification |
| C06 | ToolBrain → EmergencyStop / PermissionGateway / authenticated PENDING intent / executor | `core/brain/tool_brain.py`, `emergency_stop.py`, permission/audit modules | PROTECTED PATH PRESENT; fail closed if pre-execution audit intent cannot be authenticated |
| C07 | ToolIntelligence → OperationalVerificationRecovery | `tools/intelligence.py` and verification-depth clarification in adoption register | Seven internal consistency/safety checks; does not prove external side-effect final state or factual correctness |
| C08 | ReasoningCoordinator / ConfidenceVerificationBrain → UncertaintyEngine | `core/brain/reasoning_coordinator.py`, `uncertainty.py`, confidence brain | COMPOSED in those bounded paths; probability calibration remains PARTIAL |
| C09 | MasterBrain → AttentionEngine | `core/brain/attention.py`, `tests/unit/test_attention_engine.py` | STANDALONE COMPONENT + TESTS; live MasterBrain composition/transitive runtime path NOT VERIFIED |
| C10 | MasterBrain/context → WorkingMemoryExpansionEngine | `core/brain/working_memory_expansion.py`, `core/research/working_memory.py` and tests | BOUNDED COMPONENTS + TESTS; full lifecycle/context integration NOT VERIFIED |
| C11 | Runtime idle scheduler → SleepConsolidationExpansion | `core/brain/sleep_consolidation_expansion.py`, `wake_sleep_state.py` and phase-N tests | COMPONENTS PRESENT; safe scheduled runtime acceptance PARTIAL |
| C12 | Runtime events → ObservabilityEngine | `core/brain/observability_expansion.py` and phase-Y tests | BOUNDED COLLECTOR; persistent correlated production traces/retention integration PARTIAL |
| C13 | Resource telemetry → planner/model router/worker scheduler | `core/brain/resource.py`, model gateway and worker resource boundaries | PARTIAL; existing task/load contracts do not prove live RAM/CPU/battery adaptive scheduling |
| C14 | RecoveryController → runtime supervisor / restore path | `core/brain/recovery_controller.py`, backup/recovery modules and tests | COMPONENTS + TESTS; physical process-kill/disk-full/restore drills remain pending |
| C15 | PersistentMemoryKnowledgeGraph / KnowledgeGraphStorage → production retrieval | `core/research/persistent_memory_knowledge_graph.py`, `knowledge_graph_storage.py`, dedicated tests | NOT VERIFIED in bounded production core/app call-site search; do not claim live GraphRAG |
| C16 | SahibexExecutionLoop → production MasterBrain runtime | `core/brain/sahibex_execution_loop.py`, tests and P2 acceptance script | NOT VERIFIED as a production composition path; not a confirmed defect |
| C17 | ModelGateway → operational generation/provider fallback | `core/model_gateway/router.py`, provider modules, MasterBrain operational integration | ROUTING COMPONENTS PRESENT; live local model may be offline/resource-blocked; no guard bypass |
| C18 | Companion Accessibility service → Termux bridge → approved Android action | Android Companion source, P8 status reports | SOFTWARE CONTRACT PRESENT; pairing, UI tree/action and persistent E-stop physical acceptance pending |

## C. Dependency and control-plane ordering
1. Input adapters must normalize/label untrusted input before intent interpretation.
2. Intent/action/risk classification must precede protected-action permission decisions.
3. Constitution, human authority, PermissionGateway and Emergency Stop dominate all planner, Council, worker and tool decisions.
4. Verification of a proposed action is distinct from executing it.
5. Tool execution requires permission/confirmation and authenticated PENDING audit intent before handler execution.
6. Post-execution checks must distinguish internal consistency from independent external outcome verification.
7. Memory/knowledge context must pass provenance and latest lifecycle verification before being treated as trusted.
8. Graph/vector retrieval must inherit the same verified-only filters; indexing must not bypass lifecycle policy.
9. Learning and sleep consolidation occur after result acceptance and must not promote unverified claims or make protected changes.
10. Resource limits and cancellation/Emergency Stop apply to background workers, model inference and child tasks.

## D. Reopen conditions
Revisit a connection only if:
- its source code changes;
- a new runtime/physical-device artifact is produced;
- a test fails or a regression is reported;
- a previously NOT VERIFIED edge gains a concrete production call site;
- a security, provenance or authority boundary is changed.
Otherwise reuse this registry and the E01–E19 audit; do not rerun duplicate scans.

## E. Current architecture conclusion
The primary MainBrain software route and major permission/worker/tool boundaries have source evidence. Several cognitive components exist as bounded standalone components but need transitive production composition evidence. Graph retrieval and SahibexExecutionLoop production composition remain NOT VERIFIED. Voice, semantic vision and Accessibility physical paths remain open. This registry is not a release certificate.


## 2026-11-01 — Phase 2 cognitive-loop integration update
- C09 updated: MasterBrain now instantiates and invokes the existing AttentionEngine through the common `_record_context` path. Its result is advisory metadata only; attention never gates execution or grants permission. Scores are deterministic heuristics, not calibrated probabilities.
- C10 clarified: the existing MemoryBrain-owned `core.research.working_memory.WorkingMemory` is the active bounded storage used by interaction memory; MasterBrain now exposes a read-only post-activation snapshot (capacity, count, top IDs). The separate `WorkingMemoryExpansionEngine` remains an assessment/coverage component, not a storage engine.
- Full-path input-understanding metadata propagation was fixed so the normal processing route passes `input_trace` into the common result/context recorder.
- Evidence: `docs/STATUS/PHASE2_COGNITIVE_LOOP_INTEGRATION_2026-11-01.md`; three new integration tests plus targeted regression suites PASS.


## 2026-11-01 — Phase 2 Task 2: Cognitive context data-flow update
- C09 remains composed: AttentionEngine is advisory only.
- C10 updated: the bounded active WorkingMemory snapshot is now included in MotherDecisionContext and passed into both Reasoning and Orchestration dispatches. Up to five items are carried with an explicit non-evidence label.
- C08/ReasoningCoordinator receives the context as reusable prior context; missing-information remains true, so this assessment cannot be treated as factual verification.
- Planner stores memory/knowledge/working-memory/retrieval references in plan metadata; no task execution or authority grant occurs.
- Runtime flow trace and tests verify both dispatches receive context, reasoning reuses it, planning retains references and authority remains unchanged.
- Evidence: docs/STATUS/PHASE2_COGNITIVE_LOOP_INTEGRATION_2026-11-01.md; focused expanded regression 25 passed.


## 2026-11-01 — Phase 2 Task 3: Durable goal continuity
- CheckpointResumeStore now supports durable, integrity-checked snapshots; sensitive nested fields are stripped and files are written atomically with 0600 permissions.
- AutonomousWorkBrain reloads checkpoint state across process construction; MasterBrain receives configured path; app/main.py configures the Termux runtime default.
- Restart recovery is explicit: a new run invocation with matching objective/job/runtime resumes verified completed steps; no startup auto-execution and no permission transfer.
- PASS scope is checkpoint continuity only. TaskManager graph and LongRunningJobManager lifecycle/history remain memory-only and are explicitly NOT claimed as durable.
- Evidence: docs/STATUS/PHASE2_COGNITIVE_LOOP_INTEGRATION_2026-11-01.md; focused regression 19 passed.


## Task 4 — Durable Task Graph and Job Lifecycle Recovery (2026-11-01)

**Status: PASS — bounded software recovery contract verified.**

- `TaskManager` now accepts the existing `ResearchStorage` persistence interface, restores full persisted Goals/Tasks on construction, and writes each graph as a single SQLite transaction (goal row plus task rows). Creation and cancellation persist immediately; autonomous execution persists state transitions and verified step outcomes.
- On process recreation, tasks left `RUNNING` are changed to `READY` with `metadata.recovered_after_restart=true`; this is a recoverable state only and does not execute work. Dependency links, parent IDs, priority, approval flag, retry counters, timestamps, result/error fields and metadata remain in the stored task graph.
- `LongRunningJobManager` now supports an optional atomic JSON lifecycle store with SHA-256 envelope integrity validation and mode 0600. It persists job records, sequence, checkpoints and history. A job found `RUNNING` after restart is converted to `PAUSED` with an interruption reason; terminal states remain terminal. Explicit `resume()` remains required.
- Normal runtime derives `*.state.sqlite3` and `*.jobs.json` beside the configured autonomous checkpoint file. Existing checkpoint persistence remains separate and unchanged.
- Tests: `PYTHONPATH=. pytest -q tests/unit/test_phase2_task_job_graph_recovery.py tests/unit/test_task_state.py tests/unit/test_task_dependencies.py tests/unit/test_task_persistence.py tests/unit/test_phase2_durable_goal_resume.py tests/unit/test_task34_persistence_restart_recovery.py tests/unit/test_task35_failure_recovery.py` — **10 passed**. `py_compile` and `git diff --check` — PASS. Full repository suite not run.
- Backups: `backups/phase2_cognitive_loop/task_state.py.pre_task_graph_20261101.bak` (SHA-256 `21c7d5ca03f05c4e61fe0ac95912654bee796de033a1785b367a0c52b958ebfc`); `long_running_jobs.py.pre_job_lifecycle_20261101.bak` (`fd0d983dd8a064ae0bec8a99a9470b660433be9d718252fac73435b9c8112d18`); `autonomous_work_brain.py.pre_task_job_recovery_20261101.bak` (`c17054fb218d5ce742bd80aaa14dd62496728f469e86cb0143b34a7c177329f2`).
- Limitations: physical phone kill/restart recovery was not exercised; full autonomous goal/plan reconstruction and callable/worker reattachment are not proven. Injected custom `TaskManager`/`LongRunningJobManager` instances retain their caller-defined persistence behavior. Full-suite regression remains pending.


## Task 5 — Full Autonomous Plan Reconstruction & Safe Resume (2026-11-01)

**Status: PASS — bounded plan/task reconstruction and explicit-resume contract verified.**

- Autonomous checkpoint records now carry a versioned-by-schema plan manifest: stable `plan_id`, plan version/reason, ordered decomposed goals with stable goal IDs, objective/intent/success criteria/dependencies, and the persisted TaskManager `task_goal_id`. Resume reconstructs the original `AgentPlan` rather than decomposing into fresh IDs.
- The persisted task Goal also carries an `autonomous_plan` manifest plus job/objective identity. This is a recovery fallback if the latest checkpoint file is missing, provided the durable task graph still exists. A mismatched/missing graph is fail-closed; no duplicate replacement plan is silently created.
- Recovery reconciles completed task states and task results with checkpoint progress. If task completion reached SQLite but the later checkpoint did not, the completed task is still recognized and not re-executed. Unfinished work remains eligible only after an explicit `run(...)` invocation supplies fresh execution and verification callbacks. No callbacks, tools, or protected actions are serialized or auto-invoked on startup.
- Checkpoint completion titles/results are no longer overwritten by an empty local list after resume. Job ID/objective/runtime identity and lifecycle validation remain enforced; terminal jobs require a new job ID.
- Planning graph persistence now sanitizes nested sensitive-key fields in task results and metadata before writing the durable graph, without mutating the in-memory task result.
- Tests: `PYTHONPATH=. pytest -q tests/unit/test_phase7_autonomous_work_brain.py tests/unit/test_phase2_durable_goal_resume.py tests/unit/test_phase2_task_job_graph_recovery.py tests/unit/test_task_state.py tests/unit/test_task_dependencies.py tests/unit/test_task_persistence.py tests/unit/test_task34_persistence_restart_recovery.py tests/unit/test_task35_failure_recovery.py` — **18 passed**. `py_compile` and `git diff --check` — PASS. Full repository suite not run.
- Backup: `backups/phase2_cognitive_loop/autonomous_work_brain.py.pre_plan_reconstruction_20261101.bak` (SHA-256 `a24830e2710ce30a4a628b02c3740c749c37b8970be1eec131e16cc985f652b0`).
- Limitations: physical Android force-stop/reboot validation remains pending. External `execute_step`/`verify_step` callables are intentionally not persisted; the caller must provide them again on explicit resume. Full-suite regression remains pending. No P6/P7/P8/P10/P11 gate was changed by this task.
