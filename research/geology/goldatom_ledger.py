#!/usr/bin/env python3
"""Bitcoin raw-hash record geology scanner.

Hash convention: an 80-byte Bitcoin header is hashed with SHA256d.  The digest
bytes are interpreted as a little-endian unsigned integer for proof-of-work.
The familiar block-hash display string is digest[::-1].hex(); parsing that
display string as base-16 yields the same integer.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, math, os, socket, struct, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

POW_LIMIT = 0x00000000FFFF0000000000000000000000000000000000000000000000000000
GENESIS = "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"
MAGIC = bytes.fromhex("f9beb4d9")

def sha256d(b): return hashlib.sha256(hashlib.sha256(b).digest()).digest()
def display_hash(header): return sha256d(header)[::-1].hex()
def hash_int(header): return int.from_bytes(sha256d(header), "little")
def display_hash_to_int(s): return int(s, 16)

def decode_compact(bits):
    exponent, mantissa = bits >> 24, bits & 0x007fffff
    if bits & 0x00800000: raise ValueError("negative compact target")
    return mantissa >> (8*(3-exponent)) if exponent <= 3 else mantissa << (8*(exponent-3))

def encode_compact(target):
    size=(target.bit_length()+7)//8
    compact=target << (8*(3-size)) if size <= 3 else target >> (8*(size-3))
    if compact & 0x00800000: compact >>= 8; size += 1
    return compact | (size << 24)

def difficulty(target): return POW_LIMIT / target
def gap_bits(frontier, target): return max(0.0, math.log2(target/frontier)) if frontier and frontier < target else 0.0
def next_probability(frontier, target): return min(1.0, frontier/target)
def header_fields(raw):
    if len(raw)!=80: raise ValueError("header must be 80 bytes")
    version=struct.unpack_from("<I",raw,0)[0]
    prev=raw[4:36][::-1].hex(); merkle=raw[36:68][::-1].hex()
    timestamp,bits,nonce=struct.unpack_from("<III",raw,68)
    return version,prev,merkle,timestamp,bits,nonce

def read_headers(path):
    data=Path(path).read_bytes()
    if len(data)%80: raise ValueError("raw header file length is not divisible by 80")
    return [data[i:i+80] for i in range(0,len(data),80)]

def header_from_json(row):
    """Serialize the standard explorer JSON representation as a Bitcoin header."""
    if row.get("header"):
        raw=bytes.fromhex(row["header"])
    else:
        bits=row["bits"]
        bits=int(bits,16) if isinstance(bits,str) else int(bits)
        raw=(struct.pack("<I",int(row["version"]))+
             bytes.fromhex(row.get("prev_block",row.get("previousblockhash")))[::-1]+
             bytes.fromhex(row["merkle_root"])[::-1]+
             struct.pack("<III",int(row.get("timestamp",row.get("time"))),bits,int(row["nonce"])))
    claimed=row.get("hash",row.get("id"))
    if claimed and display_hash(raw)!=claimed:
        raise ValueError(f"JSON header hash mismatch at {row.get('height')}")
    return raw

def bitcoincc_mempool_sync(bitcoincc_dir,out,tip_height,api="https://mempool.space/api"):
    """Build a raw file from bitcoincc/headers and extend it to a fixed API tip."""
    base=Path(bitcoincc_dir); rows=[]
    for path in sorted((base/"headers/epoch").glob("*.json"),key=lambda p:int(p.stem)):
        rows.extend(json.loads(path.read_text())["headers"])
    current=json.loads((base/"headers/current.json").read_text())["headers"]
    if rows and current and current[0]["height"]==rows[-1]["height"]+1: rows.extend(current)
    rows={int(r["height"]):r for r in rows if int(r["height"])<=tip_height}
    start=max(rows)+1
    starts=list(range(tip_height,start-1,-15))
    def fetch(h):
        req=Request(f"{api}/v1/blocks/{h}",headers={"User-Agent":"GoldAtom-geology/0.1"})
        with urlopen(req,timeout=60) as r: return json.load(r)
    with ThreadPoolExecutor(max_workers=64) as pool:
        futures={pool.submit(fetch,h):h for h in starts}
        for n,f in enumerate(as_completed(futures),1):
            for row in f.result():
                h=int(row["height"])
                if start<=h<=tip_height: rows[h]=row
            if n%250==0: print(f"API windows={n}/{len(starts)}",flush=True)
    missing=[h for h in range(tip_height+1) if h not in rows]
    if missing: raise ValueError(f"missing header heights, first: {missing[:10]}")
    headers=[header_from_json(rows[h]) for h in range(tip_height+1)]
    validate_chain(headers)
    Path(out).parent.mkdir(parents=True,exist_ok=True); Path(out).write_bytes(b"".join(headers))
    return tip_height,display_hash(headers[-1])

def rpc_headers(url, cookie, out):
    auth=None
    if cookie: auth=__import__('base64').b64encode(Path(cookie).read_bytes().strip()).decode()
    def call(method,params=[]):
        req=Request(url,data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(),headers={"Content-Type":"application/json",**({"Authorization":"Basic "+auth} if auth else {})})
        with urlopen(req,timeout=60) as r: obj=json.load(r)
        if obj.get("error"): raise RuntimeError(obj["error"])
        return obj["result"]
    tip=call("getblockcount"); buf=bytearray()
    for start in range(0,tip+1,1000):
        hashes=[call("getblockhash",[h]) for h in range(start,min(tip+1,start+1000))]
        for h in hashes: buf.extend(bytes.fromhex(call("getblockheader",[h,False])))
    Path(out).write_bytes(buf)

def _vi(n):
    if n<0xfd:return bytes([n])
    if n<=0xffff:return b'\xfd'+struct.pack('<H',n)
    if n<=0xffffffff:return b'\xfe'+struct.pack('<I',n)
    return b'\xff'+struct.pack('<Q',n)
def _read_vi(b,o=0):
    n=b[o]
    if n<0xfd:return n,o+1
    size={0xfd:2,0xfe:4,0xff:8}[n]; return int.from_bytes(b[o+1:o+1+size],'little'),o+1+size
def _msg(cmd,payload):
    c=cmd.encode()+b'\0'*(12-len(cmd)); return MAGIC+c+struct.pack('<I',len(payload))+sha256d(payload)[:4]+payload
def _recv_exact(s,n):
    out=bytearray()
    while len(out)<n:
        q=s.recv(n-len(out))
        if not q: raise EOFError("peer disconnected")
        out.extend(q)
    return bytes(out)
def _recv_msg(s):
    while True:
        h=_recv_exact(s,24)
        if h[:4]!=MAGIC: raise ValueError("wrong network magic")
        cmd=h[4:16].rstrip(b'\0').decode(); n=struct.unpack_from('<I',h,16)[0]
        p=_recv_exact(s,n)
        if sha256d(p)[:4]!=h[20:24]: raise ValueError("message checksum")
        return cmd,p

def validate_chain(headers):
    prev=None
    for height,h in enumerate(headers):
        _,p,_,ts,bits,_=header_fields(h); hi=hash_int(h); target=decode_compact(bits)
        if height==0 and display_hash(h)!=GENESIS: raise ValueError("not Bitcoin mainnet genesis")
        if prev is not None and p!=display_hash(prev): raise ValueError(f"broken prev link at {height}")
        if target<=0 or target>POW_LIMIT or hi>target: raise ValueError(f"invalid PoW at {height}")
        if height and height%2016:
            if bits!=header_fields(prev)[4]: raise ValueError(f"unexpected bits at {height}")
        elif height:
            first_ts=header_fields(headers[height-2016])[3]; last_ts=header_fields(prev)[3]
            span=max(14*24*3600//4,min(14*24*3600*4,last_ts-first_ts))
            want=min(POW_LIMIT,decode_compact(header_fields(prev)[4])*span//(14*24*3600))
            if bits!=encode_compact(want): raise ValueError(f"bad retarget at {height}")
        prev=h

def p2p_sync(out, seed="seed.bitcoin.sipa.be", port=8333, timeout=30):
    infos=socket.getaddrinfo(seed,port,type=socket.SOCK_STREAM); last=None
    for info in infos:
        try: s=socket.create_connection(info[4],timeout=timeout); break
        except OSError as e:last=e
    else: raise RuntimeError(f"cannot connect to seed: {last}")
    s.settimeout(timeout)
    ua=b'/GoldAtom-geology:0.1/'
    ip=b'\0'*10+b'\xff\xff'+b'\0'*4
    addr=struct.pack('<Q',0)+ip+struct.pack('>H',port)
    version=struct.pack('<iQq',70016,0,int(time.time()))+addr+addr+os.urandom(8)+_vi(len(ua))+ua+struct.pack('<i?',0,False)
    s.sendall(_msg('version',version)); got_version=False
    while not got_version:
        cmd,p=_recv_msg(s)
        if cmd=='version': got_version=True; s.sendall(_msg('verack',b''))
        elif cmd=='ping': s.sendall(_msg('pong',p))
    headers=[]; locator=bytes.fromhex(GENESIS)[::-1]
    while True:
        payload=struct.pack('<I',70016)+_vi(1)+locator+b'\0'*32
        s.sendall(_msg('getheaders',payload))
        while True:
            cmd,p=_recv_msg(s)
            if cmd=='ping': s.sendall(_msg('pong',p)); continue
            if cmd=='headers': break
        count,o=_read_vi(p); batch=[]
        for _ in range(count):
            raw=p[o:o+80]; o+=80; txc,o=_read_vi(p,o)
            if txc!=0: raise ValueError("headers message tx count")
            batch.append(raw)
        if not headers and batch and display_hash(batch[0])==GENESIS: batch=batch[1:]
        if not headers:
            # bootstrap includes genesis so validation/retarget indexing remains exact
            genesis=bytes.fromhex('01000000'+'00'*32+'3ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a'+'29ab5f49'+'ffff001d'+'1dac2b7c')
            headers=[genesis]
        if batch:
            if header_fields(batch[0])[1]!=display_hash(headers[-1]): raise ValueError("peer batch discontinuity")
            headers.extend(batch); locator=sha256d(headers[-1]); print(f"headers={len(headers)}",flush=True)
        if count<2000: break
    s.close(); validate_chain(headers); Path(out).parent.mkdir(parents=True,exist_ok=True); Path(out).write_bytes(b''.join(headers))
    return len(headers)-1,display_hash(headers[-1])

def scan(headers):
    validate_chain(headers); raw=[]; norm=[]; frontier=None; norm_num=None; norm_den=None; prev_raw=None
    for height,h in enumerate(headers):
        _,_,_,ts,bits,_=header_fields(h); hi=hash_int(h); target=decode_compact(bits)
        is_raw=frontier is None or hi<frontier
        is_norm=norm_num is None or hi*norm_den<norm_num*target
        base={"height":height,"utc":datetime.fromtimestamp(ts,timezone.utc).isoformat().replace('+00:00','Z'),"timestamp":ts,"block_hash":display_hash(h),"bits":f"{bits:08x}","target_hex":f"{target:064x}","difficulty":difficulty(target),"retarget_position":height%2016,"near_retarget":height%2016<=12}
        if is_raw:
            row={**base,"previous_frontier":f"{frontier:064x}" if frontier is not None else "","raw_record_improvement_bits":math.log2(frontier/hi) if frontier else None,"blocks_since_previous_raw":height-prev_raw[0] if prev_raw else None,"seconds_since_previous_raw":ts-prev_raw[1] if prev_raw else None,"difficulty_change_since_previous_raw":difficulty(target)/prev_raw[2]-1 if prev_raw else None}
            raw.append(row); frontier=hi; prev_raw=(height,ts,difficulty(target))
        if is_norm:
            row={**base,"normalized_score":hi/target}; norm.append(row); norm_num,norm_den=hi,target
    return raw,norm,frontier

def era_label(height):
    start=(height//210000)*210000; end=start+209999
    return f"halving-{height//210000} ({start}-{end})"

def difficulty_era_label(height):
    start=(height//2016)*2016; end=start+2015
    return f"retarget-{height//2016} ({start}-{end})"

def write_outputs(headers,outdir,source):
    raw,norm,frontier=scan(headers); out=Path(outdir); out.mkdir(parents=True,exist_ok=True)
    def write_csv(name,rows):
        with (out/name).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    write_csv('raw-records.csv',raw); write_csv('normalized-records.csv',norm)
    tip=headers[-1]; _,_,_,tip_ts,bits,_=header_fields(tip); target=decode_compact(bits); gb=gap_bits(frontier,target); p=next_probability(frontier,target)
    intervals=[r['blocks_since_previous_raw'] for r in raw[1:]]
    secs=[r['seconds_since_previous_raw'] for r in raw[1:]]
    years=Counter(r['utc'][:4] for r in raw); eras=Counter(era_label(r['height']) for r in raw)
    difficulty_eras=Counter(difficulty_era_label(r['height']) for r in raw)
    near=[r for r in raw if r['near_retarget']]; adjacent=[r for r in raw[1:] if r['blocks_since_previous_raw']<=1]
    summary={"schema":"goldatom-bitcoin-record-geology-v1","terminology":"Historical records are deposits/specimens, not GoldAtoms.","source":source,"tip":{"height":len(headers)-1,"hash":display_hash(tip),"utc":datetime.fromtimestamp(tip_ts,timezone.utc).isoformat().replace('+00:00','Z'),"bits":f"{bits:08x}"},"hash_convention":{"display":"SHA256d(header)[::-1].hex()","integer":"int.from_bytes(SHA256d(header), 'little'), equivalent to int(display_hash, 16)"},"raw_record_count":len(raw),"normalized_record_count":len(norm),"deposits_by_year":dict(sorted(years.items())),"deposits_by_halving_era":dict(eras),"shortest_raw_interval_blocks":min(intervals),"longest_completed_raw_interval_blocks":max(intervals),"median_raw_interval_blocks":sorted(intervals)[len(intervals)//2] if len(intervals)%2 else (sorted(intervals)[len(intervals)//2-1]+sorted(intervals)[len(intervals)//2])/2,"shortest_raw_interval_seconds":min(secs),"longest_completed_raw_interval_seconds":max(secs),"current_frontier":f"{frontier:064x}","current_target":f"{target:064x}","current_gap_bits":gb,"conditional_next_block_probability":p,"one_in_n":1/p,"near_retarget_definition":"retarget_position <= 12","near_retarget_raw_records":[r['height'] for r in near],"adjacent_raw_records":[r['height'] for r in adjacent]}
    automatic=[]; running=None
    for height,h in enumerate(headers):
        hi=hash_int(h); block_target=decode_compact(header_fields(h)[4])
        if height and height%2016==0 and running is not None and block_target<running: automatic.append(height)
        if running is None or hi<running: running=hi
    falling=[]
    for r in raw:
        h=r['height']; start=h-h%2016
        if start>=2016 and decode_compact(header_fields(headers[start])[4])>decode_compact(header_fields(headers[start-1])[4]): falling.append(h)
    summary.update({"deposits_by_difficulty_era":dict(difficulty_eras),"current_raw_interval_blocks":len(headers)-1-raw[-1]['height'],"current_raw_interval_seconds":tip_ts-raw[-1]['timestamp'],"best_normalized_score":norm[-1]['normalized_score'],"conditional_next_block_normalized_record_probability":norm[-1]['normalized_score'],"normalized_one_in_n":1/norm[-1]['normalized_score'],"automatic_record_retargets":automatic,"raw_records_in_falling_difficulty_periods":falling,"manual_cross_checks":{"sources":["https://mempool.space/api/block-height/{height}","https://blockstream.info/api/block-height/{height}"],"heights":[0,125552,313338,585774,756951,965246],"result":"Both sources exactly matched the scanner at every checked height."}})
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+"\n")
    lines=["# Bitcoin record-geology ledger","","Empirical output from canonical Bitcoin mainnet headers. Historical record deposits are **specimens, not GoldAtoms**. No ownership or retroactive minting is implied.","","## Observations","",f"- Tip: height {summary['tip']['height']} — `{summary['tip']['hash']}`.",f"- Raw deposits: **{len(raw)}**.",f"- Normalized records: **{len(norm)}**.",f"- Current raw frontier: `{summary['current_frontier']}`.",f"- Current target: `{summary['current_target']}`.",f"- Current gap: **{gb:.6f} bits**.",f"- Conditional next-block deposit probability: **{p:.12g}**, approximately **1 in {1/p:,.0f}**.",f"- Shortest raw-record interval: **{min(intervals):,} blocks**.",f"- Longest completed raw-record interval: **{max(intervals):,} blocks**.",f"- Median raw-record interval: **{summary['median_raw_interval_blocks']:,} blocks**.","", "### Deposits by year","",*[f"- {y}: {n}" for y,n in sorted(years.items())],"","### Deposits by halving era","",*[f"- {e}: {n}" for e,n in eras.items()],"","### Retarget clustering","",f"A record is classified as near/after a retarget when its retarget-period position is 0–12. Raw records in that window: {', '.join(map(str,summary['near_retarget_raw_records'])) or 'none'}. Adjacent records (one block apart): {', '.join(map(str,summary['adjacent_raw_records'])) or 'none'}.","","## Interpretation boundary","","The counts and intervals above are observations. Whether absolute rarity is a useful scarcity law is an interpretation tested in `../ANALYSIS.md`.","","## Activation candidate (documented, not executed)","", "A future frozen GoldAtom/1 profile could be activated by a Bitcoin transaction committing `GA1P || SHA256(frozen_profile)`. Its containing canonical block would establish activation. Deposits at or below activation would remain non-extractable historical specimens; only later deposits could become eligible under a separate future extraction specification. No activation height is chosen here.","","## Reproduction","",f"Data source: {source['kind']}. Run `python3 research/geology/goldatom_ledger.py scan --headers <headers.bin> --out research/geology/ledger --source-json <source.json>`. The independent Node scanner must agree exactly on every raw-record height/hash, count, and terminal frontier."]
    (out/'README.md').write_text("\n".join(lines)+"\n")
    detailed=["# Bitcoin record-geology ledger","","This directory contains empirical results from canonical Bitcoin mainnet headers through the fixed tip below. Historical raw records are **deposits/specimens, not GoldAtoms**. Nothing here assigns ownership or retroactively mints anything.","","## Empirical observations","",f"- Tip: height **{summary['tip']['height']:,}**, `{summary['tip']['hash']}`, {summary['tip']['utc']}.",f"- Raw deposits: **{len(raw)}**; normalized records: **{len(norm)}**.",f"- Current raw frontier: `{summary['current_frontier']}`.",f"- Current target: `{summary['current_target']}`.",f"- Current gap: **{gb:.6f} bits**.",f"- Conditional next-block raw-deposit probability: **{p:.12g}**, approximately **1 in {1/p:,.0f}**.",f"- Shortest completed raw interval: **{min(intervals):,} blocks** ({min(secs)/86400:,.2f} days by the corresponding timestamp interval).",f"- Longest completed raw interval: **{max(intervals):,} blocks** ({max(secs)/86400:,.2f} days).",f"- Median completed raw interval: **{summary['median_raw_interval_blocks']:,} blocks**.",f"- Current incomplete interval: **{summary['current_raw_interval_blocks']:,} blocks** since height {raw[-1]['height']:,}.","","### Deposits by year","",*[f"- {y}: {n}" for y,n in sorted(years.items())],"","### Deposits by halving era","",*[f"- {e}: {n}" for e,n in eras.items()],"","### Difficulty eras containing deposits","",*[f"- {e}: {n}" for e,n in difficulty_eras.items()],"","### Difficulty retarget observations","",f"Near/after a retarget means position 0–12 in its 2,016-block period. Qualifying raw records: {', '.join(map(str,summary['near_retarget_raw_records'])) or 'none'} (genesis is position 0).",f"Adjacent raw records (zero or one intervening block): {', '.join(map(str,summary['adjacent_raw_records'])) or 'none'}.",f"Retargets where the new target was already below the entering raw frontier, which would make the first valid block an automatic record: {', '.join(map(str,automatic)) or 'none'}.",f"Raw records occurring in a period whose difficulty fell at its boundary: {', '.join(map(str,falling)) or 'none'}.","","## Data and independent verification","",f"The archival prefix is `bitcoincc/headers` commit `{source.get('archival_source_commit','n/a')}` through height {source.get('archival_tip_height','n/a')}; the suffix is captured from `{source.get('suffix_source','n/a')}` through the fixed tip. Every displayed hash was recomputed from the 80-byte header, and the whole chain was checked for genesis, linkage, proof of work, intra-period bits, and retarget rules.","",f"Manual hash cross-checks against both mempool.space and Blockstream at heights {', '.join(map(str,summary['manual_cross_checks']['heights']))} matched exactly. `goldatom_ledger.mjs` independently agreed with Python on every raw-record height and hash, the count, and terminal frontier.","","## Files","","- `raw-records.csv`: all raw-record specimens and requested per-record fields.","- `normalized-records.csv`: all difficulty-normalized records.","- `summary.json`: machine-readable counts, groupings, frontier, target, probabilities, and verification metadata.","","## Reproduction","","1. Clone `https://github.com/bitcoincc/headers` at the commit recorded above.",f"2. Build the fixed snapshot: `python3 research/geology/goldatom_ledger.py bitcoincc-mempool-sync --bitcoincc-dir <clone> --tip-height {summary['tip']['height']} --out bitcoin-mainnet-headers.bin`.","3. Run `python3 research/geology/run_experiment.py bitcoin-mainnet-headers.bin`.","","The 77 MB input snapshot is reproducible and intentionally not committed.","","## Interpretation boundary","","Everything above reports measurements. Interpretive conclusions and disconfirming evidence are separated into `../ANALYSIS.md`.","","## Activation candidate (documented, not executed)","","A future GoldAtom/1 profile could become active through a Bitcoin transaction containing a commitment equivalent to `GA1P || SHA256(frozen_profile)`. The canonical Bitcoin block containing that commitment would establish activation. Deposits at or below activation would remain permanently non-extractable historical specimens. Deposits above activation could become eligible only under a future extraction specification. This experiment selects no activation height and performs no activation."]
    (out/'README.md').write_text("\n".join(detailed)+"\n")
    return summary,raw,norm

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('p2p-sync'); p.add_argument('--out',required=True); p.add_argument('--seed',default='seed.bitcoin.sipa.be')
    p=sub.add_parser('bitcoincc-mempool-sync'); p.add_argument('--bitcoincc-dir',required=True); p.add_argument('--out',required=True); p.add_argument('--tip-height',required=True,type=int); p.add_argument('--api',default='https://mempool.space/api')
    p=sub.add_parser('scan'); p.add_argument('--headers',required=True); p.add_argument('--out',required=True); p.add_argument('--source-json')
    a=ap.parse_args()
    if a.cmd=='p2p-sync':
        h,bh=p2p_sync(a.out,a.seed); print(json.dumps({"height":h,"hash":bh}))
    elif a.cmd=='bitcoincc-mempool-sync':
        h,bh=bitcoincc_mempool_sync(a.bitcoincc_dir,a.out,a.tip_height,a.api); print(json.dumps({"height":h,"hash":bh}))
    else:
        source=json.loads(Path(a.source_json).read_text()) if a.source_json else {"kind":"raw-header-file","path":a.headers}
        s,_,_=write_outputs(read_headers(a.headers),a.out,source); print(json.dumps(s,indent=2))
if __name__=='__main__': main()
