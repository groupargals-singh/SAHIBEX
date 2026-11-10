# SAHIBEX Master Architecture Specification
Version: 1.0 (Architecture consolidation baseline)
Date: 2026-11-01
Status: DOCUMENTED TARGET + EVIDENCE-BOUND CURRENT STATE
Authority: User / SAHIBEX Constitution
Workspace: ~/SAHIBEX

## 1. Purpose and source-of-truth boundaries
This document consolidates the current SAHIBEX architecture and the approved direction from the supplied HUSAI v3.2 / Release 4.0 material. It is an architecture specification, not a claim that every target capability is implemented or accepted.

The following remain authoritative for their own evidence:
- `docs/ROADMAP/MASTER_ROADMAP_RECONCILED.md`: master roadmap and no-repeat policy.
- `docs/ROADMAP/MASTER_REMAINING_WORK_LIST_2026-10-10.md`: remaining work queue.
- `docs/ROADMAP/SAHIBEX_PHASE_GATE_REGISTRY_2026-10-21.md`: scoped phase-gate evidence.
- `docs/ROADMAP/417_REQUIREMENTS_MASTER_AUDIT_MATRIX.md`: 417-item requirements reference; historical v1.0 provenance remains unresolved.
- `docs/ROADMAP/GEMINI_HUSAI_ARCHITECTURE_ADOPTION_REGISTER_2026-11-01.md`: external concept adoption decisions.
- `docs/architecture/SAHIBEX_EDGE_BY_EDGE_CALL_PATH_AUDIT_2026-10-24.md`: source-level E01–E19 call-path evidence.
- `docs/STATUS/PHASE1_TASK1_PROJECT_BASELINE_2026-11-01.md` and `PHASE1_TASK2_ARCHITECTURE_INVENTORY_2026-11-01.md`: Phase 1 evidence.

## 2. Non-negotiable governance
1. User Authority is final. No subsystem, Council, model, worker, child brain or generated plan may override it.
2. Constitution is immutable to SAHIBEX. Changes require the user's explicit decision through a separately governed process; no self-modification.
3. Protected operations (write, delete, execute, network, credentials, system changes, financial actions, self-update and external control) remain behind explicit permission/approval and audit requirements.
4. Emergency Stop must dominate all action/worker paths and remain effective during recovery.
5. A planner, Cognitive Council or confidence score cannot grant permission.
6. Untrusted input, retrieved snippets, model output and synthetic data are not verified evidence.
7. No bulk promotion of legacy knowledge. Verified-only retrieval requires the latest VERIFIED lifecycle event and current explicit verification metadata.
8. Code presence, architecture diagrams and unit tests do not prove physical-device or end-to-end acceptance.
9. Preserve all existing user modifications, untracked files, databases, logs and backups. No destructive cleanup or reset.

## 3. Architecture planes

### 3.1 Interaction and perception plane
Responsibilities: accept text, Hindi/Hinglish/English, voice, image/OCR and authorized device signals; normalize input; identify language/entities; estimate ambiguity and input quality.
Existing evidence: `core/brain/perception.py`, `perception_language_brain.py`, `contextual_input_understanding.py`, `universal_language_brain.py`, `speech_recognition.py`, `voice.py`, `vision.py`, `ocr_runtime.py`, multimodal modules and the P6/P7 records.
Current acceptance: text/language paths have bounded software acceptance; physical Hindi speech and mic-to-speaker E2E remain PARTIAL; vision is OCR-led and semantic image understanding remains PARTIAL/BLOCKED.

### 3.2 Root command and control plane
Responsibilities: one MasterBrain entry point; intent/action/risk classification; Constitution; human authority; permission/approval; verification; Emergency Stop; audit.
Existing evidence: `core/brain/master_brain.py`, `intent.py`, `permission_gateway.py`, `emergency_stop.py`, `core/policies/approval.py`, `verification/verifier.py`, ToolBrain and audit modules.
Rule: fast deterministic paths may return before the full route; diagrams and tests must not imply every request traverses every stage.

### 3.3 Cognitive state and memory plane
Responsibilities:
- Working memory: current task state, relevant recent context and bounded scratchpad.
- Episodic memory: interactions/events with time and provenance.
- Semantic memory: durable claims/knowledge with verification lifecycle.
- Procedural memory: approved reusable procedures and task patterns.
- Attention: select relevant signals and manage task focus.
- Context manager: assemble only task-relevant and trust-eligible context.
Existing evidence: `memory_brain.py`, `working_memory_expansion.py`, `attention.py`, `core/research/episodic_memory.py`, `semantic_memory.py`, `procedural_memory.py`, storage and provenance modules.
Current acceptance: bounded components and tests exist. Full lifetime relevance/retention policy and every runtime composition path are not automatically complete.

### 3.4 Knowledge and research plane
Responsibilities: source discovery, permission-gated acquisition, validation, deduplication, provenance, claim extraction, conflict handling, independent corroboration, graph relationships and verified-only retrieval.
Existing evidence: `knowledge_brain.py`, `research_learning_brain.py`, `core/research/*`, `knowledge_graph_storage.py`, `persistent_memory_knowledge_graph.py`, source/evidence registries and provenance audit.
Important distinctions:
- Knowledge graph storage is not by itself GraphRAG.
- Vector embedding/vector search is a separate capability and is currently MISSING/DESIGN REQUIRED in the adoption register.
- Search snippets are leads, not verified facts.
- Knowledge trust remediation remains BLOCKED until independent corroboration and lifecycle verification are performed under backup and approval controls.

### 3.5 Reasoning and planning plane
Responsibilities: goal decomposition, reasoning modes, plan generation, constraint checking, uncertainty estimation, alternatives and result critique.
Existing evidence: `reasoning.py`, `reasoning_coordinator.py`, `operational_reasoning.py`, `core/orchestrator/planner.py`, goal modules, `uncertainty.py`, `three_brain_council.py`.
HUSAI mapping: Innovator, Critic and Pragmatist may advise through the existing Council. Their agreement is not proof and cannot bypass the permission plane.
HTN-specific planning and measurable plan-quality benchmarks remain DESIGN/ACCEPTANCE work.

### 3.6 Action and tool plane
Responsibilities: tool selection, schema validation, approval checks, sandboxed execution, result integrity, audit and recovery.
Existing evidence: `tool_brain.py`, tool registry/executor, operational tool execution, permission gateway, sandbox and tests.
Structured JSON Schema validation is the first adoption step for tool arguments. GBNF constrained decoding is MISSING/DESIGN REQUIRED until backend capability is verified; grammar constraints alone do not make execution safe.
Dynamic Tool Synthesizer remains DEFERRED until isolated sandbox, approval, verification and rollback are demonstrated.

### 3.7 Learning, reflection and consolidation plane
Responsibilities: inspect outcomes, detect errors, update only permitted memories, consolidate during approved idle windows and propose improvements for human review.
Existing evidence: learning integrations, confidence/verification, sleep consolidation, controlled self-improvement governance and audit.
No automatic sensitive code changes, Constitution edits, permission changes or unverified knowledge promotion are allowed.

### 3.8 Runtime, model and resource plane
Responsibilities: model provider routing, capability checks, local/cloud selection, bounded resource scheduling, lifecycle supervision, observability and recovery.
Existing evidence: `core/model_gateway/*`, `core/brain/resource.py`, `observability_expansion.py`, `recovery_controller.py`, runtime/supervisor scripts.
Current limitations: resource module presence is not proof of live adaptive RAM/CPU/battery scheduling; SahibexExecutionLoop production composition remains NOT VERIFIED. Do not bypass device RAM guards.

## 4. Root request flow
1. User input enters through CLI/text or an authenticated Companion route.
2. Perception/normalization and intent/action/risk classification run; deterministic safe fast paths may exit early.
3. Constitution, human authority, permission and verification gates decide whether a protected route may proceed.
4. Task-relevant memory/knowledge context is assembled under provenance and lifecycle rules.
5. MasterBrain dispatches reasoning and orchestration handlers; a plan is required for the relevant execution routes.
6. Request routes to research, learning, operational/coding or ToolBrain execution as appropriate.
7. Branch-specific acceptance checks validate result, verification status and persistence where required.
8. Audit/context records are written through their governed paths; response reports truthful status and uncertainty.
9. Learning/consolidation is separate from immediate execution and must follow permission and data-trust rules.

Source edge details and exceptions are maintained in the E01–E19 edge audit, not duplicated here.

## 5. HUSAI department mapping
- Central/Kendriya Brain → existing SAHIBEX MasterBrain/router (one root only).
- Learning Brain → research, learning and knowledge acquisition responsibilities.
- Teaching Brain → explanation/education responsibilities distributed among existing handlers; no duplicate root.
- Action Brain → planner + ToolBrain + approved execution.
- Reflection Brain → confidence/verification, audit, evaluation, recovery and approved consolidation.
- Cognitive Council → advisory perspectives, not an authority or truth oracle.

## 6. Dependency and acceptance matrix

| Capability | Depends on | Current disposition | Acceptance still needed |
|---|---|---|---|
| Perception | input adapters, language/context, modality runtime | IMPLEMENTED bounded / PARTIAL | physical voice E2E; semantic vision |
| Working memory / attention | MasterBrain context composition, lifecycle, relevance policy | IMPLEMENTED bounded / integration to verify | end-to-end lifecycle and cross-task prioritization |
| Episodic/semantic/procedural memory | storage, provenance, lifecycle verification | IMPLEMENTED bounded | full-lifetime quality; preserve verified-only rule |
| GraphRAG | verified knowledge retrieval + graph traversal/ranking | GRAPH STORAGE IMPLEMENTED; GraphRAG NOT VERIFIED | production wiring and retrieval benchmark |
| Vector search | multilingual embedding model, index/storage, provenance filter | MISSING / DESIGN REQUIRED | model selection, recall/latency/RAM benchmark |
| Reasoning / HTN | intent, goals, planner, constraints, context | COMPONENTS IMPLEMENTED; HTN acceptance PARTIAL | plan-quality benchmark and integration trace |
| Cognitive Council | MasterBrain response path, evidence-aware critic | IMPLEMENTED advisory | preserve advisory-only status; outcome eval |
| Uncertainty | claim/task signals and labelled evaluation set | IMPLEMENTED bounded | probability calibration and multilingual evaluation |
| Structured tool calls | provider schema capability, JSON Schema validation, permission gateway | MISSING / DESIGN REQUIRED | schema validation then backend grammar capability test |
| World/causal/simulation | defined state/action model and labelled prediction tasks | MISSING / RESEARCH-DESIGN | narrow benchmark before implementation |
| Action/ToolBrain | approval, Emergency Stop, sandbox, audit, verification | IMPLEMENTED bounded | real Companion/physical action acceptance |
| Sleep/proactive jobs | idle scheduler, cancellation, resource caps, audit, approval | PARTIAL | safe scheduled runtime proof |
| Observability/recovery | correlated events, retention, supervisor, restore drills | IMPLEMENTED components / PARTIAL | persistent traces and physical recovery drills |
| Self-improvement | proposal, tests, human approval, atomic commit, rollback | CONTROLLED framework | no autonomous protected update; verify each bounded lifecycle |
| Model/resource routing | provider capabilities, hardware telemetry and safety guards | IMPLEMENTED routing / PARTIAL resource intelligence | live resource-aware policy evaluation |

## 7. Explicitly deferred / research-only
- LoRA/RLHF/DPO/SFT and foundation pretraining: defer until licensed/curated data, sufficient compute, safety evaluation and explicit approval.
- Dynamic code synthesis: sandbox research only; no generated execution outside approved isolation.
- PRM/MCTS and speculative decoding: benchmark only after a concrete use case and supported backend.
- FlashAttention, PagedAttention, ZeRO, Ring-AllReduce, HBM/Tensor Core optimization: server-scale research, not assumed useful on Android.
- Mechanistic interpretability/SAE: research/diagnostic work only.

## 8. Phase 1 open items
1. Complete the dedicated Brain Connection Registry, including source-verified edges and unresolved runtime-only edges.
2. Consolidate the Security/Authority matrix and Resource/Model dependency matrix with exact source anchors.
3. Decide whether this document is accepted as the current additive Master Architecture Specification; it does not replace the 417-item baseline or phase-gate registry.
4. After Phase 1 documentation is accepted, move to Phase 2 cognitive-loop implementation only for genuine integration gaps.

## 9. Acceptance statement
This specification consolidates the architecture and current evidence boundaries. It does not claim full runtime completion, physical voice/vision/Accessibility acceptance, live GraphRAG, vector search, world-model simulation or release readiness.
