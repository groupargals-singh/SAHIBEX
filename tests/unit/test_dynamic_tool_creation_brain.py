from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from core.brain.dynamic_tool_creation_brain import (
    DynamicToolCreationBrain,
    DynamicToolSpec,
    DynamicToolStep,
)
from core.brain.tool_brain import ToolBrain
from core.policies.approval import PermissionEngine
from tools.registry import build_default_registry


def make_brain(tmp_path):
    registry = build_default_registry(tmp_path)
    return DynamicToolCreationBrain(registry, tmp_path), registry


def test_stage_validate_approve_and_execute_safe_declarative_tool(tmp_path):
    brain, registry = make_brain(tmp_path)
    spec = DynamicToolSpec(
        "project_inventory",
        "List project root entries",
        (DynamicToolStep("list_directory", {"path": "."}),),
    )
    candidate = brain.stage(spec)
    assert candidate.status == "STAGED"
    assert candidate.sha256
    assert not registry.has(spec.name)

    with pytest.raises(PermissionError):
        brain.approve(candidate.candidate_id)

    active = brain.approve(candidate.candidate_id, user_approved=True)
    assert active.status == "ACTIVE"
    result = registry.get(spec.name).handler()
    assert result["tool"] == spec.name
    assert result["step_count"] == 1
    assert (tmp_path / "data" / "dynamic_tools" / f"{candidate.candidate_id}.json").is_file()


@pytest.mark.parametrize(
    "spec",
    [
        DynamicToolSpec("Bad-Name", "bad", (DynamicToolStep("list_directory", {"path": "."}),)),
        DynamicToolSpec("unsafe_tool", "unsafe", (DynamicToolStep("run_command", {"command": "id"}),)),
        DynamicToolSpec("path_escape", "escape", (DynamicToolStep("read_file", {"path": "../../etc/passwd"}),)),
        DynamicToolSpec("bad_args", "bad args", (DynamicToolStep("list_directory", {"path": ".", "shell": "id"}),)),
        DynamicToolSpec("empty_steps", "empty", ()),
    ],
)
def test_rejects_invalid_or_unsafe_specs(tmp_path, spec):
    brain, registry = make_brain(tmp_path)
    candidate = brain.stage(spec)
    assert candidate.status == "REJECTED"
    assert candidate.findings
    with pytest.raises(ValueError):
        brain.approve(candidate.candidate_id, user_approved=True)
    assert not registry.has(spec.name)


def test_approval_checker_can_veto_activation(tmp_path):
    registry = build_default_registry(tmp_path)
    brain = DynamicToolCreationBrain(registry, tmp_path, approval_checker=lambda _: False)
    candidate = brain.stage(DynamicToolSpec(
        "safe_tool", "safe", (DynamicToolStep("file_info", {"path": "."}),)
    ))
    with pytest.raises(PermissionError):
        brain.approve(candidate.candidate_id, user_approved=True)
    assert not registry.has("safe_tool")


def test_rollback_requires_explicit_approval_and_removes_only_owned_tool(tmp_path):
    brain, registry = make_brain(tmp_path)
    candidate = brain.stage(DynamicToolSpec(
        "safe_tool", "safe", (DynamicToolStep("file_info", {"path": "."}),)
    ))
    brain.approve(candidate.candidate_id, user_approved=True)
    with pytest.raises(PermissionError):
        brain.rollback(candidate.candidate_id)
    rolled_back = brain.rollback(candidate.candidate_id, user_approved=True)
    assert rolled_back.status == "ROLLED_BACK"
    assert not registry.has("safe_tool")
    manifest = tmp_path / "data" / "dynamic_tools" / f"{candidate.candidate_id}.json"
    assert '"status": "ROLLED_BACK"' in manifest.read_text(encoding="utf-8")


def test_tool_brain_exposes_dynamic_tool_creation(tmp_path):
    brain = ToolBrain(PermissionEngine(), project_root=tmp_path)
    assert isinstance(brain.dynamic_tool_creation, DynamicToolCreationBrain)
    contract = brain.capability_contract()
    assert contract["dynamic_tool_design"] is True
    assert contract["dynamic_tool_arbitrary_code_execution"] is False


def test_active_tool_restores_after_restart_and_tampering_is_rejected(tmp_path):
    brain, registry = make_brain(tmp_path)
    candidate = brain.stage(DynamicToolSpec(
        "persistent_tool", "safe", (DynamicToolStep("file_info", {"path": "."}),)
    ))
    brain.approve(candidate.candidate_id, user_approved=True)

    restarted_registry = build_default_registry(tmp_path)
    restarted = DynamicToolCreationBrain(restarted_registry, tmp_path)
    assert restarted_registry.has("persistent_tool")
    assert restarted.get_candidate(candidate.candidate_id).status == "ACTIVE"

    manifest = tmp_path / "data" / "dynamic_tools" / f"{candidate.candidate_id}.json"
    payload = manifest.read_text(encoding="utf-8").replace("persistent_tool", "tampered_tool")
    manifest.write_text(payload, encoding="utf-8")
    clean_registry = build_default_registry(tmp_path)
    clean_brain = DynamicToolCreationBrain(clean_registry, tmp_path)
    assert not clean_registry.has("tampered_tool")
    assert not clean_registry.has("persistent_tool")


def test_staged_candidate_survives_restart_without_activation(tmp_path):
    brain, _ = make_brain(tmp_path)
    candidate = brain.stage(DynamicToolSpec(
        "waiting_tool", "awaiting approval",
        (DynamicToolStep("file_info", {"path": "."}),)
    ))
    restarted_registry = build_default_registry(tmp_path)
    restarted = DynamicToolCreationBrain(restarted_registry, tmp_path)
    restored = restarted.get_candidate(candidate.candidate_id)
    assert restored.status == "STAGED"
    assert not restarted_registry.has("waiting_tool")
    with pytest.raises(PermissionError):
        restarted.approve(candidate.candidate_id)


def test_dynamic_tool_lifecycle_is_written_to_canonical_audit(tmp_path):
    from security.audit.audit_logger import AuditLogger

    brain, _ = make_brain(tmp_path)
    candidate = brain.stage(DynamicToolSpec(
        "audited_tool", "audited lifecycle",
        (DynamicToolStep("file_info", {"path": "."}),)
    ))
    brain.approve(candidate.candidate_id, user_approved=True)
    brain.rollback(candidate.candidate_id, user_approved=True)

    events = AuditLogger(tmp_path / "security" / "audit").read_recent(limit=20)
    lifecycle = [event for event in events if event.get("execution_id") == candidate.candidate_id]
    assert [event["action"] for event in lifecycle] == [
        "dynamic_tool_stage",
        "dynamic_tool_approve_activate",
        "dynamic_tool_rollback",
    ]
    assert all(event["intent"] == "dynamic_tool_lifecycle" for event in lifecycle)



def test_natural_language_proposal_stages_but_never_activates(tmp_path):
    brain, registry = make_brain(tmp_path)
    candidate = brain.propose_from_request(
        "Please create a tool to list files in the project",
        context={"name": "project_file_list"},
    )
    assert candidate.status == "STAGED"
    assert not registry.has("project_file_list")
    summary = brain.list_candidates()
    assert candidate.candidate_id in {item.candidate_id for item in summary}


def test_exact_spec_proposal_supports_multiple_allowlisted_steps(tmp_path):
    brain, registry = make_brain(tmp_path)
    candidate = brain.propose_from_request(
        "build this reviewed tool",
        context={"spec": {
            "name": "project_inspector",
            "description": "Inspect project files safely",
            "steps": [
                {"operation": "list_directory", "arguments": {"path": "."}},
                {"operation": "file_info", "arguments": {"path": "README.md"}},
            ],
        }},
    )
    assert candidate.status == "STAGED"
    assert len(candidate.spec.steps) == 2
    assert not registry.has("project_inspector")


@pytest.mark.parametrize("user_text,context", [
    ("make a tool", {"name": "ambiguous_tool"}),
    ("search project files", {"name": "search_tool"}),
    ("read file", {"name": "reader"}),
    ("list files and read file", {"name": "multi_tool", "path": "README.md"}),
])
def test_ambiguous_or_incomplete_natural_language_is_rejected(tmp_path, user_text, context):
    brain, _ = make_brain(tmp_path)
    with pytest.raises(ValueError):
        brain.propose_from_request(user_text, context=context)


def test_proposal_rejects_unknown_spec_fields_and_unsafe_operation(tmp_path):
    brain, registry = make_brain(tmp_path)
    with pytest.raises(ValueError):
        brain.propose_from_request("spec", context={"spec": {
            "name": "unsafe_tool", "description": "unsafe", "extra": True,
            "steps": [{"operation": "run_command", "arguments": {"command": "id"}}],
        }})
    candidate = brain.propose_from_request("spec", context={"spec": {
        "name": "unsafe_tool", "description": "unsafe",
        "steps": [{"operation": "run_command", "arguments": {"command": "id"}}],
    }})
    assert candidate.status == "REJECTED"
    assert not registry.has("unsafe_tool")


def test_natural_language_proposal_rejects_mixed_or_protected_intent(tmp_path):
    brain, registry = make_brain(tmp_path)
    with pytest.raises(ValueError):
        brain.propose_from_request(
            "list files and delete old files",
            context={"name": "mixed_intent_tool"},
        )
    assert not registry.has("mixed_intent_tool")


def test_restored_staged_candidate_needs_fresh_explicit_approval(tmp_path):
    brain, registry = make_brain(tmp_path)
    candidate = brain.stage(DynamicToolSpec(
        "fresh_approval_tool", "approval required",
        (DynamicToolStep("file_info", {"path": "."}),)
    ))
    restarted_registry = build_default_registry(tmp_path)
    restarted = DynamicToolCreationBrain(restarted_registry, tmp_path)
    with pytest.raises(PermissionError):
        restarted.approve(candidate.candidate_id)
    assert not restarted_registry.has("fresh_approval_tool")
    activated = restarted.approve(candidate.candidate_id, user_approved=True)
    assert activated.status == "ACTIVE"


def test_audit_failure_blocks_staging_and_leaves_no_candidate_manifest(tmp_path):
    class BrokenAudit:
        def record(self, **_kwargs):
            raise OSError("audit storage unavailable")

    registry = build_default_registry(tmp_path)
    brain = DynamicToolCreationBrain(registry, tmp_path, audit_logger=BrokenAudit())
    spec = DynamicToolSpec(
        "audit_fail_tool", "must not stage without audit",
        (DynamicToolStep("file_info", {"path": "."}),)
    )
    with pytest.raises(OSError):
        brain.stage(spec)
    assert brain.list_candidates() == []
    manifest_dir = tmp_path / "data" / "dynamic_tools"
    assert not list(manifest_dir.glob("*.json")) if manifest_dir.exists() else True
    assert not registry.has("audit_fail_tool")


def test_spec_normalizes_list_steps_and_rejects_invalid_elements():
    step = DynamicToolStep("file_info", {"path": "."})
    spec = DynamicToolSpec("normalized_tool", "normalized", [step])
    assert isinstance(spec.steps, tuple)
    assert spec.steps == (step,)
    with pytest.raises(TypeError):
        DynamicToolSpec("invalid_tool", "invalid", [object()])


@pytest.mark.parametrize("operation,arguments", [
    ("list_directory", {}),
    ("read_file", {}),
    ("file_info", {}),
    ("search_local_files", {}),
])
def test_required_arguments_are_enforced(tmp_path, operation, arguments):
    brain, _ = make_brain(tmp_path)
    candidate = brain.stage(DynamicToolSpec(
        "missing_args_tool", "missing required args",
        (DynamicToolStep(operation, arguments),),
    ))
    assert candidate.status == "REJECTED"
    assert any("missing required arguments" in item for item in candidate.findings)


def test_read_file_uses_actual_primitive_max_bytes_signature(tmp_path):
    brain, registry = make_brain(tmp_path)
    (tmp_path / "sample.txt").write_text("hello world", encoding="utf-8")
    candidate = brain.stage(DynamicToolSpec(
        "bounded_reader", "Read a bounded file",
        (DynamicToolStep("read_file", {"path": "sample.txt", "max_bytes": 5}),),
    ))
    brain.approve(candidate.candidate_id, user_approved=True)
    result = registry.get("bounded_reader").handler()
    assert result["steps"][0]["content"] == "hello"
    assert result["steps"][0]["bytes_read"] == 5


def test_design_report_and_static_verification_never_activate_tool(tmp_path):
    brain, registry = make_brain(tmp_path)
    report = brain.design_report(
        "create a tool to list files", context={"name": "design_report_tool"}
    )
    assert report["accepted"] is True
    assert report["approval_required"] is True
    assert report["activated"] is False
    verification = brain.verify_candidate(report["candidate_id"])
    assert verification["valid"] is True
    assert verification["executed"] is False
    assert not registry.has("design_report_tool")


def test_lifecycle_status_reports_safe_budgets_and_capabilities(tmp_path):
    brain, _ = make_brain(tmp_path)
    status = brain.lifecycle_status()
    assert status["max_steps"] == brain.MAX_STEPS
    assert status["max_result_bytes"] == brain.MAX_RESULT_BYTES
    assert status["arbitrary_code_execution"] is False
    assert status["network_access"] is False
    assert status["write_delete_access"] is False


def test_mutating_input_arguments_after_step_creation_does_not_change_step(tmp_path):
    original = {"path": "."}
    step = DynamicToolStep("file_info", original)
    original["path"] = "../../outside"
    assert step.arguments["path"] == "."


def test_dynamic_tool_rejects_duplicate_staged_names(tmp_path):
    brain, _ = make_brain(tmp_path)
    first = brain.stage(DynamicToolSpec(
        "same_staged_name", "first",
        (DynamicToolStep("file_info", {"path": "."}),),
    ))
    second = brain.stage(DynamicToolSpec(
        "same_staged_name", "second",
        (DynamicToolStep("file_info", {"path": "."}),),
    ))
    assert first.status == "STAGED"
    assert second.status == "REJECTED"
    assert any("staged" in finding for finding in second.findings)


def test_dynamic_list_directory_has_entry_budget(tmp_path):
    brain, registry = make_brain(tmp_path)
    for index in range(510):
        (tmp_path / f"entry_{index:03}.txt").write_text("x", encoding="utf-8")
    candidate = brain.stage(DynamicToolSpec(
        "bounded_directory_list", "bounded listing",
        (DynamicToolStep("list_directory", {"path": "."}),),
    ))
    brain.approve(candidate.candidate_id, user_approved=True)
    result = registry.get("bounded_directory_list").handler()
    output = result["steps"][0]
    assert output["count"] == 500
    assert output["truncated"] is True


def test_dynamic_execution_metrics_track_success_and_failure(tmp_path):
    brain, registry = make_brain(tmp_path)
    candidate = brain.stage(DynamicToolSpec(
        "metric_tool", "metrics",
        (DynamicToolStep("file_info", {"path": "."}),),
    ))
    brain.approve(candidate.candidate_id, user_approved=True)
    registry.get("metric_tool").handler()
    metrics = brain.lifecycle_status()["execution_metrics"]["metric_tool"]
    assert metrics["calls"] == 1
    assert metrics["successes"] == 1
    assert metrics["failures"] == 0
    assert metrics["last_duration_seconds"] >= 0


def test_dynamic_search_has_file_count_and_size_limits(tmp_path):
    brain, registry = make_brain(tmp_path)
    (tmp_path / "small.txt").write_text("needle", encoding="utf-8")
    (tmp_path / "large.txt").write_bytes(b"x" * (brain.MAX_SEARCH_FILE_BYTES + 1))
    candidate = brain.stage(DynamicToolSpec(
        "bounded_search_tool", "bounded search",
        (DynamicToolStep("search_local_files", {"query": "needle", "path": ".", "max_results": 10}),),
    ))
    brain.approve(candidate.candidate_id, user_approved=True)
    result = registry.get("bounded_search_tool").handler()["steps"][0]
    result_paths = {item["path"] for item in result["results"]}
    assert "small.txt" in result_paths
    assert "large.txt" not in result_paths
    assert result["files_scanned"] <= brain.MAX_SEARCH_FILES


def test_restore_rejects_manifest_with_mismatched_filename_id(tmp_path):
    brain, _ = make_brain(tmp_path)
    candidate = brain.stage(DynamicToolSpec(
        "manifest_name_guard", "manifest",
        (DynamicToolStep("file_info", {"path": "."}),),
    ))
    manifest = tmp_path / "data" / "dynamic_tools" / f"{candidate.candidate_id}.json"
    payload = manifest.read_text(encoding="utf-8")
    import json
    data = json.loads(payload)
    data["candidate_id"] = "00000000-0000-0000-0000-000000000000"
    manifest.write_text(json.dumps(data), encoding="utf-8")
    restarted_registry = build_default_registry(tmp_path)
    restarted = DynamicToolCreationBrain(restarted_registry, tmp_path)
    assert not restarted_registry.has("manifest_name_guard")
    assert candidate.candidate_id not in {item.candidate_id for item in restarted.list_candidates()}


def test_dynamic_tool_failure_metrics_are_recorded(tmp_path):
    brain, registry = make_brain(tmp_path)
    candidate = brain.stage(DynamicToolSpec(
        "failing_metric_tool", "failure metrics",
        (DynamicToolStep("file_info", {"path": "missing.txt"}),),
    ))
    brain.approve(candidate.candidate_id, user_approved=True)
    with pytest.raises(FileNotFoundError):
        registry.get("failing_metric_tool").handler()
    metrics = brain.lifecycle_status()["execution_metrics"]["failing_metric_tool"]
    assert metrics["calls"] == 1
    assert metrics["successes"] == 0
    assert metrics["failures"] == 1
    assert metrics["last_error_type"] == "FileNotFoundError"


def test_lifecycle_status_exposes_all_resource_budgets(tmp_path):
    brain, _ = make_brain(tmp_path)
    status = brain.lifecycle_status()
    assert status["max_execution_seconds_soft_deadline"] == brain.MAX_EXECUTION_SECONDS
    assert status["max_search_files"] == brain.MAX_SEARCH_FILES
    assert status["max_search_file_bytes"] == brain.MAX_SEARCH_FILE_BYTES
    assert status["max_directory_entries"] == 500
    assert status["max_read_bytes"] == brain.MAX_READ_CHARS
    assert status["max_candidates"] == brain.MAX_CANDIDATES


def test_concurrent_approval_activates_candidate_only_once(tmp_path):
    import threading

    brain, registry = make_brain(tmp_path)
    candidate = brain.stage(DynamicToolSpec(
        "concurrent_activation_tool", "concurrency guard",
        (DynamicToolStep("file_info", {"path": "."}),),
    ))
    barrier = threading.Barrier(3)
    outcomes = []

    def approve():
        barrier.wait()
        try:
            outcomes.append(brain.approve(candidate.candidate_id, user_approved=True).status)
        except Exception as exc:
            outcomes.append(type(exc).__name__)

    workers = [threading.Thread(target=approve) for _ in range(2)]
    for worker in workers:
        worker.start()
    barrier.wait()
    for worker in workers:
        worker.join(timeout=3)
    assert sorted(outcomes) == ["ACTIVE", "ValueError"]
    assert registry.has("concurrent_activation_tool")
    assert brain.lifecycle_status()["candidate_counts"]["ACTIVE"] == 1
