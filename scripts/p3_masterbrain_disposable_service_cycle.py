#!/usr/bin/env python3
"""Disposable two-process MasterBrain persistence cycle; never touches production DB."""
import json, os, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
WRITE = r'''import json, sys
from pathlib import Path
import app.config
from dataclasses import replace
app.config.settings = replace(app.config.settings, data_dir=Path(sys.argv[1]))
from core.brain.master_brain import MasterBrain
from core.research.memory_object import MemoryCandidate
b = MasterBrain(); s = b.mother_operational.storage
c = MemoryCandidate(memory_id='p3-restart-marker-20261021', content='disposable P3 restart marker: sapphire comet 7391', memory_type='fact', source='p3_disposable_acceptance', tags=['p3','restart'], metadata={'test_only': True, 'timestamp_utc':'2026-10-21T00:00:00Z'})
s.save_memory(c)
print(json.dumps({'stage':'write','database':str(s.database_path),'saved_id':c.memory_id,'persisted':True}))
s.close()
'''
READ = r'''import json, sys
from pathlib import Path
import app.config
from dataclasses import replace
app.config.settings = replace(app.config.settings, data_dir=Path(sys.argv[1]))
from core.brain.master_brain import MasterBrain
b = MasterBrain(); s = b.mother_operational.storage
matches = s.retrieve_memories('sapphire comet 7391')
found = [m for m in matches if m.memory_id == 'p3-restart-marker-20261021']
print(json.dumps({'stage':'read_after_process_restart','found':bool(found),'match_count':len(found),'content':found[0].content if found else None,'metadata':found[0].metadata if found else None,'database':str(s.database_path)}, default=str))
s.close()
if not found: raise SystemExit(5)
'''
def main():
  with tempfile.TemporaryDirectory(prefix='sahibex-p3-masterbrain-cycle-') as td:
    data_dir = Path(td) / 'data'; data_dir.mkdir()
    env = dict(os.environ, PYTHONPATH=str(ROOT), SAHIBEX_MODEL_PROVIDER='mock', SAHIBEX_SEMANTIC_INTENT_ENABLED='0')
    w = subprocess.run([sys.executable, '-c', WRITE, str(data_dir)], cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    r = subprocess.run([sys.executable, '-c', READ, str(data_dir)], cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    result = {'acceptance':'P3 disposable MasterBrain two-process persistence cycle','production_db_touched':False,'scope':'temporary disposable data_dir','writer_exit':w.returncode,'writer_stdout':w.stdout.strip(),'writer_stderr':w.stderr[-2500:],'reader_exit':r.returncode,'reader_stdout':r.stdout.strip(),'reader_stderr':r.stderr[-2500:],'status':'PASS' if w.returncode == 0 and r.returncode == 0 else 'FAIL'}
    for name in ('p3_masterbrain_disposable_service_cycle_20261021.json','p3_masterbrain_disposable_service_cycle_20261021.log'):
      (ROOT/'logs'/name).write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if result['status']=='PASS' else 1
if __name__ == '__main__': raise SystemExit(main())
