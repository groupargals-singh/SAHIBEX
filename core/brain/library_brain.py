"""Privacy-conscious local knowledge library catalogue for SAHIBEX.

Only indexes metadata and hashes from explicitly allowed local directories.
It does not execute, upload, or automatically trust indexed content.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class LibraryBrain:
    ALLOWED_ROOTS = ("knowledge", "docs", "data/knowledge")
    ALLOWED_SUFFIXES = {".pdf", ".txt", ".md", ".json", ".csv", ".html", ".htm"}
    MAX_FILE_BYTES = 50 * 1024 * 1024

    def __init__(self, project_root: str | Path | None = None, index_path: str | Path | None = None) -> None:
        self.project_root = Path(project_root or Path(__file__).resolve().parents[2]).resolve()
        self.index_path = Path(index_path) if index_path else self.project_root / "data" / "library_brain" / "catalog.json"

    def index_local_file(self, relative_path: str, *, title: str = "", category: str = "general", source: str = "local_user_library", license_status: str = "UNKNOWN") -> dict[str, Any]:
        if not isinstance(relative_path, str) or not relative_path.strip():
            return self._fail("PATH_REQUIRED")
        candidate = (self.project_root / relative_path).resolve()
        allowed = [ (self.project_root / root).resolve() for root in self.ALLOWED_ROOTS ]
        if not any(candidate == root or root in candidate.parents for root in allowed):
            return self._fail("PATH_OUTSIDE_LIBRARY_ROOTS")
        if candidate.is_symlink() or not candidate.is_file():
            return self._fail("LOCAL_FILE_NOT_FOUND_OR_SYMLINK")
        if candidate.suffix.lower() not in self.ALLOWED_SUFFIXES:
            return self._fail("FILE_TYPE_NOT_ALLOWED")
        size = candidate.stat().st_size
        if size <= 0 or size > self.MAX_FILE_BYTES:
            return self._fail("FILE_SIZE_OUT_OF_RANGE")
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        record = {"path": candidate.relative_to(self.project_root).as_posix(), "title": str(title or candidate.stem)[:200],
                  "category": str(category)[:80], "source": str(source)[:200],
                  "license_status": str(license_status)[:80], "size_bytes": size,
                  "sha256": digest, "verification_status": "UNVERIFIED", "trusted_for_training": False}
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"schema_version": 1, "records": []}
        if self.index_path.exists():
            try:
                loaded = json.loads(self.index_path.read_text(encoding="utf-8"))
                if not isinstance(loaded, dict) or loaded.get("schema_version") != 1 or not isinstance(loaded.get("records"), list):
                    return self._fail("LIBRARY_INDEX_CORRUPT")
                payload = loaded
            except (OSError, json.JSONDecodeError):
                return self._fail("LIBRARY_INDEX_CORRUPT")
        records = [item for item in payload["records"] if isinstance(item, dict) and item.get("path") != record["path"]]
        records.append(record)
        payload["records"] = records
        temporary = self.index_path.with_suffix(self.index_path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.index_path)
        return {"success": True, "status": "INDEXED_UNVERIFIED", "record": record, "trusted_for_training": False, "network_used": False}

    def list_entries(self, *, category: str | None = None) -> dict[str, Any]:
        if not self.index_path.exists():
            return {"success": True, "status": "LIBRARY_EMPTY", "entries": []}
        try:
            payload = json.loads(self.index_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or payload.get("schema_version") != 1 or not isinstance(payload.get("records"), list):
                return self._fail("LIBRARY_INDEX_CORRUPT")
            entries = [item for item in payload["records"] if isinstance(item, dict) and (category is None or item.get("category") == category)]
            return {"success": True, "status": "LIBRARY_LISTED", "entries": entries}
        except (OSError, json.JSONDecodeError):
            return self._fail("LIBRARY_INDEX_CORRUPT")

    @staticmethod
    def _fail(status: str) -> dict[str, Any]:
        return {"success": False, "status": status, "network_used": False, "trusted_for_training": False}

    @staticmethod
    def capability_contract() -> dict[str, bool]:
        return {"local_library_catalogue": True, "source_and_hash_tracking": True,
                "automatic_training_trust": False, "network_upload": False,
                "code_execution": False, "mother_verification_required": True}
