# SAHIBEX Control-Plane, Authority and Resource/Model Matrix
Date: 2026-11-01
Status: STATIC SOURCE REVIEW — acceptance boundaries only

## 1. Authority hierarchy
1. User Authority — final decision-maker.
2. Constitution / policy — immutable constraints; no Brain/model/worker may edit or override them.
3. PermissionEngine + PermissionGateway — classify and decide whether a typed action is allowed; these components do not execute actions.
4. Human approval/confirmation — required for protected operations according to the active policy.
5. EmergencyStop — fail-closed execution latch; blocks protected execution while engaged and never grants permission.
6. Planner / Cognitive Council / internal roles / child workers — advisory or delegated task responsibilities only; they cannot grant authority.
7. ToolBrain / executor — may execute only after upstream and local gates pass.
8. Verification / audit — inspect decisions and outcomes; must not be conflated with permission or execution.

## 2. Action policy observed in current PermissionEngine
Source: `core/policies/approval.py`; gateway: `core/brain/permission_gateway.py`.

| ActionType | Current risk | Current policy in PermissionEngine |
|---|---|---|
| RESPOND | LOW | Allowed without confirmation |
| RESEARCH | LOW | Allowed without confirmation |
| CREATE | LOW | Allowed without confirmation (this enum alone does not prove arbitrary filesystem writes are allowed) |
| READ_FILE | LOW | Allowed without confirmation |
| WRITE_FILE | MEDIUM | Requires user confirmation |
| NETWORK_ACCESS | MEDIUM | Requires user confirmation |
| DELETE_FILE | HIGH | Requires explicit user confirmation |
| RUN_COMMAND | HIGH | Requires explicit user confirmation |
| CREDENTIAL_USE | HIGH | Requires explicit user confirmation |
| SYSTEM_CHANGE | CRITICAL | Blocked by default, including when the confirmation flag alone is true |
| FINANCIAL_ACTION | CRITICAL | Blocked by default, including when the confirmation flag alone is true |

Important scope note: the enum/policy above is the exact observed implementation of this PermissionEngine. Higher-level protected categories such as self-update or external control must remain blocked by the relevant Constitution/approval/tool boundary; do not assume they are covered by this enum unless their actual mapping is traced.

PermissionGateway delegates to PermissionEngine, validates the action/confirmation types and raises PermissionError on denied requirements. It never executes actions or creates authority.

## 3. Emergency Stop and recovery semantics
- `core/brain/emergency_stop.py`: CLEAR/STOPPED latch with timestamped in-memory event history; `allows_protected_execution()` returns false when engaged; it explicitly grants no permission, executes no action, modifies no system and overrides no human authority.
- Persistence across process restart is NOT established by this class alone. P8 persistent Emergency Stop acceptance remains pending until a durable store/service and physical restart test are demonstrated.
- `core/brain/recovery_controller.py`: READY/RECOVERING/RECOVERED/FAILED lifecycle state machine with in-memory history. It does not grant permission or execute protected work. Physical supervisor/restart/restore recovery remains separate acceptance.
- Emergency Stop must dominate retries, background workers, model/tool execution and recovery actions. Clearing it must require an authorized reasoned operation; this source review does not certify the entire physical control path.

## 4. Verification and audit boundary
- Verification evaluates intent/action/risk or execution-result consistency; it does not itself execute an action.
- The existing ToolIntelligence post-execution verifier checks internal consistency/safety properties. It does not prove the real-world side effect reached its intended final state or that generated content is factually correct.
- Authenticated PENDING intent must be recorded before protected ToolBrain handler execution. If this precondition fails, execution must fail closed.
- A final audit write failure after a tool may have executed must be reported as potentially executed; do not blindly retry a protected side effect.
- Council consensus and confidence values cannot replace independent evidence or permission checks.

## 5. Resource and model control matrix

| Component | What source proves | What source does NOT prove | Current disposition |
|---|---|---|---|
| `core/brain/resource.py:BrainResourceState` | Tracks active task count and max concurrency; validates bounds | No live RAM/CPU/battery/storage telemetry or model-load-aware scheduling | BOUNDED LOAD CONTRACT |
| `core/model_gateway/router.py:ModelRouter` | Selects explicitly requested registered provider or configured default and calls gateway | No dynamic hardware-aware routing or resource-based fallback policy in this class | PROVIDER ROUTER PRESENT |
| `core/model_gateway/*` | Provider/gateway abstractions and capability/fallback modules exist | No guarantee every fallback is safe/available in current runtime | ROUTING FRAMEWORK; runtime-specific |
| `core/brain/observability_expansion.py` | Read-only in-memory event collector with max_events bound (default 1000) | No durable correlated tracing/retention across process restart | IN-MEMORY OBSERVABILITY |
| `core/brain/recovery_controller.py` | Recovery lifecycle state tracking | No process supervisor, automatic restore or physical failure recovery by itself | STATE MACHINE ONLY |
| Worker resource boundaries | Bounded active task contracts exist | No proof of phone-wide adaptive scheduling | PARTIAL |

## 6. Required resource-aware design before implementation
A future Resource Intelligence service may read, but must not exceed, approved OS/device telemetry:
- available RAM and memory pressure;
- CPU load and thermal state where available;
- battery level/charging and power-saver state;
- storage availability;
- network availability/latency;
- model resident size, context/KV-cache budget and measured inference latency;
- active task count, priority, deadline and cancellation state.

Scheduling policy must:
1. enforce hard memory/concurrency ceilings and never bypass model guards;
2. prefer smaller/offline models when network is unavailable or resource pressure is high;
3. pause/defer low-priority work under thermal/battery pressure;
4. bound worker fan-out, queue depth, retries and execution time;
5. honor Emergency Stop and user cancellation before dispatch and between steps;
6. log decisions with privacy-conscious correlated event IDs;
7. fail closed for protected actions if permission, audit or verification services are unavailable.

## 7. Model-routing adoption sequence
1. Inventory actual provider capabilities and resource constraints (read-only).
2. Add/verify typed request schemas and provider capability validation.
3. Add telemetry collection with explicit privacy/retention policy.
4. Benchmark model latency, memory and answer quality on representative Hindi/Hinglish/English tasks.
5. Define a deterministic resource policy with hard limits and explainable routing reasons.
6. Test provider unavailable, low-memory, network-offline, cancellation, timeout and Emergency Stop cases.
7. Only then consider adaptive routing; no silent cloud fallback or credential use.

## 8. Current blockers / non-claims
- Do not claim persistent Emergency Stop based solely on the in-memory latch.
- Do not claim full device-level Resource Intelligence from BrainResourceState's task counter.
- Do not claim hardware-aware ModelRouter from explicit/default provider selection.
- Do not claim durable observability from the in-memory collector.
- Do not claim physical recovery from RecoveryController's state machine.
- Do not claim a protected action is factually or externally verified solely because internal consistency checks passed.
- P6/P7/P8/P10/P11 and knowledge-trust statuses are unchanged.

## 9. Source files inspected
- `core/brain/permission_gateway.py`
- `core/brain/emergency_stop.py`
- `core/policies/approval.py`
- `core/brain/resource.py`
- `core/model_gateway/router.py`
- `core/brain/recovery_controller.py`
- `core/brain/observability_expansion.py`
- Related execution and verification call-path findings in `SAHIBEX_BRAIN_CONNECTION_REGISTRY_2026-11-01.md` and `GEMINI_HUSAI_ARCHITECTURE_ADOPTION_REGISTER_2026-11-01.md`

## 10. Acceptance statement
This matrix is PASS as a static source-boundary review. It identifies concrete limitations that must be addressed before claiming persistent stop, adaptive resource intelligence, durable observability, hardware-aware model routing or physical recovery. No runtime or physical-device acceptance is claimed.
