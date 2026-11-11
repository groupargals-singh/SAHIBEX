from __future__ import annotations

import os
import select
import sys
import time
from datetime import datetime, time as datetime_time, timedelta
from pathlib import Path

from core.brain.master_brain import MasterBrain
from core.brain.sahibex_execution_loop import SahibexExecutionLoop
from core.brain.wake_sleep_state import WakeSleepController, WakeSleepState
from core.research.persistent_memory_knowledge_graph import PersistentMemoryKnowledgeGraph


def build_runtime_components(
    *,
    project_root: Path | None = None,
    brain: MasterBrain | None = None,
):
    """Build the CLI execution loop and graph on Mother's shared database."""
    root = (
        Path(project_root).resolve()
        if project_root is not None
        else Path(__file__).resolve().parents[1]
    )
    active_brain = brain or MasterBrain()
    database_path = Path(active_brain.mother_research.storage.database_path)
    if str(database_path) == ":memory:":
        raise RuntimeError(
            "The persistent knowledge graph requires the file-backed Mother Brain database."
        )
    operational_path = Path(active_brain.mother_operational.storage.database_path)
    if operational_path.resolve() != database_path.resolve():
        raise RuntimeError(
            "Mother Brain operational and research stores are not the same persistent database."
        )

    graph = PersistentMemoryKnowledgeGraph(str(database_path))
    summary = graph.summary()
    connected = (
        summary.get("persistent") is True
        and summary.get("shared_sqlite_database") is True
        and summary.get("knowledge_graph_connected") is True
    )
    if not connected:
        graph.close()
        raise RuntimeError("Persistent knowledge graph failed its runtime connection check.")

    try:
        active_brain.bind_persistent_memory_knowledge_graph(graph)
        loop = SahibexExecutionLoop(brain=active_brain, project_root=root)
    except Exception:
        graph.close()
        raise
    return active_brain, loop, graph


BANNER = """
============================================================
                 SAHIBEX PERSONAL AI
============================================================
 Master Brain Runtime
 Intent + Planning + Authority + Permission + Verification
 Idle Sleep Mode: enabled by default (configurable)
============================================================
Commands: status | sleep | wake | sleepmode on | sleepmode off | exit
============================================================
"""


def print_result(result) -> None:
    print()
    print("------------------------------------------------------------")
    print("SAHIBEX")
    print("------------------------------------------------------------")
    print(f"Message              : {result.message}")
    print(f"Intent               : {result.intent}")
    print(f"Intent confidence    : {result.intent_confidence:.2f}")
    print(f"Action               : {result.action}")
    print(f"Action confidence    : {result.action_confidence:.2f}")
    print(f"Risk                 : {result.risk}")
    print(f"Authority decision   : {result.authority_decision}")
    print(f"Permission allowed   : {result.permission_allowed}")
    print(f"Confirmation needed  : {result.confirmation_required}")
    print(f"Plan created         : {result.plan_created}")
    print(f"Task count           : {result.task_count}")
    print(f"Verification         : {result.verification_status}")
    if result.goal_id:
        print(f"Goal ID              : {result.goal_id}")
    print("------------------------------------------------------------")
    print()


def print_status(brain: MasterBrain, execution_loop: SahibexExecutionLoop,
                 knowledge_graph: PersistentMemoryKnowledgeGraph,
                 sleep_controller: WakeSleepController,
                 sleep_mode_enabled: bool, idle_seconds: int) -> None:
    print()
    print("============================================================")
    print("SAHIBEX BRAIN STATUS")
    print("============================================================")
    print("Master Brain         : ONLINE")
    print("Intent Engine        : ONLINE")
    print("Context Manager      : ONLINE")
    print("Master Planner       : ONLINE")
    print("Constitution         : ACTIVE")
    print("Permission Engine    : ONLINE")
    print("Verification Engine  : ONLINE")
    print(f"Execution Loop       : ONLINE (v{execution_loop.VERSION})")
    graph_status = knowledge_graph.summary()
    print("Persistent Graph     : CONNECTED" if graph_status.get("knowledge_graph_connected") is True else "Persistent Graph     : NOT VERIFIED")
    print(f"Graph Associations   : {graph_status.get('association_count', 0)}")
    print("Graph DB             : Mother Brain shared SQLite store")
    roles = brain.internal_brain_team.roles()
    executable_roles = sum(1 for role in roles if role.handler_registered)
    print(f"Internal Brain Roles : {len(roles)} defined; {executable_roles} handlers connected")
    print("Child Brain Framework : PRESENT (registry/lifecycle code exists)")
    print("Persistent Child E2E  : NOT VERIFIED (restart + live task acceptance pending)")
    print("Protected Actions    : CONTROLLED")
    print("User Authority       : FINAL")
    print(f"Runtime State        : {sleep_controller.state.value.upper()}")
    print(f"Idle Sleep Mode      : {'ON' if sleep_mode_enabled else 'OFF'}")
    print(f"Idle Sleep Timeout   : {idle_seconds} seconds")
    print("Model Policy         : model stays loaded in this phase; no auto-kill")
    print("============================================================")
    print()


def _read_input(timeout: float | None) -> str | None:
    """Read terminal input with an optional idle timeout; None means timeout."""
    if timeout is None:
        line = sys.stdin.readline()
        return line if line else ""
    ready, _, _ = select.select([sys.stdin], [], [], max(0.0, timeout))
    if not ready:
        return None
    line = sys.stdin.readline()
    return line if line else ""


def main() -> None:
    os.environ.setdefault("SAHIBEX_MODEL_PROVIDER", "local")
    # Enable the optional model-backed semantic fallback by default only for
    # the local provider. SemanticIntentBrain performs a 1s health preflight,
    # so an offline model never causes a long request stall.
    if os.getenv("SAHIBEX_MODEL_PROVIDER", "").strip().lower() == "local":
        os.environ.setdefault("SAHIBEX_SEMANTIC_INTENT_ENABLED", "1")
    os.environ.setdefault("SAHIBEX_SEARCH_BACKEND", "google_news_rss")
    os.environ.setdefault(
        "SAHIBEX_AUTONOMOUS_CHECKPOINT_PATH",
        str(Path(__file__).resolve().parents[1] / "data" / "runtime" / "autonomous_work_checkpoints.json"),
    )
    os.environ.setdefault(
        "SAHIBEX_SELF_IMPROVEMENT_AUDIT_DB",
        str(Path(__file__).resolve().parents[1] / "data" / "runtime" / "self_improvement_audit.sqlite3"),
    )

    try:
        idle_seconds = max(30, int(os.getenv("SAHIBEX_IDLE_SLEEP_SECONDS", "300")))
    except ValueError:
        idle_seconds = 300
    sleep_mode_enabled = os.getenv("SAHIBEX_IDLE_SLEEP_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}

    brain, execution_loop, knowledge_graph = build_runtime_components()
    sleep_controller = WakeSleepController()
    sleep_controller.wake("main_runtime_start")
    last_activity = time.monotonic()
    print(BANNER, flush=True)
    print(f"SAHIBEX > Idle sleep is {'ON' if sleep_mode_enabled else 'OFF'}; timeout={idle_seconds}s.", flush=True)

    try:
        while True:
            timeout = None
            if sleep_mode_enabled and sleep_controller.state is WakeSleepState.AWAKE:
                timeout = max(0.0, idle_seconds - (time.monotonic() - last_activity))
            try:
                user_input = _read_input(timeout)
            except (KeyboardInterrupt, EOFError):
                print("\\nSAHIBEX stopped by terminal interruption.", flush=True)
                break

            if user_input is None:
                if sleep_controller.state is WakeSleepState.AWAKE:
                    sleep_controller.sleep("idle_timeout")
                    print("\\nSAHIBEX > SLEEP MODE: idle timeout reached. Root brain remains listening; enter a task to wake.", flush=True)
                continue

            user_input = user_input.strip()
            if not user_input:
                if not sys.stdin.isatty():
                    print("SAHIBEX > Input stream closed; interactive runtime cannot continue. Use a persistent PTY or companion task endpoint.", flush=True)
                    break
                continue

            last_activity = time.monotonic()
            lowered = user_input.lower()
            if lowered in {"exit", "quit", "q"}:
                print("SAHIBEX > Session closed by user.", flush=True)
                break
            if lowered in {"status", "/status"}:
                print_status(brain, execution_loop, knowledge_graph, sleep_controller, sleep_mode_enabled, idle_seconds)
                continue
            if lowered in {"sleepmode on", "sleep mode on"}:
                sleep_mode_enabled = True
                print(f"SAHIBEX > Idle sleep mode ON ({idle_seconds}s timeout).", flush=True)
                continue
            if lowered in {"sleepmode off", "sleep mode off"}:
                sleep_mode_enabled = False
                if sleep_controller.state is WakeSleepState.SLEEPING:
                    sleep_controller.wake("sleep_mode_disabled")
                print("SAHIBEX > Idle sleep mode OFF.", flush=True)
                continue
            if lowered == "sleep":
                if sleep_controller.state is WakeSleepState.AWAKE:
                    sleep_controller.sleep("manual_sleep")
                print("SAHIBEX > SLEEP MODE. Root brain remains listening; enter 'wake' or a task to resume.", flush=True)
                continue
            if lowered == "wake":
                if sleep_controller.state is WakeSleepState.SLEEPING:
                    sleep_controller.wake("manual_wake")
                last_activity = time.monotonic()
                print("SAHIBEX > AWAKE. Ready for tasks.", flush=True)
                continue

            if sleep_controller.state is WakeSleepState.SLEEPING:
                sleep_controller.wake("incoming_task")
                print("SAHIBEX > WAKING for incoming task.", flush=True)
            try:
                result = execution_loop.process(user_input)
                print_result(result.brain)
                print(f"Execution Lifecycle   : {result.status}")
                print(f"Execution Verified    : {result.metadata.get('verified', result.brain.verification_status == 'VERIFIED')}")
                print(f"Execution Audit       : {result.metadata.get('audit_recorded', 'not_required')}")
            except Exception as exc:
                reason = str(exc).strip() or exc.__class__.__name__
                print(f"SAHIBEX > TASK FAILED SAFELY: {reason}", flush=True)
            last_activity = time.monotonic()

    finally:
        knowledge_graph.close()


if __name__ == "__main__":
    main()
