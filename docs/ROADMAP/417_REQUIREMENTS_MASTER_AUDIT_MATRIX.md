# SAHIBEX — 417 Requirements Master Audit Matrix
Date: 2026-10-08
Status: ACTIVE AUDIT BASELINE

## Audit rule
The historical baseline is documented as 417 items across Phase A–AC (29 phase labels), but the exact original 417-item source is not currently recoverable from the repository/Git history. Therefore no requirement name is invented and no missing item is marked complete by assumption.

Status meanings:
- VERIFIED: implementation + relevant test/evidence is present
- NEEDS-RECONCILIATION: original specification/item mapping is unavailable
- PARTIAL/PENDING: implementation exists but dedicated final evidence is still required

## A–AC checkpoint matrix

| Phase | Checkpoint | Current status | Evidence / test family | Remaining audit action |
|---|---|---|---|---|
| A | Brain foundation | VERIFIED | Phase/brain foundation tests | Recover exact original A items and map individually |
| B | Input validation / sensory coverage | VERIFIED | docs/PHASE_B_SENSORY_INPUT_COVERAGE.md + tests | Recover exact original B items and map individually |
| C | Perception | VERIFIED | test_phase_c_perception_expansion.py | Recover exact original C items and map individually |
| D | Attention | VERIFIED | test_phase_d_attention_expansion.py | Recover exact original D items and map individually |
| E | Working memory | VERIFIED | test_phase_e_working_memory_expansion.py | Recover exact original E items and map individually |
| F | Long-term memory | VERIFIED | test_phase_f_long_term_memory_expansion.py | Recover exact original F items and map individually |
| G | Original specification | NEEDS-RECONCILIATION | No recoverable original mapping | Recover/reconstruct G specification |
| H | Reasoning | VERIFIED | test_phase_h_reasoning_expansion.py | Recover exact original H items and map individually |
| I | Executive brain | VERIFIED | test_phase_i_executive_expansion.py | Recover exact original I items and map individually |
| J | Inhibition/control | VERIFIED | test_phase_j_inhibition_control_expansion.py | Recover exact original J items and map individually |
| K | Original specification | NEEDS-RECONCILIATION | No recoverable original mapping | Recover/reconstruct K specification |
| L | Verification | VERIFIED | test_phase_l_verification_expansion.py | Recover exact original L items and map individually |
| M | Learning | VERIFIED | test_phase_m_learning_expansion.py | Recover exact original M items and map individually |
| N | Sleep/consolidation | VERIFIED | test_phase_n_sleep_consolidation_expansion.py | Recover exact original N items and map individually |
| O | Computational state | VERIFIED | test_phase_o_computational_state_expansion.py | Recover exact original O items and map individually |
| P | Child genesis | VERIFIED | test_phase_p_child_genesis_expansion.py | Recover exact original P items and map individually |
| Q | Independent child brain | VERIFIED | test_phase_q_independent_child_brain_expansion.py | Recover exact original Q items and map individually |
| R | Mother-child integration | VERIFIED | test_phase_r_mother_child_integration_expansion.py | Recover exact original R items and map individually |
| S | Living child loop | VERIFIED | test_phase_s_living_child_loop_expansion.py | Recover exact original S items and map individually |
| T | Original specification | NEEDS-RECONCILIATION | No recoverable original mapping | Recover/reconstruct T specification |
| U | Original specification | NEEDS-RECONCILIATION | No recoverable original mapping | Recover/reconstruct U specification |
| V | Original specification | NEEDS-RECONCILIATION | No recoverable original mapping | Recover/reconstruct V specification |
| W | Model independence | VERIFIED | test_phase_w_model_independence_expansion.py | Recover exact original W items and map individually |
| X | Continuous runtime | VERIFIED | test_phase_x_continuous_runtime.py | Recover exact original X items and map individually |
| Y | Observability | VERIFIED | test_phase_y_observability_expansion.py | Recover exact original Y items and map individually |
| Z | Backup/recovery | VERIFIED | test_phase_z_backup_recovery_expansion.py | Recover exact original Z items and map individually |
| AA | Audit/provenance | VERIFIED | test_phase_aa_audit_provenance_expansion.py | Recover exact original AA items and map individually |
| AB | Failure/recovery | VERIFIED | test_phase_ab_failure_recovery_expansion.py | Recover exact original AB items and map individually |
| AC | Original specification | NEEDS-RECONCILIATION | No recoverable original mapping | Recover/reconstruct AC specification |

## Engineering overlays requiring mapping
- E01–E13 (Maya/Hunter expansion track): map into A–AC without creating duplicate architecture requirements.
- 6P-1–12: map into A–AC as an engineering overlay.
- 6P-13–29: repository tests exist, but these are not part of the maintained 6P roadmap definition and require explicit reconciliation before being counted as official milestones.
- Historical/duplicate tests must not be counted as separate architecture requirements.

## Engineering verification update — 2026-10-08

The local recovery audit confirmed that the phone repository is the authoritative working copy for the current implementation: `main` is 26 commits ahead of `origin/main`, with the local Phase 9–14, Android, Main Brain, memory, research, tool, agent, security, and native-intelligence work preserved locally. No GitHub push was performed during this audit.

The exact historical 417-item source was not found in the current Git history or the three discovered SAHIBEX ZIP backups using targeted requirement/specification searches. Therefore the audit does not invent missing requirement text.

Current engineering evidence:
- 6P final commissioning suite: 6 passed
- Default-provider integration regression: 2 passed
- Full repository regression: 1130 passed, 0 failed
- Python compileall: PASS
- `git diff --check`: PASS
- Local Qwen3 1.7B GGUF model is present and the compiled llama.cpp server loaded it successfully on localhost:8080.
- A live SAHIBEX cognitive smoke test using the local model returned a verified response. The phone CPU inference is slow, but functional.

A real integration bug was fixed in `core/brain/mother_operational_integration.py`: omitting the provider now uses the registered default provider instead of incorrectly assuming `mock`. Explicit provider selection remains supported.

Additional live-brain commissioning evidence:
- Protected Tool Brain now has real project-scoped `write_file`, `delete_file`, and `run_command` handlers behind the existing PermissionEngine + Human Confirmation gate.
- Verification policy was corrected so an explicitly confirmed medium/high action is considered verified after the permission gate has consumed the confirmation; unconfirmed protected actions remain blocked.
- MasterBrain now delegates confirmed protected filesystem/command actions to Tool Brain instead of merely generating a cognitive response.
- End-to-end protected runtime probe: write → read → delete → command all returned `VERIFIED`; the probe file was removed after the test.
- Persistent-memory context was strengthened: deterministic token-overlap retrieval plus safe DATA-labelled memory/knowledge context is now supplied to the local cognitive model.
- Cross-instance persistent-memory test: PASS; stored project-codename memory was retrieved and used by the local cognitive engine.
- A live runtime robustness bug was found and fixed: an empty operational-model failure response could previously crash the interactive app through `MotherRuntimeState.fail()`. The runtime now converts an empty failure into a non-empty controlled failure message and keeps the session alive.
- Latest full regression after these changes: 1130 passed, 0 failed; compileall PASS; `git diff --check` PASS.
- Live commissioning also found and fixed a local-model context overflow: persistent retrieval could build an approximately 36,000-character prompt for a 2048-token local context. Cognitive memory/knowledge context is now bounded before prompt construction; dedicated bounds tests pass.
- Master Brain → local Qwen3 → operational verification was re-run after the fix and returned SUCCESS / VERIFIED.
- Latest interactive SAHIBEX runtime was restarted successfully (PID 3077 at commissioning time); status showed Master Brain ONLINE, Constitution ACTIVE, Permission Engine ONLINE, Verification Engine ONLINE, Protected Actions CONTROLLED, User Authority FINAL.
- Live unconfirmed delete test remained blocked with `require_confirmation`, `permission_allowed=False`, and `NOT_EXECUTED`.

## Current audit conclusion
- 29 phase labels: 23 have implementation/evidence checkpoints.
- 6 labels (G, K, T, U, V, AC) remain specification-reconciliation blockers.
- Exact 417-item completion percentage: NOT CLAIMABLE until the original item-level source is recovered/reconstructed.
- 6P final commissioning evidence is verified against the current repository.
- Current engineering regression is green at 1126/1126.
- The missing original A–AC requirement source is a documentation/specification recovery gap, not an observed code-test failure.
- Next specification action: recover/reconstruct the original A–AC item-level baseline only from authoritative historical artifacts, while keeping reconstructed items explicitly labelled.

## Safety
This audit document does not change Constitution, permissions, authority boundaries, or runtime behavior.


## Live Runtime Commissioning — 2026-10-09

- Local Qwen3 1.7B GGUF via llama.cpp is operational on `127.0.0.1:8080`; llama.cpp exposes `/health` and OpenAI-compatible `/v1/chat/completions`.
- Live DuckDuckGo HTML discovery backend is implemented and real external search returned 3 verified discovery records during commissioning.
- Production CLI runtime now explicitly enables `SAHIBEX_SEARCH_BACKEND=duckduckgo_html`; every network acquisition remains behind the existing NETWORK_ACCESS permission gate.
- Background supervisor added with health checking/restart and optional `termux-wake-lock` support.
- `scripts/start_sahibex_live.sh` starts the local model and the interactive SAHIBEX runtime.
- `scripts/start_sahibex_background.sh` starts the persistent model supervisor.
- Search fail-closed tests explicitly clear the runtime environment and pass; no permission boundary was removed.
- Latest full repository regression after live-runtime changes: **1130 passed, 0 failed**.

## Source recovery + research evidence gate follow-up — 2026-10-09

### Historical 417-item source recovery result
- Repeated repository search across tracked/untracked project documentation found no independent original 417-item requirement list.
- Repeated local archive inventory covered `SAHIBEX_FULL_BACKUP.zip`, `SAHIBEX_COMPLETE_ARCHIVE.zip`, `SAHIBEX_BACKUPS/SAHIBEX_FULL_BACKUP_2026-10-04.zip`, and `SAHIBEX_FULL_BACKUP_2026-10-09.zip`. The archive entries expose the current/reconstructed audit matrix and roadmap documents, but no separate original item-level 417 specification.
- Git history for `docs/ROADMAP` contains the reconciled roadmap/status/audit documents but no independent original item-level source.
- Therefore the historical source remains **NOT RECOVERED**. This is a source/provenance limitation, not evidence that 417 requirements failed. No original item text or exact completion ratio has been fabricated.
- A reconstructed baseline can be drafted from documented architecture, existing code contracts, and tests, but must remain explicitly labelled `RECONSTRUCTED — NOT THE HISTORICAL ORIGINAL` until the user approves it as the new maintained baseline.

### Additional research-answer integrity fix
- `ResearchPipelineIntegration.handle_answer()` now refuses synthesis unless the current job has a positive verified-evidence count, the evidence records can be loaded, and at least one corresponding source record is retrievable for traceability.
- Regression tests cover zero evidence, missing verified-evidence gate, and evidence with an unavailable source.
- Focused research/security regression at this checkpoint: 26 passed; focused research answer/pipeline regression after source-traceability guard: 19 passed.
- Full repository regression and compile validation are being rerun before this code change is committed.


## Live runtime / research integrity continuation — 2026-10-09

- Full repository regression after fail-closed research/learning changes: **1541 passed, 0 failed** in 140.48 seconds. Final source-lead helper has a separate focused result of 13 passed; rerun full regression after final changes before marking the current pass complete.
- Local Qwen3 model and authenticated Android media bridge are healthy. Two live Hindi `/voice` requests returned correct curated answers over HTTP 200 in 0.12–0.15 seconds. Physical phone microphone/TTS UI remains pending app update/pairing.
- Supervisor duplicate-restart defect fixed: health-first check avoids spawning duplicate media servers; restart count remained stable during a 12-second runtime check.
- Research extraction now strips active HTML and navigation chrome, bounds work to 200,000 content characters / 100 findings, and marks extraction truncation. The final research result now fails closed unless the answer is actually `VERIFIED`; a live run completed but returned `NOT_VERIFIED`, which is treated as `insufficient_evidence`, not success. Source links may be offered as unverified research leads, not conclusions.
- A production research answer is not yet proven. The current default sentence extractor has confidence 0.50 and the current pipeline has not demonstrated cross-source semantic corroboration for a real query. Do not mark live research as complete until a query returns a verified, relevant, source-traceable answer.
- Companion APK staged version `6 / 0.2.2` matches the installed signing certificate and is now hash-matched in Downloads. Installed version remains `4 / 0.2.0` pending user-visible Android install confirmation.
