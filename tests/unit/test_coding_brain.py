from core.brain.coding_brain import CodingBrain
from core.brain.master_brain import MasterBrain


def test_coding_brain_parses_source_and_reports_imports():
    result = CodingBrain().review_python("import json\n\ndef answer():\n    return json.dumps({'ok': True})\n")
    assert result.success is True
    assert result.status == "STATIC_CHECK_PASSED"
    assert "json" in result.imports
    assert result.functions == 1
    assert result.executes_code is False
    assert result.installs_packages is False


def test_coding_brain_flags_syntax_error():
    result = CodingBrain().review_python("def broken(:\n    pass")
    assert result.success is False
    assert result.status == "SYNTAX_ERROR"
    assert result.findings[0].code == "SYNTAX_ERROR"


def test_coding_brain_flags_risky_calls_without_executing_them():
    result = CodingBrain().review_python("import os\n\ndef run(value):\n    return eval(value)\n")
    assert result.success is True
    assert result.status == "REVIEW_REQUIRED"
    assert any(item.code == "REVIEW_REQUIRED" for item in result.findings)
    assert result.executes_code is False


def test_coding_brain_bounds_source_size():
    result = CodingBrain().review_python("x = 1\n" * 100_000)
    assert result.success is False
    assert result.status == "SOURCE_TOO_LARGE"


def test_master_coding_role_routes_supplied_code_to_static_review():
    brain = MasterBrain()
    result = brain.dispatch_internal_brain(
        "coding", "review this Python code",
        {"source_code": "def add(a, b):\n    return a + b\n", "language": "python"},
        authorization_passed=True, verification_passed=True,
    )
    assert result.accepted is True
    assert result.result["status"] == "STATIC_CHECK_PASSED"
    assert result.result["functions"] == 1
    assert result.result["executes_code"] is False
    assert result.result["writes_files"] is False
