#!/usr/bin/env python3
"""Safe P3 app-level restore/read-back against a temporary copy of production DB."""
from __future__ import annotations
import hashlib, json, os, sqlite3, subprocess, sys, tempfile, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'data' / 'sahibex_brain.db').resolve()
REPORT = ROOT / 'logs' / 'p3_application_restore_readback_20261021.json'

def main() -> int:
    if not SOURCE.is_file(): raise FileNotFoundError(SOURCE)
    result = {'date': time.strftime('%Y-%m-%d'), 'source_open_mode':'read-only', 'production_db_modified':False, 'restore_target':'temporary disposable copy', 'application':'core.brain.master_brain.MasterBrain', 'checks':{}}
    with tempfile.TemporaryDirectory(prefix='sahibex-p3-app-restore-') as td:
        tmp = Path(td); data_dir = tmp/'data'; data_dir.mkdir(); restored = data_dir/'sahibex_brain.db'
        src = sqlite3.connect(f'file:{SOURCE.as_posix()}?mode=ro', uri=True, timeout=60)
        try:
            src.execute('PRAGMA query_only=ON')
            src.backup(sqlite3.connect(str(restored), timeout=60))
        finally: src.close()
        # Capture a stable, non-sensitive expected record fingerprint from the restored DB.
        raw = sqlite3.connect(f'file:{restored.as_posix()}?mode=ro', uri=True, timeout=30)
        try:
            row = raw.execute('SELECT memory_id, data FROM memories ORDER BY memory_id LIMIT 1').fetchone()
            total = raw.execute('SELECT COUNT(*) FROM memories').fetchone()[0]
            if row is None: raise AssertionError('restored DB has no memory record for app-level read-back')
            expected_id, expected_json = row[0], row[1]
            expected = json.loads(expected_json)
            expected_content_hash = hashlib.sha256(expected['content'].encode('utf-8')).hexdigest()
        finally: raw.close()
        app_code = r'''import hashlib,json,sys
from pathlib import Path
from dataclasses import replace
import app.config
app.config.settings = replace(app.config.settings, data_dir=Path(sys.argv[1]))
from core.brain.master_brain import MasterBrain
b=MasterBrain(); s=b.mother_operational.storage
mid=sys.argv[2]; m=s.get_memory(mid)
if m is None: raise SystemExit('APP_READBACK_MISSING_MEMORY')
print(json.dumps({'found':True,'memory_id':m.memory_id,'content_sha256':hashlib.sha256(m.content.encode('utf-8')).hexdigest(),'memory_type':m.memory_type,'source_present':bool(m.source),'tags_count':len(m.tags),'metadata_matches_expected':m.metadata == json.loads(sys.argv[3]).get('metadata',{}),'created_at':m.created_at.isoformat(),'updated_at':m.updated_at.isoformat(),'last_accessed_at':m.last_accessed_at.isoformat() if m.last_accessed_at else None,'db_path':str(s.database_path)}))
s.close()
'''
        env = dict(os.environ, PYTHONPATH=str(ROOT), SAHIBEX_MODEL_PROVIDER='mock', SAHIBEX_SEMANTIC_INTENT_ENABLED='0')
        p = subprocess.run([sys.executable, '-c', app_code, str(data_dir), expected_id, json.dumps(expected)], cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
        if p.returncode != 0: raise RuntimeError(f'application read-back failed exit={p.returncode}: {p.stderr[-2500:]}')
        app = json.loads(p.stdout.strip().splitlines()[-1])
        if app['content_sha256'] != expected_content_hash: raise AssertionError('application content hash differs from restored row')
        if not app['metadata_matches_expected']: raise AssertionError('application metadata differs from restored row')
        if Path(app['db_path']).resolve() != restored.resolve(): raise AssertionError('MasterBrain did not open the disposable restored DB')
        result['checks'] = {'online_backup_to_temp_copy':'PASS','sqlite_integrity_check':None,'source_memory_count':int(total),'app_level_get_memory':'PASS','content_hash_matches_restored_record':True,'metadata_matches_restored_record':True,'timestamps_readable':bool(app['created_at'] and app['updated_at']),'app_used_temporary_restore_path':True}
        check = sqlite3.connect(f'file:{restored.as_posix()}?mode=ro', uri=True, timeout=30)
        try:
            result['checks']['sqlite_integrity_check'] = check.execute('PRAGMA integrity_check').fetchone()[0]
        finally: check.close()
        if result['checks']['sqlite_integrity_check'] != 'ok': raise AssertionError('restored database integrity check failed')
        result['application_readback'] = {k:v for k,v in app.items() if k not in ('db_path',)}
        result['status']='PASS'
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({'status':result['status'],'report':str(REPORT),'production_db_modified':False,'restored_memory_count':result['checks']['source_memory_count'],'app_level_get_memory':result['checks']['app_level_get_memory'],'integrity_check':result['checks']['sqlite_integrity_check'],'temporary_restore_only':True}, indent=2))
    return 0
if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as e:
        failure={'status':'FAIL','production_db_modified':False,'error':f'{type(e).__name__}: {e}'}
        REPORT.parent.mkdir(parents=True, exist_ok=True); REPORT.write_text(json.dumps(failure,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(failure,indent=2),file=sys.stderr); raise
