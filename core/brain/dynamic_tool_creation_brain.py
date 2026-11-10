"""Human-approved, declarative dynamic tool creation for SAHIBEX.

Generated tools are data-only plans over an allowlist of existing read-only
primitives. This module never evaluates generated Python, imports generated
modules, invokes a shell, or grants protected permissions.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4
import threading
import time
import uuid

from tools.registry import ToolRegistry
from security.audit.audit_logger import AuditLogger


_NAME = re.compile(r"^[a-z][a-z0-9_]{2,47}$")
_ALLOWED_OPERATIONS = frozenset({"list_directory", "read_file", "file_info", "search_local_files"})
_ALLOWED_ARGUMENTS = {
    "list_directory": frozenset({"path"}),
    "read_file": frozenset({"path", "max_bytes"}),
    "file_info": frozenset({"path"}),
    "search_local_files": frozenset({"query", "path", "max_results"}),
}


@dataclass(frozen=True)
class DynamicToolStep:
    operation: str
    arguments: dict[str, Any]

    def __post_init__(self) -> None:
        if isinstance(self.arguments, dict):
            # Detach from caller-owned dictionaries so later caller mutations
            # cannot silently rewrite an already staged proposal.
            import copy
            object.__setattr__(self, "arguments", copy.deepcopy(self.arguments))


@dataclass(frozen=True)
class DynamicToolSpec:
    name: str
    description: str
    steps: tuple[DynamicToolStep, ...]

    def __post_init__(self) -> None:
        if isinstance(self.steps, list):
            object.__setattr__(self, "steps", tuple(self.steps))
        if not isinstance(self.steps, tuple):
            raise TypeError("steps must be a tuple or list")
        if not all(isinstance(step, DynamicToolStep) for step in self.steps):
            raise TypeError("every step must be DynamicToolStep")


@dataclass(frozen=True)
class DynamicToolCandidate:
    candidate_id: str
    spec: DynamicToolSpec
    sha256: str
    status: str
    findings: tuple[str, ...]
    created_at: str


class DynamicToolCreationBrain:
    """Design, statically validate, stage, approve and rollback safe tools."""

    VERSION = "1.0"
    MAX_STEPS = 8
    MAX_DESCRIPTION = 240
    MAX_READ_CHARS = 20_000
    MAX_RESULT_BYTES = 64_000
    MAX_EXECUTION_SECONDS = 5.0
    MAX_SEARCH_FILES = 500
    MAX_SEARCH_FILE_BYTES = 256_000
    MAX_MANIFEST_BYTES = 128_000
    MAX_CANDIDATES = 500

    def __init__(
        self,
        registry: ToolRegistry,
        project_root: Path,
        *,
        approval_checker: Callable[[str], bool] | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        if not isinstance(registry, ToolRegistry):
            raise TypeError("registry must be ToolRegistry")
        self.registry = registry
        self.project_root = Path(project_root).resolve()
        self.approval_checker = approval_checker
        self.audit_logger = audit_logger or AuditLogger(self.project_root / "security" / "audit")
        self._candidates: dict[str, DynamicToolCandidate] = {}
        self._active: dict[str, str] = {}
        self._lock = threading.RLock()
        self._execution_metrics: dict[str, dict[str, Any]] = {}
        self.restore_active_manifests()

    @staticmethod
    def _canonical(spec: DynamicToolSpec) -> bytes:
        payload = {
            "name": spec.name,
            "description": spec.description,
            "steps": [asdict(step) for step in spec.steps],
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    def validate(self, spec: DynamicToolSpec, *, exclude_candidate_id: str | None = None) -> tuple[str, ...]:
        findings: list[str] = []
        if not isinstance(spec, DynamicToolSpec):
            return ("spec must be DynamicToolSpec",)
        if not isinstance(spec.name, str) or not _NAME.fullmatch(spec.name):
            findings.append("tool name must be 3-48 lowercase letters, digits or underscores and start with a letter")
        if not isinstance(spec.description, str) or not spec.description.strip() or len(spec.description) > self.MAX_DESCRIPTION:
            findings.append("description must contain 1-240 characters")
        if not isinstance(spec.steps, tuple):
            findings.append("steps must be a tuple")
        if isinstance(spec.name, str):
            duplicate_candidate = any(
                item.candidate_id != exclude_candidate_id
                and item.spec.name == spec.name and item.status in {"STAGED", "ACTIVE"}
                for item in self._candidates.values()
            )
            if self.registry.has(spec.name) or spec.name in self._active or duplicate_candidate:
                findings.append("tool name is already registered, staged or active")
        if not isinstance(spec.steps, tuple) or not 1 <= len(spec.steps) <= self.MAX_STEPS:
            findings.append(f"steps must be a tuple containing 1-{self.MAX_STEPS} steps")
            return tuple(findings)
        for index, step in enumerate(spec.steps):
            if not isinstance(step, DynamicToolStep):
                findings.append(f"step {index}: invalid step type")
                continue
            if not isinstance(step.operation, str) or step.operation not in _ALLOWED_OPERATIONS:
                findings.append(f"step {index}: operation is not allowlisted")
                continue
            if not isinstance(step.arguments, dict):
                findings.append(f"step {index}: arguments must be an object")
                continue
            if not all(isinstance(key, str) for key in step.arguments):
                findings.append(f"step {index}: argument names must be strings")
                continue
            required = {
                "list_directory": {"path"},
                "read_file": {"path"},
                "file_info": {"path"},
                "search_local_files": {"query"},
            }[step.operation]
            missing = required - set(step.arguments)
            if missing:
                findings.append(f"step {index}: missing required arguments: {', '.join(sorted(missing))}")
            unknown = set(step.arguments) - _ALLOWED_ARGUMENTS[step.operation]
            if unknown:
                findings.append(f"step {index}: unsupported arguments: {', '.join(sorted(unknown))}")
            for key, value in step.arguments.items():
                if key in {"path"} and (not isinstance(value, str) or not value.strip()):
                    findings.append(f"step {index}: {key} must be a non-empty relative path")
                if key == "path" and isinstance(value, str):
                    target = (self.project_root / value).resolve()
                    try:
                        target.relative_to(self.project_root)
                    except ValueError:
                        findings.append(f"step {index}: path escapes the project root")
                if key == "query" and (not isinstance(value, str) or not value.strip() or len(value) > 500):
                    findings.append(f"step {index}: query must be 1-500 characters")
                if key == "path" and isinstance(value, str) and len(value) > 2048:
                    findings.append(f"step {index}: path exceeds 2048 characters")
                if key == "max_bytes" and (not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= self.MAX_READ_CHARS):
                    findings.append(f"step {index}: max_bytes must be 1-{self.MAX_READ_CHARS}")
                if key == "max_results" and (not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 100):
                    findings.append(f"step {index}: max_results must be 1-100")
        return tuple(findings)

    def propose_from_request(self, request: str, *, context: dict[str, Any] | None = None) -> DynamicToolCandidate:
        """Translate a narrowly supported request into a staged, never-active tool.

        A caller may supply an exact declarative spec in context['spec'].
        Natural-language support is intentionally deterministic and limited to
        safe local read operations; ambiguous requests are rejected.
        """
        if not isinstance(request, str) or not request.strip() or len(request) > 2000:
            raise ValueError("request must contain 1-2000 characters")
        context = context or {}
        if not isinstance(context, dict):
            raise TypeError("context must be a dictionary")
        if len(context) > 32:
            raise ValueError("proposal context contains too many fields")
        raw = context.get("spec")
        if raw is not None:
            if not isinstance(raw, dict) or set(raw) != {"name", "description", "steps"}:
                raise ValueError("spec must contain exactly name, description and steps")
            if not isinstance(raw["steps"], list):
                raise ValueError("spec.steps must be a list")
            steps = []
            for item in raw["steps"]:
                if not isinstance(item, dict) or set(item) != {"operation", "arguments"}:
                    raise ValueError("each step must contain exactly operation and arguments")
                steps.append(DynamicToolStep(item["operation"], item["arguments"]))
            spec = DynamicToolSpec(raw["name"], raw["description"], tuple(steps))
            return self.stage(spec)

        text = request.casefold()
        forbidden = ("delete", "write", "modify", "edit", "execute", "run command", "shell", "network", "upload", "send", "install", "credential", "password", "permission", "system change")
        if any(term in text for term in forbidden):
            raise ValueError("request contains a protected or unsupported action; only local read-only tool proposals are supported")
        operations = []
        if any(term in text for term in ("list files", "list directory", "show files", "directory listing")):
            operations.append(("list_directory", {"path": context.get("path", ".")}))
        if any(term in text for term in ("read file", "show file content", "open file")):
            path = context.get("path")
            if not isinstance(path, str) or not path.strip():
                raise ValueError("file-reading proposal requires context.path")
            operations.append(("read_file", {"path": path, "max_bytes": context.get("max_bytes", 4000)}))
        if any(term in text for term in ("file info", "file details", "file metadata")):
            path = context.get("path")
            if not isinstance(path, str) or not path.strip():
                raise ValueError("file-info proposal requires context.path")
            operations.append(("file_info", {"path": path}))
        if any(term in text for term in ("search files", "search project", "find text in files")):
            query = context.get("query")
            if not isinstance(query, str) or not query.strip():
                raise ValueError("file-search proposal requires context.query")
            operations.append(("search_local_files", {"query": query, "path": context.get("path", "."), "max_results": context.get("max_results", 20)}))
        if len(operations) != 1:
            raise ValueError("request is ambiguous or unsupported; provide an exact context.spec with one or more allowlisted read-only steps")
        operation, arguments = operations[0]
        name = context.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("proposal requires an explicit context.name")
        description = context.get("description", f"User-proposed read-only {operation} tool")
        return self.stage(DynamicToolSpec(name, description, (DynamicToolStep(operation, arguments),)))

    def stage(self, spec: DynamicToolSpec) -> DynamicToolCandidate:
        with self._lock:
            return self._stage_locked(spec)

    def _stage_locked(self, spec: DynamicToolSpec) -> DynamicToolCandidate:
        if len(self._candidates) >= self.MAX_CANDIDATES:
            raise RuntimeError("dynamic tool candidate capacity reached")
        findings = self.validate(spec)
        try:
            canonical = self._canonical(spec)
        except (TypeError, ValueError) as exc:
            raise ValueError("tool specification must contain JSON-compatible data") from exc
        candidate = DynamicToolCandidate(
            candidate_id=str(uuid4()),
            spec=spec,
            sha256=hashlib.sha256(canonical).hexdigest(),
            status="REJECTED" if findings else "STAGED",
            findings=findings,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        try:
            self._persist_manifest(candidate)
            self._record_lifecycle(
                candidate, action=("dynamic_tool_reject" if findings else "dynamic_tool_stage"),
                allowed=not findings,
                reason=("; ".join(findings) if findings else "candidate staged for explicit human review"),
            )
        except Exception:
            (self.project_root / "data" / "dynamic_tools" / f"{candidate.candidate_id}.json").unlink(missing_ok=True)
            raise
        self._candidates[candidate.candidate_id] = candidate
        return candidate

    def approve(self, candidate_id: str, *, user_approved: bool = False) -> DynamicToolCandidate:
        with self._lock:
            return self._approve_locked(candidate_id, user_approved=user_approved)

    def _approve_locked(self, candidate_id: str, *, user_approved: bool = False) -> DynamicToolCandidate:
        candidate = self._candidates.get(candidate_id)
        if candidate is None:
            raise KeyError("unknown dynamic tool candidate")
        if candidate.status != "STAGED":
            raise ValueError(f"candidate is not approvable: {candidate.status}")
        if not user_approved:
            raise PermissionError("explicit human approval is required")
        if self.approval_checker is not None and not self.approval_checker(candidate_id):
            raise PermissionError("canonical approval policy denied activation")
        if self.validate(candidate.spec, exclude_candidate_id=candidate_id):
            raise ValueError("candidate failed revalidation")
        if hashlib.sha256(self._canonical(candidate.spec)).hexdigest() != candidate.sha256:
            raise ValueError("candidate integrity check failed")
        handler = self._build_handler(candidate.spec)
        self.registry.register(
            name=candidate.spec.name,
            description=candidate.spec.description,
            handler=handler,
            read_only=True,
            requires_confirmation=False,
            protected_action=None,
        )
        self._active[candidate.spec.name] = candidate_id
        approved = replace(candidate, status="ACTIVE")
        self._candidates[candidate_id] = approved
        try:
            self._persist_manifest(approved)
            self._record_lifecycle(approved, action="dynamic_tool_approve_activate", allowed=True, reason="explicit user approval and static revalidation passed")
        except Exception:
            self.registry.unregister(candidate.spec.name)
            self._active.pop(candidate.spec.name, None)
            self._candidates[candidate_id] = candidate
            self._persist_manifest(candidate)
            raise
        return approved

    def rollback(self, candidate_id: str, *, user_approved: bool = False) -> DynamicToolCandidate:
        with self._lock:
            return self._rollback_locked(candidate_id, user_approved=user_approved)

    def _rollback_locked(self, candidate_id: str, *, user_approved: bool = False) -> DynamicToolCandidate:
        candidate = self._candidates.get(candidate_id)
        if candidate is None:
            raise KeyError("unknown dynamic tool candidate")
        if candidate.status != "ACTIVE":
            raise ValueError("only an active candidate can be rolled back")
        if not user_approved:
            raise PermissionError("explicit human approval is required for rollback")
        name = candidate.spec.name
        # Registry removal is deliberately narrow and only targets this brain's own entry.
        if self._active.get(name) != candidate_id:
            raise PermissionError("candidate does not own the active registry entry")
        self.registry.unregister(name)
        self._active.pop(name, None)
        rolled_back = replace(candidate, status="ROLLED_BACK")
        self._candidates[candidate_id] = rolled_back
        try:
            self._persist_manifest(rolled_back)
            self._record_lifecycle(rolled_back, action="dynamic_tool_rollback", allowed=True, reason="explicit user-approved rollback completed")
        except Exception:
            self.registry.register(
                name=candidate.spec.name,
                description=candidate.spec.description,
                handler=self._build_handler(candidate.spec),
                read_only=True,
                requires_confirmation=False,
                protected_action=None,
            )
            self._active[name] = candidate_id
            self._candidates[candidate_id] = candidate
            self._persist_manifest(candidate)
            raise
        return rolled_back

    def restore_active_manifests(self) -> list[str]:
        """Restore only intact, previously approved declarative manifests.

        Invalid, tampered, duplicate, or unsupported manifests are skipped.
        This never imports or executes generated source code.
        """
        directory = self.project_root / "data" / "dynamic_tools"
        restored: list[str] = []
        if not directory.is_dir():
            return restored
        for path in sorted(directory.glob("*.json")):
            try:
                if path.stat().st_size > self.MAX_MANIFEST_BYTES:
                    continue
                payload = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(payload, dict):
                    continue
                if not isinstance(payload.get("steps"), list) or not 1 <= len(payload["steps"]) <= self.MAX_STEPS:
                    continue
                if not isinstance(payload.get("created_at"), str) or len(payload["created_at"]) > 80:
                    continue
                candidate_id = str(uuid.UUID(str(payload.get("candidate_id", ""))))
                if path.stem != candidate_id:
                    continue
                if payload.get("version") != self.VERSION or payload.get("status") not in {"ACTIVE", "STAGED", "REJECTED", "ROLLED_BACK"}:
                    continue
                steps = tuple(
                    DynamicToolStep(item["operation"], item["arguments"])
                    for item in payload["steps"]
                    if isinstance(item, dict) and set(item) == {"operation", "arguments"}
                    and isinstance(item["arguments"], dict)
                )
                spec = DynamicToolSpec(payload["name"], payload["description"], steps)
                digest = hashlib.sha256(self._canonical(spec)).hexdigest()
                if digest != payload.get("sha256"):
                    continue
                if self.validate(spec):
                    continue
                if candidate_id in self._candidates:
                    continue
                if len(steps) != len(payload["steps"]):
                    continue
                if payload["status"] == "ACTIVE" and spec.name in self._active:
                    continue
                candidate = DynamicToolCandidate(
                    candidate_id=candidate_id,
                    spec=spec,
                    sha256=digest,
                    status=str(payload["status"]),
                    findings=(),
                    created_at=str(payload["created_at"]),
                )
                self._candidates[candidate_id] = candidate
                if candidate.status == "ACTIVE":
                    self.registry.register(
                        name=spec.name,
                        description=spec.description,
                        handler=self._build_handler(spec),
                        read_only=True,
                        requires_confirmation=False,
                        protected_action=None,
                    )
                    self._active[spec.name] = candidate_id
                    restored.append(spec.name)
            except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
                continue
        return restored

    def design_report(self, request: str, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return a bounded design assessment without staging or activating anything."""
        try:
            candidate = self.propose_from_request(request, context=context)
        except (ValueError, TypeError, KeyError) as exc:
            return {"accepted": False, "status": "REJECTED", "reason": str(exc)[:300],
                    "available_operations": sorted(_ALLOWED_OPERATIONS)}
        # A design report is still a staged proposal; the caller must review and approve it.
        return {"accepted": candidate.status == "STAGED", "status": candidate.status,
                "candidate_id": candidate.candidate_id, "name": candidate.spec.name,
                "step_count": len(candidate.spec.steps), "sha256": candidate.sha256,
                "findings": list(candidate.findings), "approval_required": True,
                "activated": False}

    def verify_candidate(self, candidate_id: str) -> dict[str, Any]:
        """Statically verify a staged candidate; does not execute its operations."""
        with self._lock:
            candidate = self._candidates.get(candidate_id)
        if candidate is None:
            raise KeyError("unknown dynamic tool candidate")
        findings = list(self.validate(candidate.spec, exclude_candidate_id=candidate_id))
        digest_ok = hashlib.sha256(self._canonical(candidate.spec)).hexdigest() == candidate.sha256
        if not digest_ok:
            findings.append("candidate digest mismatch")
        primitive_checks = []
        for step in candidate.spec.steps:
            try:
                primitive = self.registry.get(step.operation)
                ok = primitive.read_only and primitive.protected_action is None
            except KeyError:
                ok = False
            primitive_checks.append({"operation": step.operation, "available_read_only": ok})
            if not ok:
                findings.append(f"primitive unavailable or not read-only: {step.operation}")
        return {"candidate_id": candidate_id, "valid": not findings,
                "digest_valid": digest_ok, "findings": findings,
                "primitive_checks": primitive_checks, "executed": False}

    def lifecycle_status(self) -> dict[str, Any]:
        """Expose counts and safe capability boundaries for diagnostics."""
        with self._lock:
            counts = {status: 0 for status in ("STAGED", "REJECTED", "ACTIVE", "ROLLED_BACK")}
            for candidate in self._candidates.values():
                if candidate.status in counts:
                    counts[candidate.status] += 1
            active_names = sorted(self._active)
            metrics = {name: dict(value) for name, value in self._execution_metrics.items()}
        return {"version": self.VERSION, "candidate_counts": counts,
                "active_tool_names": active_names,
                "execution_metrics": metrics,
                "allowed_operations": sorted(_ALLOWED_OPERATIONS),
                "max_steps": self.MAX_STEPS, "max_result_bytes": self.MAX_RESULT_BYTES,
                "max_execution_seconds_soft_deadline": self.MAX_EXECUTION_SECONDS,
                "max_search_files": self.MAX_SEARCH_FILES,
                "max_search_file_bytes": self.MAX_SEARCH_FILE_BYTES,
                "max_directory_entries": 500,
                "max_read_bytes": self.MAX_READ_CHARS,
                "max_candidates": self.MAX_CANDIDATES,
                "arbitrary_code_execution": False, "network_access": False,
                "write_delete_access": False}

    def get_candidate(self, candidate_id: str) -> DynamicToolCandidate:
        with self._lock:
            return self._candidates[candidate_id]

    def list_candidates(self) -> list[DynamicToolCandidate]:
        with self._lock:
            return list(self._candidates.values())

    def _build_handler(self, spec: DynamicToolSpec):
        # Capture immutable, JSON-compatible arguments; execute only known handlers.
        steps = tuple((step.operation, dict(step.arguments)) for step in spec.steps)
        def handler(**runtime_arguments: Any) -> dict[str, Any]:
            if runtime_arguments:
                raise TypeError("dynamic tools do not accept runtime overrides")
            started = time.monotonic()
            outputs = []
            success = False
            error_code = None
            try:
                for operation, arguments in steps:
                    if time.monotonic() - started > self.MAX_EXECUTION_SECONDS:
                        raise TimeoutError("dynamic tool exceeded its execution time budget")
                    tool = self.registry.get(operation)
                    if not tool.read_only or tool.protected_action is not None:
                        raise PermissionError("dynamic tool primitive is not read-only")
                    call_arguments = dict(arguments)
                    if operation == "read_file":
                        call_arguments["max_bytes"] = min(
                            int(call_arguments.get("max_bytes", self.MAX_READ_CHARS)),
                            self.MAX_READ_CHARS,
                        )
                    if operation == "search_local_files":
                        # The existing primitive scans arbitrary numbers and sizes of
                        # files. Dynamic compositions use a bounded private scanner.
                        outputs.append(self._bounded_search(call_arguments))
                    elif operation == "list_directory":
                        outputs.append(self._bounded_list_directory(call_arguments))
                    else:
                        outputs.append(tool.handler(**call_arguments))
                    encoded = json.dumps(outputs, ensure_ascii=False, default=str).encode("utf-8")
                    if len(encoded) > self.MAX_RESULT_BYTES:
                        raise ValueError("dynamic tool aggregate result exceeds the configured output budget")
                    if time.monotonic() - started > self.MAX_EXECUTION_SECONDS:
                        raise TimeoutError("dynamic tool exceeded its execution time budget")
                success = True
                return {"tool": spec.name, "steps": outputs, "step_count": len(outputs)}
            except Exception as exc:
                error_code = type(exc).__name__
                raise
            finally:
                elapsed = time.monotonic() - started
                with self._lock:
                    previous = self._execution_metrics.get(spec.name, {})
                    self._execution_metrics[spec.name] = {
                        "calls": int(previous.get("calls", 0)) + 1,
                        "successes": int(previous.get("successes", 0)) + int(success),
                        "failures": int(previous.get("failures", 0)) + int(not success),
                        "last_duration_seconds": round(elapsed, 6),
                        "last_error_type": error_code,
                        "last_executed_at": datetime.now(timezone.utc).isoformat(),
                    }
        return handler

    def _bounded_list_directory(self, arguments: dict[str, Any]) -> dict[str, Any]:
        relative = arguments["path"]
        target = (self.project_root / relative).resolve()
        try:
            target.relative_to(self.project_root)
        except ValueError as exc:
            raise PermissionError("directory path escapes project root") from exc
        if not target.is_dir():
            raise NotADirectoryError("dynamic list target is not a directory")
        entries = []
        truncated = False
        for index, item in enumerate(sorted(target.iterdir(), key=lambda value: value.name.casefold())):
            if index >= 500:
                truncated = True
                break
            entries.append({"name": item.name, "type": "directory" if item.is_dir() else "file"})
        return {"path": str(target.relative_to(self.project_root)), "entries": entries,
                "count": len(entries), "truncated": truncated, "entry_limit": 500}

    def _bounded_search(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = arguments["query"]
        relative = arguments.get("path", ".")
        maximum = min(int(arguments.get("max_results", 20)), 100)
        root = (self.project_root / relative).resolve()
        try:
            root.relative_to(self.project_root)
        except ValueError as exc:
            raise PermissionError("search path escapes project root") from exc
        if not root.is_dir():
            raise NotADirectoryError("dynamic search root is not a directory")
        results = []
        scanned = 0
        for candidate in root.rglob("*"):
            if scanned >= self.MAX_SEARCH_FILES or len(results) >= maximum:
                break
            if not candidate.is_file():
                continue
            scanned += 1
            try:
                if candidate.stat().st_size > self.MAX_SEARCH_FILE_BYTES:
                    continue
                content = candidate.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if query.casefold() in content.casefold():
                results.append({"path": str(candidate.relative_to(self.project_root))})
        return {"query": query, "results": results, "count": len(results),
                "files_scanned": scanned, "scan_limit": self.MAX_SEARCH_FILES,
                "file_size_limit_bytes": self.MAX_SEARCH_FILE_BYTES}

    def _record_lifecycle(
        self,
        candidate: DynamicToolCandidate,
        *,
        action: str,
        allowed: bool,
        reason: str,
    ) -> None:
        """Write lifecycle evidence through SAHIBEX's canonical audit logger.

        Audit failure is fail-closed: callers must not expose a staged,
        activated, or rolled-back state without its corresponding record.
        """
        self.audit_logger.record(
            request=f"dynamic_tool_candidate:{candidate.candidate_id}",
            intent="dynamic_tool_lifecycle",
            intent_confidence=1.0,
            action=action,
            action_confidence=1.0,
            risk="read_only_tool_creation",
            permission_allowed=allowed,
            confirmation_required=True,
            reason=reason[:1000],
            execution_id=candidate.candidate_id,
        )

    def _persist_manifest(self, candidate: DynamicToolCandidate) -> None:
        directory = self.project_root / "data" / "dynamic_tools"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{candidate.candidate_id}.json"
        payload = {
            "version": self.VERSION,
            "candidate_id": candidate.candidate_id,
            "name": candidate.spec.name,
            "description": candidate.spec.description,
            "sha256": candidate.sha256,
            "status": candidate.status,
            "created_at": candidate.created_at,
            "steps": [asdict(step) for step in candidate.spec.steps],
        }
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
        temporary.replace(path)
