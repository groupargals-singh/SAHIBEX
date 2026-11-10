from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scripts.audit_knowledge_provenance import audit_database


def test_knowledge_provenance_audit_is_read_only_and_flags_stale_legacy_verified(tmp_path: Path) -> None:
    database = tmp_path / "knowledge.db"
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        CREATE TABLE knowledge_candidates (
            knowledge_id TEXT PRIMARY KEY, verified INTEGER, confidence REAL, data TEXT
        );
        CREATE TABLE knowledge_verification_records (
            event_id TEXT PRIMARY KEY, knowledge_id TEXT, status TEXT,
            reason TEXT, verified_at TEXT, metadata TEXT
        );
        CREATE TABLE knowledge_conflict_records (
            conflict_id TEXT PRIMARY KEY, first_knowledge_id TEXT, second_knowledge_id TEXT,
            conflict_type TEXT, resolution_status TEXT, selected_knowledge_id TEXT,
            created_at TEXT, data TEXT
        );
        CREATE TABLE knowledge_merge_records (
            merge_id TEXT PRIMARY KEY, primary_knowledge_id TEXT, duplicate_knowledge_id TEXT,
            similarity_score REAL, status TEXT, merged_at TEXT, metadata TEXT
        );
        CREATE TABLE research_sources (source_id TEXT PRIMARY KEY, data TEXT);
        CREATE TABLE research_documents (document_id TEXT PRIMARY KEY, source_id TEXT, content_hash TEXT, data TEXT);
        CREATE TABLE research_findings (finding_id TEXT PRIMARY KEY, document_id TEXT, data TEXT);
        CREATE TABLE research_evidence (evidence_id TEXT PRIMARY KEY, finding_id TEXT, source_id TEXT, data TEXT);
        """
    )
    connection.execute("INSERT INTO research_sources VALUES ('s1', '{}')")
    connection.execute("INSERT INTO research_documents VALUES ('d1', 's1', 'h', '{}')")
    connection.execute("INSERT INTO research_findings VALUES ('f1', 'd1', '{}')")
    connection.execute("INSERT INTO research_evidence VALUES ('e1', 'f1', 's1', '{}')")
    connection.execute(
        "INSERT INTO knowledge_candidates VALUES (?, ?, ?, ?)",
        ("k1", 1, 0.9, json.dumps({
            "evidence": ["e1"], "findings": ["f1"],
            "metadata": {"independent_source_count": 1, "supporting_source_count": 1},
        })),
    )
    connection.execute(
        "INSERT INTO knowledge_verification_records VALUES (?, ?, ?, ?, ?, ?)",
        ("v1", "k1", "UNVERIFIED", "needs corroboration", "2026-01-01T00:00:00Z", "{}"),
    )
    connection.commit()
    connection.close()

    result = audit_database(database)
    assert result["read_only"] is True
    assert result["candidate_counts"]["candidate_count"] == 1
    assert result["candidate_counts"]["legacy_verified_flag_true"] == 1
    assert result["candidate_counts"]["latest_status:UNVERIFIED"] == 1
    assert result["candidate_counts"]["legacy_verified_without_latest_verified_event"] == 1
    assert result["candidate_counts"]["evidence_reference_valid"] == 1
    assert result["candidate_counts"]["finding_reference_valid"] == 1
    assert result["candidate_counts"]["evidence_source_reference_valid"] == 1

    check = sqlite3.connect(f"file:{database.resolve().as_posix()}?mode=ro", uri=True)
    try:
        assert check.execute("SELECT verified FROM knowledge_candidates WHERE knowledge_id='k1'").fetchone()[0] == 1
        assert check.execute("SELECT COUNT(*) FROM knowledge_verification_records").fetchone()[0] == 1
    finally:
        check.close()
