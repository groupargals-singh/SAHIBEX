#!/usr/bin/env python3
"""Read-only provenance/lifecycle audit for the SAHIBEX knowledge database.

This utility never opens the database in write mode and never changes candidate
flags, lifecycle records, evidence, or source rows. It prints aggregate counts
only; knowledge statements and credentials are never emitted.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
import sqlite3


def audit_database(database: Path) -> dict:
    database = database.expanduser().resolve()
    if not database.is_file():
        raise FileNotFoundError(database)
    uri = f"file:{database.as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only=ON")
        evidence = {
            row["evidence_id"]: (row["source_id"], row["finding_id"])
            for row in connection.execute(
                "SELECT evidence_id, source_id, finding_id FROM research_evidence"
            )
        }
        finding_ids = {
            row[0] for row in connection.execute("SELECT finding_id FROM research_findings")
        }
        source_ids = {
            row[0] for row in connection.execute("SELECT source_id FROM research_sources")
        }
        lifecycle = defaultdict(list)
        event_status_counts = Counter()
        for row in connection.execute(
            "SELECT knowledge_id, status, verified_at "
            "FROM knowledge_verification_records ORDER BY verified_at ASC"
        ):
            lifecycle[row["knowledge_id"]].append(row["status"])
            event_status_counts[row["status"]] += 1

        counts = Counter()
        independent_counts = Counter()
        supporting_counts = Counter()
        metadata_status_counts = Counter()
        for row in connection.execute(
            "SELECT knowledge_id, verified, data FROM knowledge_candidates"
        ):
            counts["candidate_count"] += 1
            counts["legacy_verified_flag_true"] += int(row["verified"] == 1)
            history = lifecycle.get(row["knowledge_id"], [])
            counts["candidates_with_lifecycle_event"] += int(bool(history))
            counts["candidates_without_lifecycle_event"] += int(not history)
            latest_status = history[-1] if history else "NO_EVENT"
            counts[f"latest_status:{latest_status}"] += 1
            counts["legacy_verified_without_latest_verified_event"] += int(
                row["verified"] == 1 and latest_status != "VERIFIED"
            )
            counts["legacy_verified_with_latest_verified_event"] += int(
                row["verified"] == 1 and latest_status == "VERIFIED"
            )

            try:
                data = json.loads(row["data"])
            except (TypeError, json.JSONDecodeError):
                counts["candidate_invalid_json"] += 1
                continue
            if not isinstance(data, dict):
                counts["candidate_non_object_json"] += 1
                continue

            evidence_refs = data.get("evidence", [])
            finding_refs = data.get("findings", [])
            if isinstance(evidence_refs, list):
                counts["evidence_reference_count"] += len(evidence_refs)
                counts["candidates_with_exactly_one_evidence_reference"] += int(
                    len(evidence_refs) == 1
                )
                linked_sources = set()
                linked_findings = set()
                for reference in evidence_refs:
                    reference = str(reference)
                    if reference not in evidence:
                        counts["evidence_reference_missing"] += 1
                        continue
                    counts["evidence_reference_valid"] += 1
                    source_id, finding_id = evidence[reference]
                    if source_id in source_ids:
                        counts["evidence_source_reference_valid"] += 1
                        linked_sources.add(source_id)
                    else:
                        counts["evidence_source_reference_missing"] += 1
                    if finding_id:
                        linked_findings.add(finding_id)
                counts["candidates_with_one_distinct_source"] += int(
                    len(linked_sources) == 1
                )
                counts["candidates_with_multiple_distinct_sources"] += int(
                    len(linked_sources) > 1
                )
            else:
                counts["candidate_evidence_field_not_list"] += 1
                linked_findings = set()

            if isinstance(finding_refs, list):
                counts["finding_reference_count"] += len(finding_refs)
                counts["candidates_with_exactly_one_finding_reference"] += int(
                    len(finding_refs) == 1
                )
                for reference in finding_refs:
                    reference = str(reference)
                    if reference in finding_ids:
                        counts["finding_reference_valid"] += 1
                    else:
                        counts["finding_reference_missing"] += 1
                counts["candidate_evidence_finding_link_matches"] += int(
                    bool(linked_findings.intersection(str(x) for x in finding_refs))
                )
            else:
                counts["candidate_findings_field_not_list"] += 1

            metadata = data.get("metadata", {})
            if isinstance(metadata, dict):
                for key in (
                    "verification_status",
                    "verification_reason",
                    "supporting_source_count",
                    "independent_source_count",
                    "contradicting_source_count",
                    "agreement_score",
                    "agreement_version",
                ):
                    counts[f"metadata_field:{key}"] += int(key in metadata)
                if "independent_source_count" in metadata:
                    independent_counts[str(metadata["independent_source_count"])] += 1
                if "supporting_source_count" in metadata:
                    supporting_counts[str(metadata["supporting_source_count"])] += 1
                if "verification_status" in metadata:
                    metadata_status_counts[str(metadata["verification_status"])] += 1

        table_counts = {}
        for table, column in (
            ("knowledge_candidates", "knowledge_id"),
            ("knowledge_verification_records", "event_id"),
            ("knowledge_conflict_records", "conflict_id"),
            ("knowledge_merge_records", "merge_id"),
            ("research_sources", "source_id"),
            ("research_documents", "document_id"),
            ("research_findings", "finding_id"),
            ("research_evidence", "evidence_id"),
        ):
            table_counts[table] = connection.execute(
                f"SELECT COUNT({column}) FROM {table}"
            ).fetchone()[0]

        return {
            "database": str(database),
            "database_bytes": database.stat().st_size,
            "read_only": True,
            "database_write_attempted": False,
            "table_counts": table_counts,
            "candidate_counts": dict(sorted(counts.items())),
            "lifecycle_event_status_counts": dict(sorted(event_status_counts.items())),
            "metadata_independent_source_count_distribution": dict(sorted(independent_counts.items())),
            "metadata_supporting_source_count_distribution": dict(sorted(supporting_counts.items())),
            "metadata_verification_status_distribution": dict(sorted(metadata_status_counts.items())),
            "disposition": (
                "REVIEW_REQUIRED: stale candidate flags are not lifecycle verification; "
                "do not bulk-promote or mutate records without a backed-up, evidence-based migration."
            ),
        }
    finally:
        connection.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "sahibex_brain.db",
        help="SQLite database path (opened strictly read-only).",
    )
    args = parser.parse_args()
    print(json.dumps(audit_database(args.db), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
