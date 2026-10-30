"""Bounded SAHIBEX Text/Development Brain.

Creates immutable candidate artifacts in an isolated development queue. It never
executes candidate code, installs packages, downloads models, accesses secrets,
changes production files, or promotes a candidate into the live runtime.
Mother Brain verification and an explicit authorized promotion workflow are
required before any candidate can affect production.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any
from uuid import uuid4


class TextDevelopmentBrain:
    MAX_TITLE = 160
    MAX_RATIONALE = 2_000
    MAX_CONTENT = 200_000
    ALLOWED_TYPES = {"text", "python", "model_plan", "test_plan", "documentation"}

    def __init__(self, queue_dir: str | Path | None = None) -> None:
        self.queue_dir = Path(queue_dir) if queue_dir else Path(__file__).resolve().parents[2] / "data" / "development_lab" / "candidates"

    def propose(self, request: str, context: dict[str, Any]) -> dict[str, Any]:
        """Store a bounded proposal for review; do not execute or promote it."""
        if not isinstance(request, str) or not request.strip() or len(request) > 2_000:
            return self._fail("REQUEST_INVALID")
        if not isinstance(context, dict):
            return self._fail("CONTEXT_INVALID")
        artifact_type = context.get("artifact_type", "text")
        title = context.get("title", request.strip()[:self.MAX_TITLE])
        content = context.get("content")
        rationale = context.get("rationale", "")
        if not isinstance(artifact_type, str) or artifact_type not in self.ALLOWED_TYPES:
            return self._fail("ARTIFACT_TYPE_NOT_ALLOWED")
        if not isinstance(title, str) or not title.strip() or len(title) > self.MAX_TITLE:
            return self._fail("TITLE_INVALID")
        if not isinstance(content, str) or not content.strip() or len(content) > self.MAX_CONTENT:
            return self._fail("CONTENT_INVALID_OR_TOO_LARGE")
        if not isinstance(rationale, str) or len(rationale) > self.MAX_RATIONALE:
            return self._fail("RATIONALE_INVALID")
        candidate_id = "td-" + uuid4().hex
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        record = {
            "schema_version": 1,
            "candidate_id": candidate_id,
            "created_at_unix": int(time.time()),
            "title": title.strip(),
            "artifact_type": artifact_type,
            "rationale": rationale.strip(),
            "content": content,
            "content_sha256": digest,
            "status": "PROPOSED_PENDING_MOTHER_REVIEW",
            "review": {"mother_reviewed": False, "security_passed": False, "tests_passed": False, "regression_passed": False},
            "promotion": {"production_changed": False, "executed": False, "network_used": False},
        }
        temporary_path = None
        try:
            self.queue_dir.mkdir(parents=True, exist_ok=True)
            path = self.queue_dir / f"{candidate_id}.json"
            # Write to a temporary file then atomically publish a complete record.
            fd, temporary_name = tempfile.mkstemp(prefix=f".{candidate_id}.", suffix=".tmp", dir=self.queue_dir)
            temporary_path = Path(temporary_name)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(record, handle, ensure_ascii=False, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, path)
            temporary_path = None
        except (OSError, ValueError) as exc:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            return self._fail("CANDIDATE_STORAGE_FAILED", error_type=type(exc).__name__)
        return {
            "success": True,
            "status": record["status"],
            "candidate_id": candidate_id,
            "content_sha256": digest,
            "artifact_type": artifact_type,
            "candidate_path": str(path),
            "mother_review_required": True,
            "human_approval_required_for_production_promotion": True,
            "executes_code": False,
            "installs_packages": False,
            "downloads_models": False,
            "uses_network": False,
            "changes_production": False,
            "changes_constitution": False,
            "grants_permissions": False,
        }

    @staticmethod
    def _fail(status: str, **extra: str) -> dict[str, Any]:
        return {"success": False, "status": status, "candidate_created": False,
                "executes_code": False, "changes_production": False, **extra}

    @staticmethod
    def capability_contract() -> dict[str, bool]:
        return {
            "creates_development_candidates": True,
            "mother_review_required": True,
            "human_approval_required_for_production_promotion": True,
            "executes_candidate_code": False,
            "downloads_or_trains_models_automatically": False,
            "writes_production_files": False,
            "reads_credentials": False,
            "unrestricted_network_access": False,
            "modifies_constitution": False,
            "self_authorizes_promotion": False,
        }
