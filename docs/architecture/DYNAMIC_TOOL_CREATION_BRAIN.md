# SAHIBEX Dynamic Tool Creation Brain

Status: integrated constrained implementation; full unit verification PASS on 2026-11-02.

## Complete supported lifecycle
1. Mother Brain can submit a bounded natural-language request or an exact declarative spec.
2. Deterministic request parsing supports only narrowly recognized local read-only intents. Ambiguous, mixed, protected or unsupported requests are rejected. Exact specs must contain only name, description and steps; each step must contain only operation and arguments.
3. Static validation enforces tool naming, description and step limits, operation/argument allowlists, type/range checks, project-root path containment and registry name uniqueness.
4. stage() persists STAGED/REJECTED candidates with canonical SHA-256 and lifecycle audit evidence. Staging never registers or activates a tool.
5. Mother Brain exposes the exact proposal (candidate ID, operations, arguments, digest, findings and approval requirement) for user review.
6. approve(candidate_id, user_approved=True) requires separate explicit human approval, optional canonical approval checker, revalidation and digest verification. Activation is read-only and atomic with persisted ACTIVE state and audit evidence.
7. Restart restores intact pending candidates as pending only; they cannot auto-activate. Only intact ACTIVE manifests are registered. Tampered, invalid or duplicate manifests are skipped.
8. rollback(candidate_id, user_approved=True) requires explicit human approval, removes only the registry entry owned by that candidate, persists ROLLED_BACK state and audit evidence.
9. Stage, activation and rollback fail closed when required audit/persistence fails; recovery attempts restore the prior manifest/registry state.

## Mother Brain integration
- MasterBrain.propose_dynamic_tool(request, context=...)
- MasterBrain.approve_dynamic_tool_candidate(candidate_id, user_approved=True)
- MasterBrain.rollback_dynamic_tool_candidate(candidate_id, user_approved=True)
- Existing web_tools internal role can handle context.action=propose_dynamic_tool after upstream authorization and verification gates. The proposal handler cannot approve or activate.
- No new internal role was added; the established 61-role architecture remains unchanged.
- ToolBrain accepts the same AuditLogger as Mother Brain and an injectable project root for isolated tests.

## Security boundary
- Only these existing read-only primitives are composable: list_directory, read_file, file_info, search_local_files.
- Generated Python, shell, imports, eval, exec, subprocess, network, credentials, writes, deletes, protected actions and permission grants are not supported.
- Runtime argument overrides are rejected.
- This is a constrained in-process declarative interpreter, not an OS-level sandbox for arbitrary code. Arbitrary code execution remains intentionally disabled.

## Verification
Full unit suite: .venv/bin/python -m pytest -q tests/unit
**2019 passed in 117.53s**
Focused integration/regression suite (Dynamic Tool Creation, Mother Brain, Tool Brain, registry, executor, permissions, protected actions, role counts and diagnostics): **162 passed in 12.84s**.
compileall passed for modified Python modules. git diff --check passed.
Full unit suite includes the fixed 61-role count and Android companion diagnostics checks.

## Boundaries not claimed
- This is a complete implementation of the currently supported safe declarative dynamic-tool feature.
- Arbitrary generated code tools and OS-level arbitrary-code sandboxing are not part of the feature and remain disabled by design.
- Physical Android microphone/camera/accessibility hardware gates are separate SAHIBEX release gates.
## Six-phase hardening and capability expansion (2026-11-08)

### Phase 1 — Hardened specification
- DynamicToolSpec.steps accepts a list at the public construction boundary and normalizes it to a tuple; invalid step elements are rejected.
- DynamicToolStep copies caller-owned argument dictionaries to prevent later mutation of the original input from changing the proposal.
- Validation now checks operation types, argument-key types, required arguments and bounded read_file.max_bytes.
- Non-JSON specifications fail with a controlled ValueError rather than failing during manifest serialization.

### Phase 2 — Tool designer
- Added design_report() for a bounded design/proposal summary, candidate ID, digest, findings and explicit approval boundary.
- Existing natural-language parser remains deterministic and narrow; unsupported or mixed intents are rejected. It is not a general autonomous LLM code generator.

### Phase 3 — Testing and verification
- Added verify_candidate() for static digest, schema and read-only primitive checks. It does not execute candidate operations.
- Added regression tests for list normalization, invalid elements, required arguments, and the real read_file(max_bytes=...) primitive signature.

### Phase 4 — Bounded builder / execution boundary
- Execution remains a declarative interpreter over the four allowlisted read-only primitives.
- Added a 64,000-byte aggregate result budget; read_file is capped at 20,000 bytes and search results at 100.
- Arbitrary generated code and OS-level sandbox execution remain disabled. These controls do not constitute an OS sandbox.

### Phase 5 — Lifecycle diagnostics
- Added lifecycle_status() reporting candidate counts, active names, allowed operations and explicit disabled capabilities.
- Approval, audit, persistence and rollback remain separate lifecycle gates.

### Phase 6 — Mother Brain integration
- Existing Mother Brain proposal/approval/rollback APIs and the authorization/verification-gated internal proposal route remain the integration boundary.
- Fixed a rejection-path bug that referenced an unassigned candidate when proposal parsing failed; rejected proposals now correctly report tool_activated: false.

### Verification update
- Focused Dynamic Tool Creation + Mother Brain tests: 34 passed (2026-11-08).
- Full project suite and physical Android hardware gates have not been re-run or certified by this update.
- Mother Brain now also exposes `design_dynamic_tool()`, `verify_dynamic_tool_candidate()` and `dynamic_tool_creation_status()`; verification is static and never executes candidate operations.
- Additional Mother Brain integration tests cover these diagnostics and the rejected-proposal error path.
- Full unit suite after the final Mother Brain API additions: **2030 passed in 95.50s** (2026-11-08).
- `compileall` and `git diff --check` passed after implementation.

## Extended completion work — 2026-11-08

- Added lifecycle locking around stage, approve and rollback so concurrent approvals cannot activate the same candidate twice.
- Prevented duplicate tool names while an earlier candidate is still staged.
- Hardened manifest restoration with size limits, UUID/filename consistency, schema bounds, timestamp bounds, and duplicate active-name checks.
- Dynamic list-directory operations now cap output at 500 entries.
- Dynamic search now scans at most 500 files and skips files larger than 256 KB; it no longer calls the unbounded general-purpose search primitive.
- Added a soft 5-second execution deadline checked between steps and after each primitive, 20 KB read cap, 64 KB aggregate output cap, and a 500-candidate lifecycle cap.
- Added per-tool call/success/failure/duration diagnostics.
- These are application-level budgets, not a hard OS process timeout or kernel sandbox. Since primitive calls are synchronous, a single slow filesystem call cannot be preempted by the soft deadline.
- Full arbitrary Python generation remains deliberately disabled; the builder composes declarative read-only operations only.
- Additional focused suite: 44 tests expected after final run; full regression pending.
- Final full unit regression after extended hardening: **2038 passed in 110.76s** (2026-11-08).
- Final focused Dynamic Tool Creation + Mother Brain suite: **44 passed**.
- Compile checks and `git diff --check` passed after the code changes.
