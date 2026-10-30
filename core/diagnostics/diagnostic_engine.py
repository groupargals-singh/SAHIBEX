from __future__ import annotations

import ast
import os
import re
import socket
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ERROR_RE = re.compile(r"(traceback \(most recent call last\)|\b(error|exception|failed|failure|critical)\b)", re.I)
FRAME_RE = re.compile(r'File "([^\"]+\.py)", line (\d+), in ([^\s]+)')
SECRET_RE = re.compile(r"(?i)(token|password|secret|authorization|api[_-]?key)(\s*[:=]\s*)([^\s,;]+)")

# These are core components, not the complete internal-role catalogue.
CORE_COMPONENTS = (
    ("Master Brain", "core/brain/master_brain.py"),
    ("Intent Brain", "core/brain/intent.py"),
    ("Context / Memory Brain", "core/brain/memory_brain.py"),
    ("Planning / Reasoning", "core/brain/reasoning_coordinator.py"),
    ("Research & Learning Brain", "core/brain/research_learning_brain.py"),
    ("Knowledge Brain", "core/brain/knowledge_brain.py"),
    ("Tool / Execution Brain", "core/brain/tool_brain.py"),
    ("Permission Gateway", "tools/permission_gateway.py"),
    ("Verification Engine", "core/brain/master_brain.py"),
    ("Child Brain Registry", "core/brain/child_instance_registry.py"),
    ("Library Brain", "core/brain/library_brain.py"),
    ("Test Brain", "core/brain/test_brain.py"),
    ("Vision / OCR", "core/brain/ocr_runtime.py"),
    ("Speech Recognition", "core/brain/speech_recognition.py"),
    ("Neural TTS", "core/brain/neural_tts.py"),
    ("Media Bridge", "tools/android_companion_media_server.py"),
    ("Diagnostic Engine", "core/diagnostics/diagnostic_engine.py"),
)


def _discover_internal_roles(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read role definitions and explicit MasterBrain handler registrations from AST."""
    team_path = root / "core/brain/internal_brain_team.py"
    master_path = root / "core/brain/master_brain.py"
    if not team_path.is_file() or not master_path.is_file():
        return [], {"catalogue_available": False, "error": "role source file missing"}
    try:
        team_tree = ast.parse(team_path.read_text(encoding="utf-8"))
        master_tree = ast.parse(master_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:
        return [], {"catalogue_available": False, "error": type(exc).__name__}
    role_map: dict[str, dict[str, Any]] = {}
    for node in ast.walk(team_tree):
        if not isinstance(node, ast.ClassDef) or node.name != "InternalBrainTeam":
            continue
        for member in node.body:
            if not isinstance(member, ast.Assign):
                continue
            if not any(isinstance(target, ast.Name) and target.id == "ROLE_PURPOSES" for target in member.targets):
                continue
            if not isinstance(member.value, ast.Dict):
                continue
            for key, value in zip(member.value.keys, member.value.values):
                if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                    continue
                purpose = ""
                if isinstance(value, (ast.Tuple, ast.List)) and value.elts and isinstance(value.elts[0], ast.Constant):
                    purpose = str(value.elts[0].value)
                role_map[key.value] = {"role_id": key.value, "purpose": purpose}
    registered: dict[str, int] = {}
    for node in ast.walk(master_tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute) or node.func.attr != "register_handler" or not node.args:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            registered[arg.value] = node.lineno
    roles = []
    for role_id, item in role_map.items():
        line = registered.get(role_id)
        roles.append({
            **item,
            "department": "internal",
            "handler_registered_in_master_brain": line is not None,
            "registration_source": "core/brain/master_brain.py",
            "registration_line": line,
            "status": "HANDLER_REGISTERED_NOT_FUNCTION_TESTED" if line is not None else "DEFINED_NO_HANDLER",
        })
    roles.sort(key=lambda item: item["role_id"])
    return roles, {
        "catalogue_available": True,
        "defined_roles": len(role_map),
        "unique_role_ids": len(set(role_map)),
        "registered_handlers": sum(1 for role in roles if role["handler_registered_in_master_brain"]),
        "unregistered_handlers": sum(1 for role in roles if not role["handler_registered_in_master_brain"]),
        "registration_method": "AST inspection of explicit MasterBrain.register_handler calls",
        "runtime_invocation_verified": False,
    }


def _tcp_check(port: int, timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False


def _safe_line(line: str) -> str:
    line = SECRET_RE.sub(r"\1\2[REDACTED]", line)
    return line[:500]


def _recent_errors(log_dir: Path, limit: int = 30) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if not log_dir.is_dir():
        return found
    files = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:40]
    for path in files:
        try:
            if path.stat().st_size > 2_000_000:
                with path.open("rb") as stream:
                    stream.seek(-1_000_000, os.SEEK_END)
                    raw = stream.read().decode("utf-8", "replace")
            else:
                raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = raw.splitlines()
        index = 0
        while index < len(lines):
            line = lines[index]
            if not ERROR_RE.search(line):
                index += 1
                continue
            # Treat a traceback as one event: capture its final Python frame and
            # terminal exception instead of emitting one record per stack line.
            end = index
            if "traceback (most recent call last)" in line.lower():
                while end + 1 < len(lines) and end - index < 80:
                    end += 1
                    if re.search(r"^[A-Za-z_][\w.]*?(Error|Exception|Interrupt):", lines[end].strip()):
                        break
            block = lines[index:end + 1]
            frames = [FRAME_RE.search(part) for part in block]
            frames = [match for match in frames if match]
            frame = frames[-1] if frames else None
            terminal = next((part.strip() for part in reversed(block)
                             if re.search(r"^[A-Za-z_][\w.]*?(Error|Exception|Interrupt):", part.strip())), line.strip())
            lower = terminal.lower()
            severity = "WARNING" if "brokenpipeerror" in lower or "connectionreseterror" in lower else "ERROR"
            item: dict[str, Any] = {
                "log": path.name,
                "line": index + 1,
                "log_modified_at_unix": int(path.stat().st_mtime),
                "message": _safe_line(terminal),
                "source_file": None,
                "source_line": None,
                "function": None,
                "severity": severity,
            }
            if frame:
                candidate = Path(frame.group(1))
                try:
                    item["source_file"] = str(candidate.relative_to(ROOT)) if candidate.is_absolute() and ROOT in candidate.parents else str(candidate)
                except ValueError:
                    item["source_file"] = str(candidate)
                item["source_line"] = int(frame.group(2))
                item["function"] = frame.group(3)
            found.append(item)
            if len(found) >= limit:
                return found
            index = end + 1 if end > index else index + 1
    return found


def collect_diagnostics(root: Path | str = ROOT, *, now: float | None = None) -> dict[str, Any]:
    """Collect bounded, read-only diagnostics. No code is executed or modified."""
    base = Path(root).resolve()
    brains = []
    for name, relative in CORE_COMPONENTS:
        path = base / relative
        exists = path.is_file()
        brains.append({
            "name": name,
            "file": relative,
            "file_present": exists,
            "status": "DISCOVERED_NOT_LIVE_TESTED" if exists else "MISSING",
            "evidence": "source file exists; runtime health not inferred" if exists else "expected source file not found",
        })
    ports = [
        {"name": "Media Bridge", "port": 38742, "online": _tcp_check(38742)},
        {"name": "Local Model API", "port": 8080, "online": _tcp_check(8080)},
    ]
    errors = _recent_errors(base / "logs")
    roles, role_summary = _discover_internal_roles(base)
    try:
        from core.diagnostics.flow_tracker import recent_dispatches
        dispatch_events = recent_dispatches(50)
    except Exception:
        dispatch_events = []
    missing = sum(1 for brain in brains if not brain["file_present"])
    live_checks = [item["online"] for item in ports]
    if missing or any(not value for value in live_checks) or errors:
        overall = "ATTENTION_REQUIRED"
    else:
        overall = "SOURCE_DISCOVERED_LIVE_CHECKS_PASS_ERRORS_REVIEW_REQUIRED" if errors else "LIMITED_CHECKS_PASS"
    return {
        "success": True,
        "generated_at_unix": int(time.time() if now is None else now),
        "mode": "READ_ONLY",
        "overall_status": overall,
        "summary": {
            "catalogued_components": len(brains),
            "source_files_present": len(brains) - missing,
            "internal_roles_defined": role_summary.get("defined_roles", 0),
            "internal_handlers_registered": role_summary.get("registered_handlers", 0),
            "internal_handlers_unregistered": role_summary.get("unregistered_handlers", 0),
            "source_files_missing": missing,
            "live_services_online": sum(1 for item in ports if item["online"]),
            "live_services_checked": len(ports),
            "recent_error_records": len(errors),
        },
        "brains": brains,
        "internal_roles": roles,
        "role_summary": role_summary,
        "recent_dispatch_events": dispatch_events,
        "data_flow_edges": [
            {"from": "user_input", "to": "intent", "kind": "architecture_path", "live_traced": False},
            {"from": "intent", "to": "context", "kind": "architecture_path", "live_traced": False},
            {"from": "context", "to": "planner", "kind": "architecture_path", "live_traced": False},
            {"from": "planner", "to": "permission", "kind": "architecture_path", "live_traced": False},
            {"from": "permission", "to": "tool_execution", "kind": "architecture_path", "live_traced": False},
            {"from": "tool_execution", "to": "verification", "kind": "architecture_path", "live_traced": False},
            {"from": "verification", "to": "response", "kind": "architecture_path", "live_traced": False},
        ],
        "services": ports,
        "errors": errors,
        "limitations": [
            "A source file existing does not prove that a Brain is active or working.",
            "Only the listed local TCP services are checked live in this version.",
            "Internal role handler registration is discovered from source AST; individual handler execution is not tested by this report.",
            "Data-flow edges describe the approved architecture path and are not live per-request traces.",
            "Dispatch events are process-local and in-memory; they contain role IDs/status/timing only and reset when the process restarts.",
            "Errors are discovered from recent *.log files; missing logs do not prove there were no errors.",
            "No source code, settings, credentials, or protected actions are modified.",
        ],
    }
