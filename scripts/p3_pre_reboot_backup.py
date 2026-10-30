#!/usr/bin/env python3
"""Create and integrity-verify a durable pre-reboot backup without writing source DB."""
import hashlib,json,sqlite3,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data'/'sahibex_brain.db'
OUT=ROOT/'data'/'backups'/'sahibex_brain_pre_reboot_20261021.db'
REPORT=ROOT/'logs'/'p3_pre_reboot_backup_20261021.json'
def main():
 if not SRC.is_file(): raise FileNotFoundError(SRC)
 if OUT.exists(): raise FileExistsError(f'refusing to overwrite existing backup: {OUT}')
 OUT.parent.mkdir(parents=True,exist_ok=True); started=time.time()
 source=sqlite3.connect(f'file:{SRC.as_posix()}?mode=ro',uri=True,timeout=60)
 try:
  source.execute('PRAGMA query_only=ON'); source.execute('SELECT count(*) FROM sqlite_master').fetchone()
  dst=sqlite3.connect(str(OUT),timeout=60)
  try: source.backup(dst,pages=1024,sleep=0.05)
  finally: dst.close()
 finally: source.close()
 conn=sqlite3.connect(f'file:{OUT.as_posix()}?mode=ro',uri=True,timeout=60)
 try:
  quick=conn.execute('PRAGMA quick_check').fetchone()[0]; integrity=conn.execute('PRAGMA integrity_check').fetchone()[0]
  tables=[r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
  counts={}
  for table in tables: counts[table]=conn.execute('SELECT COUNT(*) FROM "'+table.replace('"','""')+'"').fetchone()[0]
  mem=conn.execute('SELECT memory_id,data FROM memories ORDER BY memory_id LIMIT 1').fetchone() if 'memories' in tables else None
  if quick!='ok' or integrity!='ok': raise RuntimeError(f'integrity failure quick={quick} integrity={integrity}')
  if not mem: raise RuntimeError('backup has no memory record')
  memory=json.loads(mem[1])
 finally: conn.close()
 digest=hashlib.sha256()
 with OUT.open('rb') as f:
  for chunk in iter(lambda:f.read(4*1024*1024),b''): digest.update(chunk)
 result={'status':'PASS','created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'source':str(SRC),'source_open_mode':'read-only','backup':str(OUT),'backup_size_bytes':OUT.stat().st_size,'backup_sha256':digest.hexdigest(),'production_db_modified':False,'quick_check':quick,'integrity_check':integrity,'table_count':len(tables),'memory_count':counts.get('memories'),'sample_memory_json_parse':'PASS','sample_memory_id_present':bool(memory.get('memory_id')),'elapsed_seconds':round(time.time()-started,2),'row_counts':counts,'scope':'pre-reboot durable local backup; no service restart performed'}
 REPORT.parent.mkdir(parents=True,exist_ok=True); REPORT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='row_counts'},indent=2))
if __name__=='__main__': main()
