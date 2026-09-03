#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]; geo=root/'research/geology'; data=Path(sys.argv[1]) if len(sys.argv)>1 else geo/'bitcoin-mainnet-headers.bin'; out=geo/'ledger'
if not data.exists():
 raise SystemExit(f"missing real mainnet header file: {data}; no synthetic fallback is permitted")
py=subprocess.run([sys.executable,str(geo/'goldatom_ledger.py'),'scan','--headers',str(data),'--out',str(out),'--source-json',str(geo/'source.json')],check=True,capture_output=True,text=True)
node=json.loads(subprocess.check_output(['node',str(geo/'goldatom_ledger.mjs'),str(data)]))
summary=json.loads((out/'summary.json').read_text()); raw=list(__import__('csv').DictReader((out/'raw-records.csv').open()))
assert [(int(r['height']),r['block_hash']) for r in raw]==[(r['height'],r['hash']) for r in node['records']]
assert summary['raw_record_count']==node['count']; assert summary['current_frontier']==node['frontier']
(out/'independent-verification.json').write_text(json.dumps({"python_node_exact_agreement":True,"raw_record_count":node['count'],"terminal_frontier":node['frontier'],"tip_height":node['tip_height'],"tip_hash":node['tip_hash']},indent=2)+'\n')
print(py.stdout);print('independent agreement: OK')
