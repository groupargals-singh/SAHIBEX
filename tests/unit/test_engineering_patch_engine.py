from pathlib import Path
import subprocess

import pytest

from core.agent.engineering_patch_engine import EngineeringPatchEngine, PatchPolicyError


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


@pytest.fixture
def engine(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".git").mkdir()
    (root / "app").mkdir()
    (root / "core").mkdir()
    (root / "core" / "sample.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "SAHIBEX Test")
    _git(root, "add", "core/sample.py")
    _git(root, "commit", "-qm", "baseline")
    return EngineeringPatchEngine(root, tmp_path / "backups"), root


def _patch(old="VALUE = 1", new="VALUE = 2", path="core/sample.py"):
    return (
        f"diff --git a/{path} b/{path}\n"
        "index 4b9c2f1..7e2d1a0 100644\n"
        f"--- a/{path}\n+++ b/{path}\n"
        "@@ -1 +1 @@\n"
        f"-{old}\n+{new}\n"
    )


def test_dry_run_checks_patch_without_writing(engine):
    tool, root = engine
    result = tool.apply(_patch(), dry_run=True)
    assert result.success and result.dry_run and not result.applied
    assert (root / "core/sample.py").read_text() == "VALUE = 1\n"


def test_apply_creates_verified_backup_and_rollback_restores(engine):
    tool, root = engine
    result = tool.apply(_patch(), dry_run=False)
    assert result.success and result.applied and result.backup_id
    assert (root / "core/sample.py").read_text() == "VALUE = 2\n"
    rollback = tool.rollback(result.backup_id)
    assert rollback["success"] is True
    assert (root / "core/sample.py").read_text() == "VALUE = 1\n"


def test_rollback_refuses_to_overwrite_changes_made_after_patch(engine):
    tool, root = engine
    result = tool.apply(_patch(), dry_run=False)
    (root / "core/sample.py").write_text("VALUE = 3\n")
    with pytest.raises(PatchPolicyError):
        tool.rollback(result.backup_id)


def test_rejects_path_traversal(engine):
    tool, _ = engine
    with pytest.raises(PatchPolicyError):
        tool.apply(_patch(path="../outside.py"))


def test_rejects_file_deletion_and_binary_patch(engine):
    tool, _ = engine
    with pytest.raises(PatchPolicyError):
        tool.apply(_patch().replace("@@ -1 +1 @@", "deleted file mode 100644\n@@ -1 +0 @@"))
    with pytest.raises(PatchPolicyError):
        tool.apply("GIT binary patch\n")


def test_rejects_dirty_target(engine):
    tool, root = engine
    (root / "core/sample.py").write_text("USER CHANGE\n")
    with pytest.raises(PatchPolicyError):
        tool.apply(_patch())


def test_rejects_symlink_target(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".git").mkdir()
    (root / "app").mkdir()
    (root / "core").mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("VALUE = 1\n")
    (root / "core" / "sample.py").symlink_to(outside)
    _git(root, "init", "-q")
    tool = EngineeringPatchEngine(root, tmp_path / "backups")
    with pytest.raises(PatchPolicyError):
        tool.apply(_patch())
