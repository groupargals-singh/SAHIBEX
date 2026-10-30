#!/usr/bin/env python3
"""P3 durable staging restore drill from verified backup; production remains read-only."""
from __future__ import annotations
import hashlib, json, os, sqlite3, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BACKUP = ROOT / "data/backups/sahibex_brain_pre_reboot_20261021.db"
STAGE = ROOT / "data/staging/p3_restore_20261022"
DB = STAGE / "sahibex_brain.db"
REPORT = ROOT / "logs/p3_staging_restore_drill_20261022.json"
EXPECTED_BACKUP_SHA = "69a2fe74d58ae2db1735e6dd7497cea89d17e9fc67cf35a8e47d3c5955f84db6"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main() -> int:
    result = {"status":"RUNNING", "scope":"isolated staging restore from verified pre-restart backup", "production_db_modified":False, "production_service_restarted":False, "checks":{}}
    if not BACKUP.is_file():
        raise FileNotFoundError(BACKUP)
    actual = sha256(BACKUP)
    if actual != EXPECTED_BACKUP_SHA:
        raise RuntimeError(f"backup SHA mismatch: {actual}")
    result["checks"]["source_backup_sha256"] = actual
    if STAGE.exists():
        raise RuntimeError(f"Refusing to overwrite existing staging target: {STAGE}")
    STAGE.mkdir(parents=True)
    source = sqlite3.connect(f"file:{BACKUP.resolve().as_posix()}?mode=ro", uri=True, timeout=30)
    try:
        source.execute("PRAGMA query_only=ON")
        target = sqlite3.connect(str(DB), timeout=30)
        try:
            source.backup(target)
            target.commit()
        finally:
            target.close()
    finally:
        source.close()
    raw = sqlite3.connect(f"file:{DB.resolve().as_posix()}?mode=ro", uri=True, timeout=30)
    try:
        raw.execute("PRAGMA query_only=ON")
        quick = raw.execute("PRAGMA quick_check").fetchone()[0]
        integrity = raw.execute("PRAGMA integrity_check").fetchone()[0]
        tables = raw.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
        counts = {}
        for (name,) in tables:
            safe = '"' + name.replace('"','""') + '"'
            counts[name] = raw.execute(f"SELECT COUNT(*) FROM {safe}").fetchone()[0]
        row = raw.execute("SELECT memory_id,data FROM memories ORDER BY memory_id LIMIT 1").fetchone()
        if not row:
            raise RuntimeError("staging restore has no memory row")
        expected = json.loads(row[1])
        expected_hash = hashlib.sha256(expected["content"].encode("utf-8")).hexdigest()
        result["checks"].update({"staging_quick_check":quick, "staging_integrity_check":integrity, "table_count":len(tables), "memory_count":counts.get("memories"), "table_row_counts":counts, "sample_memory_id":row[0], "sample_content_sha256":expected_hash})
    finally:
        raw.close()
    if quick != "ok" or integrity != "ok":
        raise RuntimeError(f"staging integrity failed: quick={quick}, integrity={integrity}")
    app_code = r'''import hashlib,json,sys
from pathlib import Path
from dataclasses import replace
import app.config
app.config.settings = replace(app.config.settings, data_dir=Path(sys.argv[1]))
from core.brain.master_brain import MasterBrain
b=MasterBrain(); s=b.mother_operational.storage
mid=sys.argv[2]; m=s.get_memory(mid)
if m is None: raise SystemExit("APP_READBACK_MISSING_MEMORY")
print(json.dumps({"found":True,"memory_id":m.memory_id,"content_sha256":hashlib.sha256(m.content.encode("utf-8")).hexdigest(),"memory_type":m.memory_type,"source":m.source,"metadata":m.metadata,"created_at":m.created_at.isoformat(),"updated_at":m.updated_at.isoformat(),"database_path":str(s.database_path)}))
s.close()
'''
    env = dict(os.environ, PYTHONPATH=str(ROOT), SAHIBEX_MODEL_PROVIDER="mock", SAHIBEX_SEMANTIC_INTENT_ENABLED="0")
    p = subprocess.run([sys.executable, "-c", app_code, str(STAGE), row[0]], cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
    if p.returncode != 0:
        raise RuntimeError(f"staging application readback failed ({p.returncode}): {p.stderr[-2500:]}")
    app = json.loads(p.stdout.strip().splitlines()[-1])
    if app["content_sha256"] != expected_hash:
        raise RuntimeError("application read-back content hash mismatch")
    if Path(app["database_path"]).resolve() != DB.resolve():
        raise RuntimeError("application opened an unexpected database path")
    result["checks"].update({"application_get_memory":"PASS", "application_content_hash_match":True, "application_timestamps_readable":bool(app.get("created_at") and app.get("updated_at")), "application_database_path_verified":True})
    result["application_readback"] = {k:v for k,v in app.items() if k not in ("metadata",)}
    result["staging_database_path"] = str(DB)
    result["status"] = "PASS"
    REPORT.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps({"status":result["status"],"report":str(REPORT),"staging_database_path":str(DB),"memory_count":result["checks"]["memory_count"],"table_count":result["checks"]["table_count"],"quick_check":quick,"integrity_check":integrity,"application_get_memory":"PASS","production_db_modified":False}, indent=2))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        failure={"status":"FAIL","production_db_modified":False,"error":f"{type(e).__name__}: {e}"}
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(failure, indent=2)+"\n", encoding="utf-8")
        print(json.dumps(failure, indent=2), file=sys.stderr)
        raise
