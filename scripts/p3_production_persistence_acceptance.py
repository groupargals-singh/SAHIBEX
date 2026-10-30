#!/usr/bin/env python3
"""P3 persistence acceptance: read-only production snapshot, restore comparison,
and abrupt-process SQLite recovery on a disposable database.

Never writes to the configured production DB. The production snapshot is made
through SQLite's online backup API; restore and crash tests use temp files.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "data" / "sahibex_brain.db").resolve()
OUT = ROOT / "logs" / "p3_production_persistence_acceptance_20261021.json"


def canonical(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"__bytes_hex__": value.hex()}
    return value


def table_names(conn: sqlite3.Connection) -> list[str]:
    return [
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]


def snapshot_hash(conn: sqlite3.Connection, table: str) -> tuple[int, str]:
    # rowid makes ordering deterministic for the ordinary and FTS tables here.
    digest = hashlib.sha256()
    count = 0
    try:
        cursor = conn.execute(f'SELECT * FROM "{table}" ORDER BY rowid')
    except sqlite3.OperationalError:
        cursor = conn.execute(f'SELECT * FROM "{table}"')
    for row in cursor:
        payload = json.dumps(
            [canonical(v) for v in row],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
        count += 1
    return count, digest.hexdigest()


def inspect_db(path: Path) -> dict[str, Any]:
    conn = sqlite3.connect(str(path), timeout=30)
    try:
        conn.execute("PRAGMA query_only=ON")
        quick = conn.execute("PRAGMA quick_check").fetchone()[0]
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        tables = table_names(conn)
        per_table = {name: snapshot_hash(conn, name) for name in tables}
        return {
            "quick_check": quick,
            "integrity_check": integrity,
            "tables": tables,
            "table_count": len(tables),
            "row_counts": {k: v[0] for k, v in per_table.items()},
            "table_sha256": {k: v[1] for k, v in per_table.items()},
        }
    finally:
        conn.close()


def crash_recovery_test(directory: Path) -> dict[str, Any]:
    db = directory / "crash_recovery_disposable.db"
    setup = sqlite3.connect(db)
    setup.execute("PRAGMA journal_mode=WAL")
    setup.execute("PRAGMA synchronous=FULL")
    setup.execute("CREATE TABLE durable_events (event_id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
    setup.execute("INSERT INTO durable_events(value) VALUES ('baseline')")
    setup.commit()
    setup.close()

    # Commit a durable record then exit without graceful connection close.
    committed = """
import os, sqlite3, sys
c=sqlite3.connect(sys.argv[1], timeout=10)
c.execute('PRAGMA journal_mode=WAL')
c.execute('PRAGMA synchronous=FULL')
c.execute('INSERT INTO durable_events(value) VALUES (?)', ('committed-before-abrupt-exit',))
c.commit()
os._exit(23)
"""
    p = subprocess.run([sys.executable, "-c", committed, str(db)], check=False)
    if p.returncode != 23:
        raise AssertionError(f"abrupt-exit writer returned {p.returncode}, expected 23")

    reopened = sqlite3.connect(db, timeout=10)
    try:
        quick = reopened.execute("PRAGMA quick_check").fetchone()[0]
        values = [r[0] for r in reopened.execute("SELECT value FROM durable_events ORDER BY event_id")]
        if quick != "ok":
            raise AssertionError(f"post-crash quick_check={quick}")
        if values != ["baseline", "committed-before-abrupt-exit"]:
            raise AssertionError(f"committed data did not survive abrupt exit: {values}")
        # Simulate an interrupted, uncommitted write; after abrupt process exit,
        # SQLite must roll it back and retain committed rows only.
        uncommitted = """
import os, sqlite3, sys
c=sqlite3.connect(sys.argv[1], timeout=10)
c.execute('PRAGMA journal_mode=WAL')
c.execute('PRAGMA synchronous=FULL')
c.execute('BEGIN IMMEDIATE')
c.execute('INSERT INTO durable_events(value) VALUES (?)', ('must-rollback-uncommitted',))
os._exit(24)
"""
        p2 = subprocess.run([sys.executable, "-c", uncommitted, str(db)], check=False)
        if p2.returncode != 24:
            raise AssertionError(f"uncommitted writer returned {p2.returncode}, expected 24")
    finally:
        reopened.close()

    reopened2 = sqlite3.connect(db, timeout=10)
    try:
        quick2 = reopened2.execute("PRAGMA quick_check").fetchone()[0]
        values2 = [r[0] for r in reopened2.execute("SELECT value FROM durable_events ORDER BY event_id")]
        if quick2 != "ok":
            raise AssertionError(f"post-rollback quick_check={quick2}")
        if values2 != ["baseline", "committed-before-abrupt-exit"]:
            raise AssertionError(f"uncommitted write not rolled back: {values2}")
    finally:
        reopened2.close()
    return {
        "status": "PASS",
        "committed_write_survived_abrupt_process_exit": True,
        "uncommitted_write_rolled_back_after_abrupt_exit": True,
        "quick_check_after_both_reopens": "ok",
        "disposable_only": True,
    }


def main() -> int:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"production DB not found: {SOURCE}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "date": time.strftime("%Y-%m-%d"),
        "source": str(SOURCE),
        "production_source_open_mode": "read-only",
        "production_source_modified": False,
        "tests": {},
    }

    # Use an isolated temp directory so a failed run does not leave a partial
    # backup that could be mistaken for a valid recovery artifact.
    with tempfile.TemporaryDirectory(prefix="sahibex-p3-acceptance-") as tmp:
        temp = Path(tmp)
        backup = temp / "production_snapshot.db"
        restored = temp / "restored_snapshot.db"
        uri = f"file:{SOURCE.as_posix()}?mode=ro"
        src = sqlite3.connect(uri, uri=True, timeout=30)
        try:
            src.execute("PRAGMA query_only=ON")
            # Establish read visibility before creating the online snapshot.
            src.execute("SELECT count(*) FROM sqlite_master").fetchone()
            backup_conn = sqlite3.connect(str(backup), timeout=30)
            try:
                src.backup(backup_conn)
            finally:
                backup_conn.close()
        finally:
            src.close()

        backup_report = inspect_db(backup)
        dst = sqlite3.connect(str(restored), timeout=30)
        src_restore = sqlite3.connect(str(backup), timeout=30)
        try:
            src_restore.backup(dst)
        finally:
            dst.close()
            src_restore.close()
        restore_report = inspect_db(restored)

        if backup_report["quick_check"] != "ok" or backup_report["integrity_check"] != "ok":
            raise AssertionError("online backup failed SQLite integrity checks")
        if restore_report["quick_check"] != "ok" or restore_report["integrity_check"] != "ok":
            raise AssertionError("restored snapshot failed SQLite integrity checks")
        if backup_report["row_counts"] != restore_report["row_counts"]:
            raise AssertionError("restore row counts differ from online snapshot")
        if backup_report["table_sha256"] != restore_report["table_sha256"]:
            differing = [
                t for t in backup_report["table_sha256"]
                if backup_report["table_sha256"][t] != restore_report["table_sha256"].get(t)
            ]
            raise AssertionError(f"restore content hashes differ: {differing}")

        report["tests"]["production_online_backup"] = {
            "status": "PASS",
            "method": "SQLite online backup API from read-only source connection",
            "source_table_count": backup_report["table_count"],
            "quick_check": backup_report["quick_check"],
            "integrity_check": backup_report["integrity_check"],
            "row_counts": backup_report["row_counts"],
        }
        report["tests"]["restore_integrity"] = {
            "status": "PASS",
            "quick_check": restore_report["quick_check"],
            "integrity_check": restore_report["integrity_check"],
            "all_table_row_counts_equal": True,
            "all_table_content_hashes_equal": True,
            "table_count": restore_report["table_count"],
        }
        report["tests"]["abrupt_process_recovery"] = crash_recovery_test(temp)

    report["overall_status"] = "PASS"
    report["scope_note"] = (
        "Verified a read-only online snapshot and a disposable restore with per-table "
        "row-count/content hashes, plus abrupt-process SQLite WAL recovery on a tiny "
        "disposable DB. This is not a physical Android power-loss test and does not "
        "replace a separately scheduled production maintenance-window restore drill."
    )
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "overall_status": report["overall_status"],
        "report": str(OUT),
        "production_source_modified": False,
        "tests": {k: v["status"] for k, v in report["tests"].items()},
        "table_count": report["tests"]["production_online_backup"]["source_table_count"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        failure = {
            "overall_status": "FAIL",
            "source": str(SOURCE),
            "production_source_modified": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
        OUT.write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(failure, indent=2), file=sys.stderr)
        raise
