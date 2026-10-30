import hashlib

from core.brain.test_brain import TestBrain
from core.brain.library_brain import LibraryBrain


def test_test_brain_validates_python_without_execution():
    source = "def add(a, b):\n    return a + b\n"
    result = TestBrain().validate_candidate({
        "artifact_type": "python", "content": source,
        "content_sha256": hashlib.sha256(source.encode()).hexdigest(),
    })
    assert result["success"] is True
    assert result["status"] == "STATIC_CHECKS_PASSED_PENDING_MOTHER_REVIEW"
    assert result["executes_code"] is False
    assert result["promotion_allowed"] is False


def test_test_brain_rejects_invalid_python_and_tampering():
    invalid = TestBrain().validate_candidate({"artifact_type": "python", "content": "def broken(:"})
    assert invalid["status"] == "PYTHON_SYNTAX_INVALID"
    tampered = TestBrain().validate_candidate({"artifact_type": "text", "content": "safe", "content_sha256": "0" * 64})
    assert tampered["status"] == "CONTENT_INTEGRITY_MISMATCH"


def test_library_brain_indexes_only_allowed_local_files(tmp_path):
    root = tmp_path
    (root / "knowledge").mkdir()
    doc = root / "knowledge" / "guide.md"
    doc.write_text("SAHIBEX local reference", encoding="utf-8")
    brain = LibraryBrain(project_root=root)
    result = brain.index_local_file("knowledge/guide.md", category="engineering", license_status="USER_OWNED")
    assert result["success"] is True
    assert result["record"]["verification_status"] == "UNVERIFIED"
    assert result["trusted_for_training"] is False
    listed = brain.list_entries(category="engineering")
    assert len(listed["entries"]) == 1
    assert listed["entries"][0]["sha256"] == hashlib.sha256(doc.read_bytes()).hexdigest()


def test_library_brain_blocks_traversal_and_executable_files(tmp_path):
    (tmp_path / "knowledge").mkdir()
    (tmp_path / "outside.txt").write_text("private", encoding="utf-8")
    (tmp_path / "knowledge" / "bad.py").write_text("print('no')", encoding="utf-8")
    brain = LibraryBrain(project_root=tmp_path)
    assert brain.index_local_file("../outside.txt")["status"] == "PATH_OUTSIDE_LIBRARY_ROOTS"
    assert brain.index_local_file("knowledge/bad.py")["status"] == "FILE_TYPE_NOT_ALLOWED"


def test_master_brain_registers_development_testing_and_library_handlers():
    from core.brain.master_brain import MasterBrain
    brain = MasterBrain()
    roles = {role.role_id: role for role in brain.internal_brain_team.roles()}
    assert len(roles) == 61
    assert roles["testing"].handler_registered is True
    assert roles["knowledge"].handler_registered is True
    blocked = brain.dispatch_internal_brain("testing", "validate", {"candidate": {"artifact_type": "text", "content": "hello"}})
    assert blocked.accepted is False
    accepted = brain.dispatch_internal_brain("testing", "validate", {"candidate": {"artifact_type": "text", "content": "hello"}}, authorization_passed=True, verification_passed=True)
    assert accepted.accepted is True
    assert accepted.result["promotion_allowed"] is False
