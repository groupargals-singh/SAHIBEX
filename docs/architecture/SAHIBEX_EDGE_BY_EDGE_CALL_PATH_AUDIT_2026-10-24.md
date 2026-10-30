# SAHIBEX Main Brain — Edge-by-Edge Source Call-Path Audit

**Audit date:** 2026-10-24  
**Workspace:** `~/SAHIBEX`  
**Purpose:** Validate the main architecture diagram's primary edges against source code. This is a source audit, not proof that every branch was exercised in a live runtime.  
**P1–P12 impact:** None. This documentation audit does not change a phase-gate status.

## Method and evidence rules

Each edge below was checked against the named implementation and line range in the current phone workspace. “Verified in source” means the call/data relationship exists in code; it does not mean a physical modality (microphone, camera, Accessibility) has passed device acceptance. Line numbers are valid for the audited workspace revision and may shift after later code changes.

## Edge register

| ID | Diagram edge | Source evidence | Finding |
|---|---|---|---|
| E01 | CLI/user text → MainBrain | `app/main.py:104`, `app/main.py:168`; `core/brain/master_brain.py:908–910` | **VERIFIED IN SOURCE.** App constructs `MasterBrain` and passes `user_input` to `brain.process()`. The CLI path is verified; Companion voice remains a separate authenticated relay and physical mic/TTS acceptance is still pending. |
| E02 | MainBrain → deterministic fast paths | `core/brain/master_brain.py:908–1098` | **VERIFIED IN SOURCE.** Empty request, arithmetic, curated fact, deterministic conversation, and deterministic text-task branches can return before the normal intent/authorization/planning path. Diagram must not imply every request passes through all gates. |
| E03 | MainBrain → intent/action classification | `core/brain/master_brain.py:1100–1210` | **VERIFIED IN SOURCE.** Intent is detected (optional semantic fallback), action is classified, and risk is mapped before authorization. |
| E04 | Human authority + permission → verification | `core/brain/master_brain.py:1210–1298`; `core/brain/permission_gateway.py:29–44`; `verification/verifier.py:79+` | **VERIFIED IN SOURCE.** The request is checked through the approval/permission paths and passed into `VerificationEngine.verify()`. Verification does not execute actions. |
| E05 | Denied/unsafe request → blocked result | `core/brain/master_brain.py:1300–1435` | **VERIFIED IN SOURCE.** Constitution denial, missing confirmation, permission denial, and failed verification branches create blocked results, record denial/context, and return without entering the main execution route. |
| E06 | Accepted request → memory/knowledge context | `core/brain/master_brain.py:1438–1470`; `core/brain/operational_memory_knowledge.py:109+`; `core/brain/memory_brain.py:360+`; `core/brain/knowledge_brain.py:160+` | **VERIFIED IN SOURCE.** A query-scoped retrieval is added to `MotherDecisionContext` before reasoning/planning. This is a contextual side-channel, not a universal standalone answer route. Operational processing can also perform its own retrieval (`core/brain/mother_operational_integration.py:201–231`). |
| E07 | MainBrain → internal reasoning handler | `core/brain/master_brain.py:1472–1511`; `core/brain/master_brain.py:862–878`; `core/brain/internal_brain_team.py:68+` | **VERIFIED IN SOURCE.** MainBrain calls `dispatch_internal_brain("reasoning", ...)`, passing upstream authorization and verification booleans. This is an internal role dispatch, not evidence of an independent model or process. |
| E08 | Reasoning → planning/orchestration | `core/brain/master_brain.py:1512–1579`; `core/brain/master_brain.py:862–878`; `core/brain/internal_brain_team.py:68+` | **VERIFIED IN SOURCE.** MainBrain dispatches the orchestration role and requires a plan before the main research/learning/operational execution stage. Dispatch failures fail closed. |
| E09 | Protected actions → ToolBrain | `core/brain/master_brain.py:1600–1642`; `core/brain/tool_brain.py:175+` | **VERIFIED IN SOURCE.** Write/delete/command requests route to ToolBrain after upstream gates. ToolBrain maintains its own tool discovery, permission, executor, result-integrity and recovery boundary; no self-authorization is intended. |
| E10 | Read-only file operation → ToolBrain | `core/brain/master_brain.py:1644–1688`; `core/brain/tool_brain.py:175+` | **VERIFIED IN SOURCE.** File-operation/read requests are dispatched to ToolBrain rather than being answered as if a file had been read. |
| E11 | Search → research role → research result | `core/brain/master_brain.py:1690–1806`; `core/brain/master_brain.py:862–878`; `core/brain/mother_research_integration.py:716+` | **VERIFIED IN SOURCE.** Search dispatches the `research` internal role, which returns a structured result; MainBrain checks handler success, verification and persistence flags, result success and `verification_status == "VERIFIED"`. Failure returns a safe fallback. |
| E12 | Learn → learning role → verified knowledge result | `core/brain/master_brain.py:1808–1910`; `core/brain/mother_learning_integration.py:109–184+` | **VERIFIED IN SOURCE.** Learning dispatches the `learning` role and rejects results unless dispatch success/verification/persistence, result verification, and a positive verified-knowledge count are all present. Learning calls the configured research integration. |
| E13 | Operational/coding → operational result | `core/brain/master_brain.py:1912–2009`; `core/brain/mother_operational_integration.py:201+` | **VERIFIED IN SOURCE.** Coding uses the internal coding role; other listed operational intents call `process_approved_request()`. Operational result quality/factual verification is distinct from merely receiving generated text. |
| E14 | Worker team → registered child handlers | `core/brain/master_brain.py:788–860` | **VERIFIED WITH EXPLICIT GATES.** Worker dispatch requires Mother and human approval, distinct registered child IDs, child-manager dispatch, and joint result verification. Managed process execution is conditional on configured managed-worker runtime; do not draw all internal roles as independent processes. |
| E15 | Branch result → final MainBrain response | `core/brain/master_brain.py:2010–2355` | **VERIFIED IN SOURCE.** The response is selected from tool/research/learning/operational/reasoning results, metadata preserves branch-specific status, runtime is completed, and context is recorded. Research/learning failures return earlier through fail-closed branches. |
| E16 | MainBrain result → context/memory recording | `core/brain/master_brain.py:2594–2735` | **VERIFIED IN SOURCE.** Denial audit is separate from interaction/context recording. `_record_context()` stores the interaction and calls the configured memory/learning recording hooks. This is not a guarantee that every generated statement becomes trusted knowledge. |
| E17 | Companion microphone → MainBrain → audible TTS | `android_companion/VOICE_PAIRING.md` and `logs/p6_p7_p8_p10_p11_p12_checkpoint_20261023.md` | **NOT PHYSICALLY VERIFIED.** Software relay/APK evidence exists, but actual microphone recognition and audible TTS must be observed on-device. Keep P6 PARTIAL. |
| E18 | Camera/screenshot → OCR/vision → grounded answer | `core/brain/ocr_runtime.py`; `core/brain/vision_ocr_integration.py`; `core/brain/vision_reasoning.py`; `android_companion/VOICE_PAIRING.md` | **PARTIAL / NOT AN END-TO-END VISION ROUTE.** OCR runtime and a provenance-bearing observation contract exist. `VisionReasoningIntegration` is contract-only, the local model is text-only, and camera acquisition is not connected to a live vision model. Keep P7 PARTIAL. |
| E19 | Companion Accessibility → live UI actions / Emergency Stop | `android_companion/app/src/main/java/com/sahibex/companion/SahibexAccessibilityService.java`; `logs/p7_p8_device_capability_gate_20261021.md` | **SOURCE PRESENT; PHYSICAL ACCEPTANCE PENDING.** UI tree, gesture, typing, screenshot and persistent stop paths exist in source. The service still needs to be enabled and exercised on a real device; keep P8 PARTIAL. |

## Corrections/limitations for the diagram

1. Label the internal routing intermediary (`InternalBrainTeam.dispatch`) between MainBrain and reasoning/orchestration/research/learning/coding handlers.
2. Label fast deterministic exits as bypassing the normal full route; do not draw a mandatory straight-through pipeline for all prompts.
3. Show memory/knowledge as context retrieval before reasoning and as a separate audit/interaction recording side-channel, not as a specialist result that automatically flows into verification.
4. Show tool execution as a protected subroute with its own permission/executor/result-integrity checks.
5. Treat the final “verification” node as branch-specific: research and learning enforce their own verified-result checks; operational text may be only structurally valid and is not thereby fact-verified; deterministic routes use their explicit status labels.
6. Keep camera/vision, physical microphone/TTS, and live Accessibility edges dashed/labelled pending until physical acceptance evidence exists.
7. The SVG is valid source artwork but **visual rendering on the target Android screen remains unverified** in this environment because no SVG renderer is installed in the current Termux environment. XML validity is not visual acceptance.

## Verification performed

- Source call-sites and line ranges were inspected on the current phone workspace.
- No runtime code, Constitution, permission policy, model configuration, or P1–P12 status was changed by this audit.
- The architecture image must remain explanatory documentation, never proof of device capability or release readiness.
