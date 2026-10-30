"""Isolated candidate validation for SAHIBEX development artifacts.

This brain performs bounded, non-executing checks only. It never runs candidate
code, downloads dependencies, accesses the network, or promotes production.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any


class TestBrain:
    MAX_BYTES = 200_000

    def validate_candidate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(candidate, dict):
            return self._result(False, "CANDIDATE_INVALID")
        content = candidate.get("content")
        artifact_type = candidate.get("artifact_type", "text")
        expected_hash = candidate.get("content_sha256")
        if not isinstance(content, str) or not content.strip():
            return self._result(False, "CONTENT_REQUIRED")
        encoded = content.encode("utf-8")
        if len(encoded) > self.MAX_BYTES:
            return self._result(False, "CONTENT_TOO_LARGE")
        digest = hashlib.sha256(encoded).hexdigest()
        if expected_hash is not None and expected_hash != digest:
            return self._result(False, "CONTENT_INTEGRITY_MISMATCH", sha256=digest)
        checks = [{"name": "content_integrity", "passed": True}]
        if artifact_type == "python":
            try:
                ast.parse(content)
            except (SyntaxError, ValueError, TypeError) as exc:
                return self._result(False, "PYTHON_SYNTAX_INVALID", sha256=digest, error_type=type(exc).__name__, checks=checks + [{"name": "python_syntax", "passed": False}])
            checks.append({"name": "python_syntax", "passed": True})
        elif artifact_type in {"text", "documentation", "test_plan", "model_plan"}:
            checks.append({"name": "artifact_type_supported", "passed": True})
        else:
            return self._result(False, "ARTIFACT_TYPE_UNSUPPORTED", sha256=digest, checks=checks)
        return self._result(True, "STATIC_CHECKS_PASSED_PENDING_MOTHER_REVIEW", sha256=digest, checks=checks)

    @staticmethod
    def _result(success: bool, status: str, **extra: Any) -> dict[str, Any]:
        return {"success": success, "status": status, "promotion_allowed": False,
                "executes_code": False, "executes_tests": False,
                "network_used": False, "production_changed": False, **extra}

    @staticmethod
    def capability_contract() -> dict[str, bool]:
        return {"static_candidate_validation": True, "executes_candidate_code": False,
                "runs_untrusted_tests": False, "network_access": False,
                "production_promotion": False, "mother_review_required": True}
