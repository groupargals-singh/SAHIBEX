from core.brain.specialist_catalogue import (
    SPECIALIST_CATALOGUE, get_specialist, list_specialists, runtime_coverage,
)


def test_catalogue_has_unique_stable_ids_and_expected_roles():
    ids = [item.role_id for item in SPECIALIST_CATALOGUE]
    assert len(ids) == len(set(ids))
    assert len(ids) >= 54
    for role in (
        "learning", "teaching", "document_file", "coding", "app_builder", "vision",
        "orchestration", "evidence_fact_checking", "system_architecture",
        "performance_resource", "privacy_data_governance", "human_handoff", "backup_continuity", "decision_analysis", "debugging", "app_builder", "planning", "code_review", "data_analysis", "math", "language", "voice", "knowledge",
    ):
        assert get_specialist(role) is not None


def test_profiles_do_not_grant_tools_or_permissions():
    for profile in SPECIALIST_CATALOGUE:
        assert profile.tools == ()
        assert profile.executable_handler_required is True
        assert "no_cross_user_or_child_access" in profile.memory_scope
        assert "permission" not in profile.output_contract.lower() or profile.output_contract


def test_lookup_and_department_filter_are_deterministic():
    assert get_specialist(" CODING ") == get_specialist("coding")
    assert list_specialists(department="engineering")
    assert all(p.department == "engineering" for p in list_specialists(department="engineering"))


def test_runtime_coverage_reports_missing_handlers_without_claiming_execution():
    coverage = runtime_coverage(["coding", "research", "not-a-role"])
    assert coverage["handler_registered"] == ("coding", "research")
    assert "teaching" in coverage["handler_missing"]
    assert "not-a-role" not in coverage["handler_registered"]


def test_live_internal_team_coverage_is_exposed_without_claiming_unwired_roles():
    from core.brain.master_brain import MasterBrain

    brain = MasterBrain()
    coverage = brain.internal_brain_team.specialist_catalogue_coverage()
    assert coverage["catalogue_total"] == ("61",)
    assert coverage["implemented_count"] == ("61",)
    assert coverage["missing_count"] == ("0",)
    assert set(coverage["implemented"]) >= {
        "reading", "research", "learning", "memory", "verification",
        "security", "orchestration", "thinking", "teaching", "document_file", "system_architecture", "performance_resource", "privacy_data_governance", "human_handoff", "evidence_fact_checking", "backup_continuity", "coding", "testing", "knowledge_maintenance", "uncertainty", "debugging",
    }
    assert "teaching" not in coverage["missing_or_unwired"]
    assert "document_file" not in coverage["missing_or_unwired"]
    assert "system_architecture" not in coverage["missing_or_unwired"]
    assert "performance_resource" not in coverage["missing_or_unwired"]
    assert "privacy_data_governance" not in coverage["missing_or_unwired"]
    assert "human_handoff" not in coverage["missing_or_unwired"]
    assert "vision" not in coverage["missing_or_unwired"]


def test_evidence_fact_checking_is_not_reported_as_unwired():
    from core.brain.master_brain import MasterBrain
    coverage = MasterBrain().internal_brain_team.specialist_catalogue_coverage()
    assert "evidence_fact_checking" in coverage["implemented"]
    assert "evidence_fact_checking" not in coverage["missing_or_unwired"]


def test_live_handler_count_distinguishes_direct_ids_from_explicit_alias():
    """Registration count and catalogue-aligned count must not be conflated."""
    from core.brain.master_brain import MasterBrain
    from core.brain.specialist_catalogue import INTERNAL_ROLE_ALIASES

    team = MasterBrain().internal_brain_team
    registered = {role.role_id for role in team.roles() if role.handler_registered}
    direct = registered.intersection({profile.role_id for profile in SPECIALIST_CATALOGUE})
    aliased = {
        role_id: catalogue_id
        for role_id, catalogue_id in INTERNAL_ROLE_ALIASES.items()
        if role_id in registered and catalogue_id in {p.role_id for p in SPECIALIST_CATALOGUE}
    }

    assert len(registered) == 61
    assert len(direct) == 60
    assert aliased == {"reasoning": "thinking"}
    coverage = team.specialist_catalogue_coverage()
    assert coverage["implemented_count"] == ("61",)
    assert coverage["missing_count"] == ("0",)
